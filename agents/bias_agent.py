"""
Bias Detection Agent — Multi-Dimensional Grading Inconsistency Analysis

Algorithm v3.0 — addresses the "AI as ground truth" philosophical flaw:

  Instead of treating the AI score as the reference baseline, we compute a
  COMPOSITE INCONSISTENCY INDEX that combines four independent signals:

  1. Severity-Weighted Gap (SWG)
     The raw score difference is weighted by its position on the rubric.
     A 3-point gap at the top of the scale (7→10) implies more systematic
     bias than a 3-point gap at the bottom (0→3), because high-achievers
     are disproportionately harmed by conservative grading culture.

  2. Completeness Factor (CF)
     Penalises bias flags on very short answers where both raters have
     insufficient signal. Logarithmic scaling ensures a smooth curve.

  3. OCR Confidence Penalty (OCP)
     If the OCR pipeline's confidence is below 90%, we discount the
     inconsistency flag because text extraction errors—not bias—may
     explain the score gap. Answers below threshold are routed for
     manual review rather than bias classification.

  4. Directional Consistency Signal (DCS)
     Tracks the direction of disagreement across sessions (passed in by
     the caller). If a teacher *consistently* underscores vs the AI
     across multiple papers, this escalates severity—systematic patterns
     are more concerning than one-off disagreements.

  Final Composite Score = SWG × CF × OCP  (capped at 100%)
  Statistical note: a score ≥ 30% is only flagged as High Risk when
  the absolute gap ≥ 1.5 marks, providing a basic significance guard.

Why AI is not ground truth:
  The AI score is one rater; the teacher is another. We measure
  *inter-rater disagreement*, not deviation from an objective truth.
  The bias_indicators field (produced by the EvaluationAgent) surfaces
  WHAT drove the AI's score—giving teachers transparency to judge
  whether the AI's criteria were appropriate.

  For genuine demographic-aware analysis (the gold standard), integrative
  school-level data across 500+ evaluations would be required. The
  Directional Consistency Signal is a stepping-stone toward that goal.
"""

import math
from typing import Optional


