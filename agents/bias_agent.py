"""
Bias Detection Agent — Compares AI score vs. teacher score to flag grading inconsistencies.

Classifies each result as Undergraded, Overgraded, or Fair, with a severity level.
"""


class BiasAgent:
    """Agent 4 — Detects grading bias by comparing teacher score vs. AI score."""

    # Thresholds for bias severity classification
    HIGH_BIAS_THRESHOLD = 3.0
    MEDIUM_BIAS_THRESHOLD = 1.0

    def detect_bias(self, teacher_mark: float, ai_mark: float) -> dict:
        """
        Detect and classify grading inconsistency.

        Args:
            teacher_mark: Score assigned by the human teacher (0–10).
            ai_mark: Score assigned by the AI evaluation agent (0–10).

        Returns:
            dict with keys:
                - 'status': 'Undergraded' | 'Overgraded' | 'Fair'
                - 'severity': 'High' | 'Medium' | 'Low'
                - 'difference': absolute score gap (float)
        """
        diff = abs(teacher_mark - ai_mark)
        severity = self._classify_severity(diff)
        status = self._classify_status(teacher_mark, ai_mark)
        return {"severity": severity, "status": status, "difference": diff}

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
