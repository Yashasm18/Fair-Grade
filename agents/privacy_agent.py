"""
Privacy Agent — Strips student identity markers before AI grading.

Removes names, student IDs, roll numbers, and batch identifiers
to prevent implicit bias from propagating into the evaluation step.
"""

import re

# Patterns that may reveal student identity
_IDENTITY_PATTERNS = [
    r'(?i)(Name\s*[:\-]?\s*)([^\n]+)',
    r'(?i)(Roll\s*No[\.:]?\s*[:\-]?\s*)([^\n]+)',
    r'(?i)(ID\s*Number\s*[:\-]?\s*)([^\n]+)',
    r'(?i)(Student\s*ID\s*[:\-]?\s*)([^\n]+)',
    r'(?i)(Batch\s*[:\-]?\s*)([^\n]+)',
]


class PrivacyAgent:
    """Agent 2 — Anonymizes student identity fields to prevent grader bias."""

    def anonymize(self, text: str) -> str:
        """
        Replace identity-revealing fields with [REDACTED].

        Args:
            text: Raw OCR-extracted text from the answer sheet.

        Returns:
            Anonymized text safe for AI evaluation.
        """
        clean_text = text
        for pattern in _IDENTITY_PATTERNS:
            clean_text = re.sub(
                pattern,
                lambda m: m.group(1) + "[REDACTED]",
                clean_text,
            )
        return clean_text
