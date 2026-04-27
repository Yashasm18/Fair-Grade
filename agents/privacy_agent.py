"""
Privacy Agent — Strips student identity markers before AI grading.

Removes names, student IDs, roll numbers, and batch identifiers
to prevent implicit bias from propagating into the evaluation step.

v2: Tightened header-field regexes to use [^\n,]{1,40} (no \s that
    crosses newlines) so answer text on subsequent lines is preserved.
"""

import re

# ---------------------------------------------------------------------------
# Header-field patterns — each anchored to end at newline OR comma OR EOS.
# IMPORTANT: The value group MUST NOT use \s (which matches \n) to avoid
# greedily consuming lines that follow the identity field.
# ---------------------------------------------------------------------------
_IDENTITY_PATTERNS = [
    # "Name: Alice Kumar"
    r'(?i)(Name\s*[:\-]?\s*)([^\n,]{2,40})(?=[\n,]|$)',
    # "Roll No: 2024CS001" / "Roll No.: ABC-123"
    r'(?i)(Roll\s*No\.?[:\-]?\s*)([^\n,]{1,30})(?=[\n,]|$)',
    # "ID Number: 99887"
    r'(?i)(ID\s*Number\s*[:\-]?\s*)([^\n,]{1,30})(?=[\n,]|$)',
    # "Student ID: S-7890"
    r'(?i)(Student\s*ID\s*[:\-]?\s*)([^\n,]{1,30})(?=[\n,]|$)',
    # "Batch: CS-2024"
    r'(?i)(Batch\s*[:\-]?\s*)([^\n,]{1,30})(?=[\n,]|$)',

    # Inline natural language — Proper-cased name required (reduces false positives)
    r'(?i)(my\s+name\s+is\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
    r'(?i)(this\s+(?:test|paper|exam)\s+belongs\s+to\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
    r'(?i)(I\s+am\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})(?=\s*[,.\n])',
    r'(?i)(call\s+me\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})(?=\s*[,.\n])',
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
                r'\g<1>[REDACTED]',
                clean_text,
            )
        return clean_text