class BiasAgent:
    """Agent 4 — Detects grading inconsistency using a composite signal index."""

    # ── Risk thresholds (Composite Score %)
    HIGH_RISK_THRESHOLD   = 30.0
    MEDIUM_RISK_THRESHOLD = 15.0

    # ── Minimum absolute gap required to call High Risk (significance guard)
    HIGH_RISK_MIN_GAP = 1.5

    # ── OCR confidence below this triggers a 'low_ocr_confidence' flag
    OCR_CONFIDENCE_THRESHOLD = 0.90

    # ── Fairness threshold: gaps ≤ this are 'Fair' regardless of percentage
    FAIRNESS_THRESHOLD = 1.0

    def detect_bias(
        self,
        teacher_mark: float,
        ai_mark: float,
        ai_confidence: float = 1.0,
        answer_length: int = 200,
        ocr_confidence: float = 1.0,
        session_history: Optional[list] = None,
    ) -> dict:
        """
        Detect and classify grading inconsistency using a composite index.

        Args:
            teacher_mark:    Score assigned by the human teacher (0–10).
            ai_mark:         Score assigned by the AI evaluation agent (0–10).
            ai_confidence:   AI's self-reported confidence (0.0–1.0).
            answer_length:   Character count of the student's anonymised answer.
            ocr_confidence:  Estimated OCR extraction confidence (0.0–1.0).
                             Values below OCR_CONFIDENCE_THRESHOLD trigger a
                             low-confidence flag and reduce the bias score.
            session_history: Optional list of previous {teacher, ai} score dicts
                             for the same teacher in this session. Used to
                             compute a directional consistency signal.

        Returns:
            dict with keys:
                - 'status':                  'Undergraded' | 'Overgraded' | 'Fair'
                - 'severity':                'High Risk' | 'Medium Risk' | 'Low Risk'
                - 'difference':              absolute score gap (float)
                - 'bias_score_percentage':   composite inconsistency index 0–100 (float)
                - 'completeness_factor':     CF component (float)
                - 'severity_weight':         SWG component (float)
                - 'ocr_penalty_applied':     bool — was OCR confidence below threshold?
                - 'flag_manual_review':      bool — should this bypass AI bias classification?
                - 'directional_consistency': None | 'consistent_undergrading' |
                                             'consistent_overgrading' | 'mixed'
                - 'formula_used':            human-readable formula string
                - 'methodology_note':        explanation that AI ≠ ground truth
        """
        diff = abs(teacher_mark - ai_mark)
        status = self._classify_status(teacher_mark, ai_mark)

        # ── 1. Severity-Weighted Gap ──────────────────────────────────────
        severity_weight = self._compute_severity_weight(teacher_mark, ai_mark)
        raw_swg = min(100.0, diff * 10 * severity_weight)

        # ── 2. Completeness Factor ────────────────────────────────────────
        completeness_factor = self._compute_completeness_factor(answer_length)

        # ── 3. OCR Confidence Penalty ─────────────────────────────────────
        ocr_penalty_applied = ocr_confidence < self.OCR_CONFIDENCE_THRESHOLD
        ocr_factor = self._compute_ocr_factor(ocr_confidence)

        # ── Flag for manual review if OCR confidence is very low ──────────
        flag_manual_review = ocr_confidence < 0.75

        # ── Composite Score ───────────────────────────────────────────────
        composite = raw_swg * completeness_factor * ocr_factor
        final_bias = round(min(composite, 100.0), 1)

        # ── 4. Directional Consistency Signal ─────────────────────────────
        dcs = self._compute_directional_consistency(
            teacher_mark, ai_mark, session_history
        )

        # Escalate to High Risk if DCS confirms systematic pattern
        if dcs in ("consistent_undergrading", "consistent_overgrading"):
            if final_bias >= self.MEDIUM_RISK_THRESHOLD:
                final_bias = max(final_bias, self.HIGH_RISK_THRESHOLD + 0.1)

        # ── Risk Classification ───────────────────────────────────────────
        severity = self._classify_severity(final_bias, diff)

        formula = (
            f"Composite = min(100, |{teacher_mark}−{ai_mark}|×10"
            f"×SeverityWeight({severity_weight:.2f})"
            f"×CF({completeness_factor:.2f})"
            f"×OCRFactor({ocr_factor:.2f}))"
            f" = {final_bias}%"
        )

        return {
            "severity":                severity,
            "status":                  status,
            "difference":              diff,
            "bias_score_percentage":   final_bias,
            "completeness_factor":     completeness_factor,
            "severity_weight":         severity_weight,
            "ocr_penalty_applied":     ocr_penalty_applied,
            "flag_manual_review":      flag_manual_review,
            "directional_consistency": dcs,
            "formula_used":            formula,
            "methodology_note": (
                "Inter-rater disagreement metric. AI score is one rater, "
                "not ground truth. Both raters may share biases. "
                "Use bias_indicators for qualitative explainability."
            ),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _classify_severity(self, final_bias: float, gap: float) -> str:
        """
        Classify risk level with a significance guard:
        High Risk requires both a high composite score AND a meaningful gap.
        """
        if final_bias > self.HIGH_RISK_THRESHOLD and gap >= self.HIGH_RISK_MIN_GAP:
            return "High Risk"
        if final_bias > self.MEDIUM_RISK_THRESHOLD:
            return "Medium Risk"
        return "Low Risk"

    def _classify_status(self, teacher_mark: float, ai_mark: float) -> str:
        """Classify status based on raw mark difference."""
        if teacher_mark < ai_mark - self.FAIRNESS_THRESHOLD:
            return "Undergraded"
        if teacher_mark > ai_mark + self.FAIRNESS_THRESHOLD:
            return "Overgraded"
        return "Fair"

    def _compute_completeness_factor(self, char_count: int) -> float:
        """
        CF = min(1.0, log(1 + word_count) / log(120))
        Longer answers = higher confidence in the evaluation signal.
        """
        word_count = max(1, char_count // 5)
        factor = math.log(1 + word_count) / math.log(120)
        return round(min(1.0, factor), 2)

    def _compute_severity_weight(self, teacher_mark: float, ai_mark: float) -> float:
        """
        Severity-Weighted Gap multiplier (1.0–1.4):
        Disagreements in the upper rubric band (scores > 6) are weighted higher
        because high-achieving students are statistically more harmed by
        conservative grading norms (ceiling-effect bias).

        Weight = 1.0 + 0.4 × (avg_score / 10)²
        → 1.0 at bottom of scale, ~1.4 at top.
        """
        avg = (teacher_mark + ai_mark) / 2.0
        weight = 1.0 + 0.4 * ((avg / 10.0) ** 2)
        return round(weight, 3)

    def _compute_ocr_factor(self, ocr_confidence: float) -> float:
        """
        OCR Confidence Factor (0.5–1.0):
        If OCR confidence is below 90%, discount the inconsistency score
        because extraction errors—not grading bias—may explain the gap.

        Factor = max(0.5, ocr_confidence)
        (Never drops below 0.5 so borderline cases aren't zeroed out.)
        """
        return round(max(0.5, min(1.0, ocr_confidence)), 3)

    def _compute_directional_consistency(
        self,
        teacher_mark: float,
        ai_mark: float,
        session_history: Optional[list],
    ) -> Optional[str]:
        """
        Analyse session history to detect systematic directional bias.

        Returns:
            None if no history available.
            'consistent_undergrading' if teacher consistently scores below AI.
            'consistent_overgrading'  if teacher consistently scores above AI.
            'mixed'                   if disagreements vary in direction.
        """
        if not session_history or len(session_history) < 2:
            return None

        all_evals = session_history + [{"teacher": teacher_mark, "ai": ai_mark}]

        under_count = sum(1 for e in all_evals if e["teacher"] < e["ai"] - self.FAIRNESS_THRESHOLD)
        over_count  = sum(1 for e in all_evals if e["teacher"] > e["ai"] + self.FAIRNESS_THRESHOLD)
        total_biased = under_count + over_count

        if total_biased == 0:
            return "mixed"

        under_ratio = under_count / total_biased
        over_ratio  = over_count  / total_biased

        if under_ratio >= 0.75:
            return "consistent_undergrading"
        if over_ratio >= 0.75:
            return "consistent_overgrading"
        return "mixed"
