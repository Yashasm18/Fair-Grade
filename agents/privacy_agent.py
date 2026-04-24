"""
Privacy Agent — Strips student identity markers before AI grading.

Removes names, student IDs, roll numbers, and batch identifiers
to prevent implicit bias from propagating into the evaluation step.
"""

import re

# Patterns that may reveal student identity
_IDENTITY_PATTERNS = [
    # Header fields (Name, Roll No, etc.) - Match up to a comma, newline, or 40 chars max to prevent greedy matching deleting the whole text
    r'(?i)(Name\s*[:\-]?\s*)([A-Za-z\s]{2,40})(?:[\n,]|$)',
    r'(?i)(Roll\s*No[\.:]?\s*[:\-]?\s*)([A-Za-z0-9\s\-\.]+)(?:[\n,]|$)',
    r'(?i)(ID\s*Number\s*[:\-]?\s*)([A-Za-z0-9\s\-\.]+)(?:[\n,]|$)',
    r'(?i)(Student\s*ID\s*[:\-]?\s*)([A-Za-z0-9\s\-\.]+)(?:[\n,]|$)',
    r'(?i)(Batch\s*[:\-]?\s*)([A-Za-z0-9\s\-\.]+)(?:[\n,]|$)',
    
    # Inline natural language statements
    r'(?i)(my\s+name\s+is\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
    r'(?i)(this\s+(?:test|paper|exam)\s+belongs\s+to\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})'
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
                r'\g<1>[REDACTED]\n', # Keeps the prefix ("Name: "), adds REDACTED, restores newline if matched
                clean_text,
            )
        return clean_text
