"""
Bias Detection Agent — Multi-Factor Weighted Bias Analysis

Goes beyond simple score comparison by incorporating:
  1. Score Difference (core signal)
  2. AI Confidence Weight (Gemini's self-reported certainty)
  3. Answer Completeness Factor (text length as proxy for effort)

This produces a nuanced bias score that accounts for HOW confident
the AI was and HOW much the student actually wrote.
"""


class BiasAgent:
    """Agent 4 — Detects grading bias using a weighted multi-factor algorithm."""

    # Thresholds for bias severity classification
    HIGH_BIAS_THRESHOLD = 3.0
    MEDIUM_BIAS_THRESHOLD = 1.0

    # Answer completeness thresholds (character count)
    SHORT_ANSWER_THRESHOLD = 50
    LONG_ANSWER_THRESHOLD = 300

    def detect_bias(
        self,
        teacher_mark: float,
        ai_mark: float,
        ai_confidence: float = 1.0,
        answer_length: int = 200,
    ) -> dict:
        """
        Detect and classify grading inconsistency using weighted multi-factor analysis.

        Args:
            teacher_mark: Score assigned by the human teacher (0–10).
            ai_mark: Score assigned by the AI evaluation agent (0–10).
            ai_confidence: AI's self-reported confidence (0.0–1.0).
            answer_length: Character count of the student's answer text.

        Returns:
            dict with keys:
                - 'status': 'Undergraded' | 'Overgraded' | 'Fair'
                - 'severity': 'High' | 'Medium' | 'Low'
                - 'difference': absolute score gap (float)
                - 'bias_score_percentage': weighted bias severity as a percentage (float)
                - 'confidence_weight': multiplier from AI confidence (float)
                - 'completeness_factor': multiplier from answer length (float)
                - 'formula_used': string explaining the logic
        """
        diff = abs(teacher_mark - ai_mark)
        severity = self._classify_severity(diff)
        status = self._classify_status(teacher_mark, ai_mark)

        # ── Multi-Factor Weights ──────────────────────────────────────────
        confidence_weight = self._compute_confidence_weight(ai_confidence)
        completeness_factor = self._compute_completeness_factor(answer_length)

        # ── Weighted Bias Formula ─────────────────────────────────────────
        # Raw bias as percentage of max score (10)
        raw_bias = (diff / 10.0) * 100

        # Apply weights: high-confidence AI + complete answers = more trustworthy signal
        weighted_bias = raw_bias * confidence_weight * completeness_factor
        weighted_bias = min(round(weighted_bias, 1), 100.0)

        formula = (
            "Bias Score (%) = (|Teacher − AI| / 10) × 100 "
            f"× Confidence Weight ({confidence_weight}) "
            f"× Completeness Factor ({completeness_factor})"
        )

        return {
            "severity": severity,
            "status": status,
            "difference": diff,
            "bias_score_percentage": weighted_bias,
            "confidence_weight": confidence_weight,
            "completeness_factor": completeness_factor,
            "formula_used": formula,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _classify_severity(self, diff: float) -> str:
        if diff > self.HIGH_BIAS_THRESHOLD:
            return "High"
        if diff > self.MEDIUM_BIAS_THRESHOLD:
            return "Medium"
        return "Low"

    def _classify_status(self, teacher_mark: float, ai_mark: float) -> str:
        if teacher_mark < ai_mark - self.MEDIUM_BIAS_THRESHOLD:
            return "Undergraded"
        if teacher_mark > ai_mark + self.MEDIUM_BIAS_THRESHOLD:
            return "Overgraded"
        return "Fair"

    def _compute_confidence_weight(self, confidence: float) -> float:
        """
        Higher AI confidence → stronger bias signal.
        Low confidence → discount the bias (AI itself is unsure).

        Maps 0.0–1.0 confidence to a 0.5–1.2 weight range.
        """
        confidence = max(0.0, min(1.0, confidence))
        return round(0.5 + (confidence * 0.7), 2)

    def _compute_completeness_factor(self, char_count: int) -> float:
        """
        Longer, more complete answers provide a more reliable evaluation signal.
        Very short answers (< 50 chars) → discount bias (AI may lack context).
        Medium answers (50-300 chars) → neutral weight.
        Long answers (> 300 chars) → slight boost (more data for AI).

        Maps to a 0.6–1.1 weight range.
        """
        if char_count < self.SHORT_ANSWER_THRESHOLD:
            return 0.6
        if char_count < self.LONG_ANSWER_THRESHOLD:
            return 0.9
        return 1.1
