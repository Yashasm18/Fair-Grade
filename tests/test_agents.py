"""
FairGrade AI — Unit Tests

Run with:  pytest tests/ -v
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.privacy_agent import PrivacyAgent
from agents.bias_agent import BiasAgent
from agents.reporting_agent import ReportingAgent


# ---------------------------------------------------------------------------
# PrivacyAgent
# ---------------------------------------------------------------------------

class TestPrivacyAgent:
    def setup_method(self):
        self.agent = PrivacyAgent()

    def test_redacts_name(self):
        result = self.agent.anonymize("Name: Yashas Kumar\nAnswer: Photosynthesis...")
        assert "Yashas Kumar" not in result
        assert "[REDACTED]" in result

    def test_redacts_roll_number(self):
        result = self.agent.anonymize("Roll No: 2024CS001\nAnswer text here")
        assert "2024CS001" not in result
        assert "[REDACTED]" in result

    def test_redacts_student_id(self):
        result = self.agent.anonymize("Student ID: S-7890\nSome answer")
        assert "S-7890" not in result

    def test_preserves_answer_content(self):
        text = "Name: Alice\nPhotosynthesis converts CO2 and water into glucose."
        result = self.agent.anonymize(text)
        assert "Photosynthesis" in result
        assert "glucose" in result

    def test_no_identity_fields(self):
        text = "The mitochondria is the powerhouse of the cell."
        result = self.agent.anonymize(text)
        assert result == text  # Should be unchanged


# ---------------------------------------------------------------------------
# BiasAgent
# ---------------------------------------------------------------------------

class TestBiasAgent:
    def setup_method(self):
        self.agent = BiasAgent()

    def test_fair_grade_same_score(self):
        result = self.agent.detect_bias(teacher_mark=8, ai_mark=8)
        assert result["status"] == "Fair"
        assert result["severity"] == "Low"
        assert result["difference"] == 0

    def test_fair_grade_within_threshold(self):
        result = self.agent.detect_bias(teacher_mark=7, ai_mark=7.5)
        assert result["status"] == "Fair"

    def test_undergraded(self):
        result = self.agent.detect_bias(teacher_mark=4, ai_mark=8)
        assert result["status"] == "Undergraded"
        assert result["severity"] == "High"

    def test_overgraded(self):
        result = self.agent.detect_bias(teacher_mark=9, ai_mark=5)
        assert result["status"] == "Overgraded"
        assert result["severity"] == "High"

    def test_medium_severity(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7.5)
        assert result["severity"] == "Medium"

    def test_difference_is_absolute(self):
        r1 = self.agent.detect_bias(teacher_mark=3, ai_mark=8)
        r2 = self.agent.detect_bias(teacher_mark=8, ai_mark=3)
        assert r1["difference"] == r2["difference"]


# ---------------------------------------------------------------------------
# ReportingAgent
# ---------------------------------------------------------------------------

class TestReportingAgent:
    def setup_method(self):
        self.agent = ReportingAgent()

    def test_report_structure(self):
        report = self.agent.format_report(
            extracted_text="Name: Alice\nAnswer text",
            clean_text="Name: [REDACTED]\nAnswer text",
            evaluation={"score": 7, "explanation": "Good explanation of concepts."},
            bias_info={"severity": "Low", "status": "Fair", "difference": 0.5},
            teacher_score=7.5,
        )
        assert "originalTextLength" in report
        assert "anonymizedText" in report
        assert report["evaluation"]["aiScore"] == 7
        assert report["evaluation"]["teacherScore"] == 7.5
        assert report["bias"]["status"] == "Fair"

    def test_original_text_length_matches(self):
        text = "Name: Bob\nAnswer content here"
        report = self.agent.format_report(
            extracted_text=text,
            clean_text="Name: [REDACTED]\nAnswer content here",
            evaluation={"score": 6, "explanation": "Partial answer."},
            bias_info={"severity": "Medium", "status": "Undergraded", "difference": 2},
            teacher_score=4,
        )
        assert report["originalTextLength"] == len(text)


# ---------------------------------------------------------------------------
# BiasAgent — Bias Percentage Tests
# ---------------------------------------------------------------------------

class TestBiasPercentage:
    def setup_method(self):
        self.agent = BiasAgent()

    def test_bias_percentage_zero(self):
        """Zero difference = zero bias regardless of weights."""
        result = self.agent.detect_bias(teacher_mark=8, ai_mark=8, ai_confidence=1.0, answer_length=400)
        assert result["bias_score_percentage"] == 0.0

    def test_bias_percentage_weighted(self):
        """With full confidence (weight=1.2) and long answer (factor=1.1), bias is amplified."""
        result = self.agent.detect_bias(teacher_mark=2, ai_mark=9, ai_confidence=1.0, answer_length=400)
        # Raw = 70%, weighted = 70 * 1.2 * 1.1 = 92.4
        assert result["bias_score_percentage"] == 92.4

    def test_bias_percentage_low_confidence(self):
        """Low AI confidence should discount bias (AI itself is unsure)."""
        result = self.agent.detect_bias(teacher_mark=2, ai_mark=9, ai_confidence=0.3, answer_length=400)
        # confidence_weight = 0.5 + 0.3*0.7 = 0.71, completeness = 1.1
        # Raw = 70%, weighted = 70 * 0.71 * 1.1 = 54.7
        assert result["bias_score_percentage"] == 54.7

    def test_bias_percentage_short_answer(self):
        """Short answers should discount bias (AI may lack context)."""
        result = self.agent.detect_bias(teacher_mark=2, ai_mark=9, ai_confidence=1.0, answer_length=20)
        # confidence_weight = 1.2, completeness = 0.6
        # Raw = 70%, weighted = 70 * 1.2 * 0.6 = 50.4
        assert result["bias_score_percentage"] == 50.4

    def test_formula_present(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7)
        assert "formula_used" in result
        assert "Bias Score" in result["formula_used"]


# ---------------------------------------------------------------------------
# ReportingAgent — Confidence Score Tests
# ---------------------------------------------------------------------------

class TestReportingConfidence:
    def setup_method(self):
        self.agent = ReportingAgent()

    def test_confidence_score_included(self):
        report = self.agent.format_report(
            extracted_text="Answer text",
            clean_text="Answer text",
            evaluation={"score": 8, "explanation": "Good.", "confidence": 0.95},
            bias_info={"severity": "Low", "status": "Fair", "difference": 0.5,
                        "bias_score_percentage": 5.0, "formula_used": "test"},
            teacher_score=7.5,
        )
        assert report["evaluation"]["confidenceScore"] == 0.95

    def test_bias_percentage_in_report(self):
        report = self.agent.format_report(
            extracted_text="Answer text",
            clean_text="Answer text",
            evaluation={"score": 5, "explanation": "Partial.", "confidence": 0.7},
            bias_info={"severity": "High", "status": "Undergraded", "difference": 4,
                        "bias_score_percentage": 40.0, "formula_used": "test"},
            teacher_score=1,
        )
        assert report["bias"]["biasScorePercentage"] == 40.0

