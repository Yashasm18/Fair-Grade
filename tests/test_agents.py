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
