"""
Reporting Agent — Compiles pipeline outputs into a structured final report.

Formats results from OCR, Privacy, Evaluation, and Bias agents
into a clean JSON response for the frontend.
"""


class ReportingAgent:
    """Agent 5 — Assembles the final evaluation report returned to the client."""

    def format_report(
        self,
        extracted_text: str,
        clean_text: str,
        evaluation: dict,
        bias_info: dict,
        teacher_score: float,
    ) -> dict:
        """
        Build the structured JSON report sent back to the React frontend.

        Args:
            extracted_text: Raw OCR output (used only for length metric).
            clean_text: Anonymized version of the student's answer.
            evaluation: Output from EvaluationAgent (score + explanation).
            bias_info: Output from BiasAgent (status, severity, difference).
            teacher_score: Original teacher-assigned mark.

        Returns:
            Structured dict ready to be serialised as JSON.
        """
        return {
            "originalTextLength": len(extracted_text),
            "anonymizedText": clean_text,
            "evaluation": {
                "aiScore": evaluation["score"],
                "teacherScore": teacher_score,
                "explanation": evaluation["explanation"],
            },
            "bias": {
                "level": bias_info["severity"],
                "status": bias_info["status"],
                "gap": bias_info["difference"],
            },
        }
