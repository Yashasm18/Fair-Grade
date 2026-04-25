"""
Bias Detection Agent — Score Comparison with Completeness Adjustment

Calculates a clean, explainable bias score:
  1. Bias Score (%) = min(100, |Teacher − AI| × 10)
  2. Completeness Factor = min(1.0, log(1 + word_count) / log(120))
  3. Final Bias Score = Bias Score × Completeness Factor

This produces a fair, transparent bias metric that adjusts for
how much the student actually wrote.
"""

import math


class BiasAgent:
    """Agent 4 — Detects grading bias using score difference and completeness adjustment."""

    # Thresholds for risk classification (Percentage)
    HIGH_RISK_THRESHOLD = 30.0
    MEDIUM_RISK_THRESHOLD = 15.0

    # Threshold for status classification (Mark Difference)
    FAIRNESS_THRESHOLD = 1.0

    def detect_bias(
        self,
        teacher_mark: float,
        ai_mark: float,
        ai_confidence: float = 1.0,
        answer_length: int = 200,
    ) -> dict:
        """
        Detect and classify grading inconsistency.

        Args:
            teacher_mark: Score assigned by the human teacher (0–10).
            ai_mark: Score assigned by the AI evaluation agent (0–10).
            ai_confidence: AI's self-reported confidence (0.0–1.0). Stored but not used in scoring.
            answer_length: Character count of the student's answer text.

        Returns:
            dict with keys:
                - 'status': 'Undergraded' | 'Overgraded' | 'Fair'
                - 'severity': 'High' | 'Medium' | 'Low'
                - 'difference': absolute score gap (float)
                - 'bias_score_percentage': final bias severity as a percentage (float)
                - 'completeness_factor': multiplier from answer length (float)
                - 'formula_used': string explaining the logic
        """
        diff = abs(teacher_mark - ai_mark)
        status = self._classify_status(teacher_mark, ai_mark)

        # ── Completeness Factor ───────────────────────────────────────────
        completeness_factor = self._compute_completeness_factor(answer_length)

        # ── Bias Score Formula ────────────────────────────────────────────
        # Raw bias: simple percentage of max score difference
        raw_bias = min(100.0, diff * 10)

        # Apply completeness adjustment
        final_bias = raw_bias * completeness_factor
        final_bias = min(round(final_bias, 1), 100.0)

        # Classify risk based on FINAL percentage
        severity = self._classify_severity(final_bias)

        formula = (
            f"Bias Score (%) = min(100, |{teacher_mark} − {ai_mark}| × 10) "
            f"× Completeness Factor ({completeness_factor})"
        )

        return {
            "severity": severity,
            "status": status,
            "difference": diff,
            "bias_score_percentage": final_bias,
            "completeness_factor": completeness_factor,
            "formula_used": formula,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _classify_severity(self, final_bias: float) -> str:
        """Classify risk based on final bias percentage."""
        if final_bias > self.HIGH_RISK_THRESHOLD:
            return "High"
        if final_bias > self.MEDIUM_RISK_THRESHOLD:
            return "Medium"
        return "Low"

    def _classify_status(self, teacher_mark: float, ai_mark: float) -> str:
        """Classify status based on raw mark difference."""
        if teacher_mark < ai_mark - self.FAIRNESS_THRESHOLD:
            return "Undergraded"
        if teacher_mark > ai_mark + self.FAIRNESS_THRESHOLD:
            return "Overgraded"
        return "Fair"

    def _compute_completeness_factor(self, char_count: int) -> float:
        """
        Completeness Factor = min(1.0, log(1 + word_count) / log(120))

        Longer answers provide a more reliable evaluation signal.
        Very short answers → discount bias (AI may lack context).
        Uses logarithmic scaling for a smooth, fair curve.
        """
        # Approximate word count from character count (~5 chars per word)
        word_count = max(1, char_count // 5)
        factor = math.log(1 + word_count) / math.log(120)
        return round(min(1.0, factor), 2)
