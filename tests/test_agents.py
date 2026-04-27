"""
FairGrade AI — Comprehensive Unit & Integration Tests

Run with:  pytest tests/ -v
           pytest tests/ -v -k "integration"   # integration only
           pytest tests/ -v -k "not integration" # unit only
"""

import io
import json
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.privacy_agent import PrivacyAgent
from agents.bias_agent import BiasAgent
from agents.reporting_agent import ReportingAgent
from agents.ocr_agent import OCRAgent, FALLBACK_MODELS
from agents.evaluation_agent import EvaluationAgent, _build_prompt, _is_quota_exhausted, _extract_retry_delay


# ===========================================================================
# PrivacyAgent
# ===========================================================================

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

    def test_redacts_batch(self):
        result = self.agent.anonymize("Batch: CS-2024\nThe mitochondria is the powerhouse.")
        assert "CS-2024" not in result

    def test_preserves_answer_content(self):
        text = "Name: Alice\nPhotosynthesis converts CO2 and water into glucose."
        result = self.agent.anonymize(text)
        assert "Photosynthesis" in result
        assert "glucose" in result

    def test_no_identity_fields(self):
        text = "The mitochondria is the powerhouse of the cell."
        result = self.agent.anonymize(text)
        assert result == text  # unchanged

    def test_inline_my_name_is(self):
        result = self.agent.anonymize("My name is John Smith and the answer is 42.")
        assert "John Smith" not in result
        assert "[REDACTED]" in result

    def test_redacts_id_number(self):
        result = self.agent.anonymize("ID Number: 99887\nContent here")
        assert "99887" not in result

    def test_empty_string(self):
        assert self.agent.anonymize("") == ""

    def test_multiple_fields(self):
        # Each identity field must be on its own line with a newline/comma terminator
        # so the regex boundary matches correctly.
        text = "Name: Alice\nRoll No: 123\nPhotosynthesis is important."
        result = self.agent.anonymize(text)
        assert "Alice" not in result
        assert "[REDACTED]" in result
        # Answer content on the line AFTER the identity field must be preserved
        assert "Photosynthesis" in result

    def test_inline_i_am(self):
        result = self.agent.anonymize("I am John Smith.\nThe answer is 42.")
        assert "John Smith" not in result
        assert "42" in result

    def test_inline_call_me(self):
        result = self.agent.anonymize("Call me Jane.\nMitochondria is the powerhouse.")
        assert "Jane" not in result
        assert "Mitochondria" in result



# ===========================================================================
# BiasAgent — v3.0 Composite Inconsistency Index
# ===========================================================================

class TestBiasAgent:
    def setup_method(self):
        self.agent = BiasAgent()

    def test_fair_grade_same_score(self):
        result = self.agent.detect_bias(teacher_mark=8, ai_mark=8)
        assert result["status"] == "Fair"
        assert result["severity"] == "Low Risk"
        assert result["difference"] == 0

    def test_fair_grade_within_threshold(self):
        result = self.agent.detect_bias(teacher_mark=7, ai_mark=7.5)
        assert result["status"] == "Fair"

    def test_undergraded(self):
        result = self.agent.detect_bias(teacher_mark=4, ai_mark=8)
        assert result["status"] == "Undergraded"
        assert result["severity"] == "High Risk"

    def test_overgraded(self):
        result = self.agent.detect_bias(teacher_mark=9, ai_mark=5)
        assert result["status"] == "Overgraded"
        assert result["severity"] == "High Risk"

    def test_medium_severity(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7.5)
        assert result["severity"] == "Medium Risk"

    def test_difference_is_absolute(self):
        r1 = self.agent.detect_bias(teacher_mark=3, ai_mark=8)
        r2 = self.agent.detect_bias(teacher_mark=8, ai_mark=3)
        assert r1["difference"] == r2["difference"]

    def test_bias_percentage_zero_diff(self):
        result = self.agent.detect_bias(teacher_mark=8, ai_mark=8, answer_length=400)
        assert result["bias_score_percentage"] == 0.0

    def test_bias_percentage_large_gap_nonzero(self):
        """Large gap + long answer → composite score > 0."""
        result = self.agent.detect_bias(teacher_mark=2, ai_mark=9, ai_confidence=1.0, answer_length=400)
        assert result["bias_score_percentage"] > 0

    def test_bias_percentage_short_answer_lower_than_long(self):
        """Short answer → lower composite score than same gap with long answer."""
        short = self.agent.detect_bias(teacher_mark=2, ai_mark=9, answer_length=20)
        long  = self.agent.detect_bias(teacher_mark=2, ai_mark=9, answer_length=1000)
        assert short["bias_score_percentage"] < long["bias_score_percentage"]

    def test_formula_present(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7)
        assert "formula_used" in result
        assert "Composite" in result["formula_used"]

    def test_completeness_factor_long_answer(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7, answer_length=10000)
        assert result["completeness_factor"] == 1.0

    def test_completeness_factor_empty_answer(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7, answer_length=0)
        assert result["completeness_factor"] > 0  # never zero

    def test_bias_capped_at_100(self):
        result = self.agent.detect_bias(teacher_mark=0, ai_mark=10, answer_length=10000)
        assert result["bias_score_percentage"] <= 100.0

    def test_all_required_keys_present(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7)
        for key in ("severity", "status", "difference", "bias_score_percentage",
                    "completeness_factor", "severity_weight", "ocr_penalty_applied",
                    "flag_manual_review", "directional_consistency",
                    "formula_used", "methodology_note"):
            assert key in result, f"Missing key: {key}"

    # ── New v3.0 tests ────────────────────────────────────────────────────

    def test_ocr_penalty_applied_low_confidence(self):
        """Low OCR confidence → ocr_penalty_applied=True and lower score."""
        high_ocr = self.agent.detect_bias(teacher_mark=2, ai_mark=9, answer_length=400, ocr_confidence=1.0)
        low_ocr  = self.agent.detect_bias(teacher_mark=2, ai_mark=9, answer_length=400, ocr_confidence=0.5)
        assert low_ocr["ocr_penalty_applied"] is True
        assert high_ocr["ocr_penalty_applied"] is False
        assert low_ocr["bias_score_percentage"] < high_ocr["bias_score_percentage"]

    def test_flag_manual_review_very_low_ocr(self):
        """OCR confidence < 0.75 → flag for manual review."""
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7, ocr_confidence=0.50)
        assert result["flag_manual_review"] is True

    def test_no_manual_review_flag_high_ocr(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7, ocr_confidence=0.95)
        assert result["flag_manual_review"] is False

    def test_significance_guard_small_gap_not_high_risk(self):
        """Gap exactly at FAIRNESS_THRESHOLD (1.0) → at most Medium Risk."""
        result = self.agent.detect_bias(teacher_mark=7, ai_mark=8, answer_length=10000)
        assert result["severity"] != "High Risk"

    def test_severity_weight_higher_for_high_scores(self):
        """Severity weight should be higher for high-band disagreements."""
        low  = self.agent._compute_severity_weight(1, 2)
        high = self.agent._compute_severity_weight(8, 9)
        assert high > low

    def test_directional_consistency_no_history(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=8, session_history=None)
        assert result["directional_consistency"] is None

    def test_directional_consistency_consistent_undergrading(self):
        history = [{"teacher": 4, "ai": 8}, {"teacher": 3, "ai": 7}, {"teacher": 5, "ai": 9}]
        result = self.agent.detect_bias(teacher_mark=4, ai_mark=8, session_history=history)
        assert result["directional_consistency"] == "consistent_undergrading"

    def test_directional_consistency_mixed(self):
        history = [{"teacher": 8, "ai": 4}, {"teacher": 3, "ai": 8}]
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7, session_history=history)
        assert result["directional_consistency"] == "mixed"

    def test_methodology_note_present(self):
        result = self.agent.detect_bias(teacher_mark=5, ai_mark=7)
        assert "methodology_note" in result
        assert "not ground truth" in result["methodology_note"]

    def test_consistent_undergrading_escalates_to_high_risk(self):
        """Directional consistency should escalate medium bias to high risk."""
        history = [
            {"teacher": 5, "ai": 7},
            {"teacher": 4, "ai": 6},
            {"teacher": 6, "ai": 8},
        ]
        result = self.agent.detect_bias(
            teacher_mark=5, ai_mark=7,
            answer_length=1000,
            session_history=history,
        )
        assert result["directional_consistency"] == "consistent_undergrading"
        assert result["severity"] == "High Risk"


# ===========================================================================
# OCRAgent — estimate_confidence heuristic
# ===========================================================================

class TestOCRConfidenceEstimation:
    def setup_method(self):
        self.agent = OCRAgent(gemini_client=None)

    def test_empty_text_returns_zero(self):
        assert self.agent.estimate_confidence("") == 0.0

    def test_fallback_text_returns_zero(self):
        assert self.agent.estimate_confidence("could not be extracted") == 0.0

    def test_ocr_failed_marker_returns_zero(self):
        assert self.agent.estimate_confidence("[OCR FAILED] something") == 0.0

    def test_very_short_text_low_confidence(self):
        score = self.agent.estimate_confidence("Hello")
        assert score < 0.5

    def test_metadata_only_medium_confidence(self):
        text = "Name: Alice\nRoll No: 123\nDate: 2024-01-01"
        score = self.agent.estimate_confidence(text)
        assert score <= 0.6

    def test_full_answer_high_confidence(self):
        text = (
            "The mitochondria is the powerhouse of the cell. "
            "It generates ATP through oxidative phosphorylation. "
            "The electron transport chain is located on the inner membrane. "
            "This process creates a proton gradient used to synthesize ATP."
        )
        score = self.agent.estimate_confidence(text)
        assert score >= 0.9


# ===========================================================================
# ReportingAgent
# ===========================================================================

class TestReportingAgent:
    def setup_method(self):
        self.agent = ReportingAgent()

    def _sample_report(self, **overrides):
        defaults = dict(
            extracted_text="Name: Alice\nAnswer text",
            clean_text="Name: [REDACTED]\nAnswer text",
            evaluation={"score": 7, "explanation": "Good.", "confidence": 0.9},
            bias_info={"severity": "Low Risk", "status": "Fair", "difference": 0.5,
                       "bias_score_percentage": 5.0, "completeness_factor": 1.0, "formula_used": "test"},
            teacher_score=7.5,
        )
        defaults.update(overrides)
        return self.agent.format_report(**defaults)

    def test_report_structure(self):
        report = self._sample_report()
        assert "originalTextLength" in report
        assert "anonymizedText" in report
        assert "evaluation" in report
        assert "bias" in report

    def test_original_text_length_matches(self):
        text = "Name: Bob\nAnswer content here"
        report = self._sample_report(extracted_text=text)
        assert report["originalTextLength"] == len(text)

    def test_ai_score_in_report(self):
        report = self._sample_report(evaluation={"score": 8, "explanation": "Good.", "confidence": 0.95})
        assert report["evaluation"]["aiScore"] == 8

    def test_teacher_score_in_report(self):
        report = self._sample_report(teacher_score=6.5)
        assert report["evaluation"]["teacherScore"] == 6.5

    def test_confidence_score_included(self):
        report = self._sample_report(evaluation={"score": 8, "explanation": "Good.", "confidence": 0.95})
        assert report["evaluation"]["confidenceScore"] == 0.95

    def test_confidence_defaults_to_zero(self):
        report = self._sample_report(evaluation={"score": 8, "explanation": "Good."})
        assert report["evaluation"]["confidenceScore"] == 0.0

    def test_bias_percentage_in_report(self):
        bias = {"severity": "High Risk", "status": "Undergraded", "difference": 4,
                "bias_score_percentage": 40.0, "formula_used": "test"}
        report = self._sample_report(bias_info=bias)
        assert report["bias"]["biasScorePercentage"] == 40.0

    def test_no_confidence_weight_field(self):
        """confidenceWeight was removed as it was always 1.0 (dead field)."""
        report = self._sample_report()
        assert "confidenceWeight" not in report["bias"]


# ===========================================================================
# OCRAgent — mocked Gemini Vision calls
# ===========================================================================

class TestOCRAgent:
    """All Gemini I/O is mocked — no real API calls."""

    def _make_mock_client(self, text="Extracted text"):
        mock_response = MagicMock()
        mock_response.text = text
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        return mock_client

    def test_extract_text_success(self):
        agent = OCRAgent(gemini_client=self._make_mock_client("Hello world"))
        # Provide minimal 1x1 PNG bytes so PIL can open it
        import struct, zlib
        def png_1x1():
            sig = b'\x89PNG\r\n\x1a\n'
            ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
            ihdr_chunk = b'IHDR' + ihdr
            ihdr_crc = struct.pack('>I', zlib.crc32(ihdr_chunk) & 0xffffffff)
            idat_data = zlib.compress(b'\x00\xff\xff\xff')
            idat_chunk = b'IDAT' + idat_data
            idat_crc = struct.pack('>I', zlib.crc32(idat_chunk) & 0xffffffff)
            iend_crc = struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
            return (sig + b'\x00\x00\x00\rIHDR' + ihdr + ihdr_crc +
                    b'\x00\x00\x00' + bytes([len(idat_data)]) + idat_chunk + idat_crc +
                    b'\x00\x00\x00\x00IEND' + iend_crc)
        result = agent.extract_text(png_1x1(), "test.png")
        assert result == "Hello world"

    def test_no_client_returns_fallback(self):
        agent = OCRAgent(gemini_client=None)
        result = agent.extract_text(b"fake bytes", "test.png")
        assert "[OCR FAILED]" in result or "could not be extracted" in result

    def test_empty_response_returns_fallback(self):
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        agent = OCRAgent(gemini_client=mock_client)
        result = agent.extract_text(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50, "test.png")
        # Should fall through all models and return DEMO_FALLBACK_TEXT
        assert result is not None

    def test_fallback_models_list_valid(self):
        """gemini-2.5-flash-lite was removed — verify it's no longer in the list."""
        assert "gemini-2.5-flash-lite" not in FALLBACK_MODELS
        assert len(FALLBACK_MODELS) >= 2

    def test_quota_exhausted_tries_next_model(self):
        """On 429 quota-exhausted, agent should try the next model."""
        call_count = [0]
        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("429 RESOURCE_EXHAUSTED limit: 0")
            mock_resp = MagicMock()
            mock_resp.text = "Success on second model"
            return mock_resp

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = side_effect
        agent = OCRAgent(gemini_client=mock_client)

        import struct, zlib
        # Provide a minimal valid PNG for PIL
        png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        result = agent._run_gemini_ocr(png)
        assert result == "Success on second model"
        assert call_count[0] == 2


# ===========================================================================
# EvaluationAgent — mocked Gemini calls
# ===========================================================================

class TestEvaluationAgent:
    """All Gemini I/O is mocked — no real API calls."""

    def _make_agent(self, response_json: dict):
        mock_response = MagicMock()
        mock_response.text = json.dumps(response_json)
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        return EvaluationAgent(gemini_client=mock_client)

    def test_evaluate_returns_score(self):
        agent = self._make_agent({"score": 8, "explanation": "Good.", "confidence": 0.9,
                                  "thought_process": "...", "bias_indicators": []})
        result = agent.evaluate("Some answer text", "What is photosynthesis?")
        assert result["score"] == 8
        assert result["confidence"] == 0.9
        # v2.1: weighted fields should be present
        assert "weighted_score" in result
        assert result["question_weight"] == 1.0
        assert "bias_indicators" in result

    def test_evaluate_no_client_returns_mock(self):
        agent = EvaluationAgent(gemini_client=None)
        result = agent.evaluate("Any text")
        assert result["score"] == 8
        assert "Mocked" in result["explanation"]
        assert result["confidence"] == 0.0
        # v2.1: also returns weighted_score, question_weight, bias_indicators
        assert "weighted_score" in result
        assert "question_weight" in result
        assert "bias_indicators" in result

    def test_evaluate_strips_markdown_fences(self):
        mock_response = MagicMock()
        mock_response.text = "```json\n{\"score\": 7, \"explanation\": \"OK\", \"confidence\": 0.8, \"thought_process\": \"...\", \"bias_indicators\": []}\n```"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        agent = EvaluationAgent(gemini_client=mock_client)
        result = agent.evaluate("Some text")
        assert result["score"] == 7

    def test_evaluate_quota_exhausted_falls_back(self):
        """All models return quota-exhausted — should return score 0 with QUOTA_EXHAUSTED."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(
            "429 RESOURCE_EXHAUSTED limit: 0 exceeded your current quota"
        )
        agent = EvaluationAgent(gemini_client=mock_client)
        result = agent.evaluate("Some text")
        assert result["score"] == 0
        assert "QUOTA_EXHAUSTED" in result["explanation"]

    def test_build_prompt_includes_answer(self):
        prompt = _build_prompt("My answer here", "What is photosynthesis?", 1.0)
        assert "My answer here" in prompt
        assert "What is photosynthesis?" in prompt

    def test_build_prompt_no_context(self):
        prompt = _build_prompt("My answer", None, 1.0)
        assert "No specific context provided" in prompt

    def test_build_prompt_weighted_note(self):
        prompt = _build_prompt("My answer", "Explain osmosis.", 2.0)
        assert "WEIGHT" in prompt
        assert "2.0x" in prompt

    def test_is_quota_exhausted_true(self):
        assert _is_quota_exhausted("limit: 0 exceeded your current quota") is True

    def test_is_quota_exhausted_false(self):
        assert _is_quota_exhausted("RESOURCE_EXHAUSTED rate limit") is False

    def test_extract_retry_delay_seconds(self):
        delay = _extract_retry_delay("retryDelay: 30.0s please wait")
        assert delay == 30.0

    def test_extract_retry_delay_none(self):
        assert _extract_retry_delay("some other error") is None

    def test_evaluate_missing_keys_defaults(self):
        """Partial JSON from API — agent should gracefully default missing keys."""
        agent = self._make_agent({"score": 5, "thought_process": "..."})  # missing explanation, confidence, bias_indicators
        result = agent.evaluate("Some text")
        assert result["score"] == 5
        assert result["explanation"] == ""
        assert result["confidence"] == 1.0  # default
        assert result["bias_indicators"] == []  # v2.1 default


# ===========================================================================
# Integration Tests — FastAPI TestClient (no real Gemini calls)
# ===========================================================================

class TestAPIIntegration:
    """
    End-to-end tests against the FastAPI app using TestClient.
    All Gemini SDK calls are mocked at the agent level.
    """

    @pytest.fixture(autouse=True)
    def setup_app(self, monkeypatch):
        """Patch agents before importing the app to avoid real Gemini init."""
        import agents
        # Patch OCRAgent to return canned text
        monkeypatch.setattr(agents.OCRAgent, "extract_text",
                            lambda self, b, n: "Name: Test Student\nPhotosynthesis makes glucose.")
        # Patch EvaluationAgent to return canned evaluation (v2.1 shape)
        monkeypatch.setattr(agents.EvaluationAgent, "evaluate",
                            lambda self, t, q=None, w=1.0: {
                                "score": 7,
                                "weighted_score": 7.0,
                                "question_weight": 1.0,
                                "explanation": "Good answer.",
                                "confidence": 0.88,
                                "bias_indicators": ["Correct: main concept named"],
                            })

        # Clear API key auth so integration tests don't need to send a header
        monkeypatch.setenv("FAIRGRADE_API_KEY", "")

        # Import app module AFTER patches are applied
        # Use a fresh sys.modules pop so monkeypatch env is respected
        import sys
        sys.modules.pop("app", None)
        import app as app_module

        from fastapi.testclient import TestClient
        self.client = TestClient(app_module.app)

    def test_health_check(self):
        r = self.client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "FairGrade AI backend is running"
        assert "google_tech" in data

    def test_evaluate_valid_png(self):
        # Minimal 8-byte PNG header (file validation passes, agent is mocked)
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        r = self.client.post(
            "/api/evaluate",
            files={"file": ("test.png", png_bytes, "image/png")},
            data={"teacher_score": "7.5"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "evaluation" in data
        assert "bias" in data
        assert data["evaluation"]["aiScore"] == 7
        assert data["evaluation"]["teacherScore"] == 7.5

    def test_evaluate_unsupported_file_type(self):
        r = self.client.post(
            "/api/evaluate",
            files={"file": ("test.txt", b"some text", "text/plain")},
            data={"teacher_score": "5"},
        )
        assert r.status_code == 400
        assert "Unsupported file type" in r.json()["detail"]

    def test_evaluate_file_too_large(self):
        big_file = b'\x89PNG\r\n\x1a\n' + b'\x00' * (11 * 1024 * 1024)
        r = self.client.post(
            "/api/evaluate",
            files={"file": ("big.png", big_file, "image/png")},
            data={"teacher_score": "5"},
        )
        assert r.status_code == 413
        assert "too large" in r.json()["detail"]

    def test_evaluate_missing_teacher_score(self):
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        r = self.client.post(
            "/api/evaluate",
            files={"file": ("test.png", png_bytes, "image/png")},
            # teacher_score omitted
        )
        assert r.status_code == 422  # Pydantic validation error

    def test_evaluate_with_question_context(self):
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        r = self.client.post(
            "/api/evaluate",
            files={"file": ("test.png", png_bytes, "image/png")},
            data={"teacher_score": "8", "question_context": "Explain photosynthesis."},
        )
        assert r.status_code == 200

    def test_verify_accept_ai(self):
        r = self.client.post(
            "/api/verify",
            json={
                "fileName": "test.png",
                "originalAiScore": 7.0,
                "originalTeacherScore": 8.0,
                "finalScore": 7.0,
                "action": "accept_ai",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["verified"] is True
        assert data["action"] == "accept_ai"

    def test_verify_override(self):
        r = self.client.post(
            "/api/verify",
            json={
                "fileName": "test.png",
                "originalAiScore": 5.0,
                "originalTeacherScore": 9.0,
                "finalScore": 9.0,
                "action": "override",
                "overrideReason": "Student showed working correctly.",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "override"
        assert data["overrideReason"] == "Student showed working correctly."

    def test_verify_invalid_action(self):
        r = self.client.post(
            "/api/verify",
            json={
                "fileName": "test.png",
                "originalAiScore": 5.0,
                "originalTeacherScore": 9.0,
                "finalScore": 9.0,
                "action": "delete",
            },
        )
        assert r.status_code == 400

    def test_evaluate_pdf_multipart(self):
        """PDF files should be accepted (content-type check)."""
        pdf_bytes = b'%PDF-1.4 fake pdf content'
        r = self.client.post(
            "/api/evaluate",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
            data={"teacher_score": "6"},
        )
        # Should not 400 on file type — may fail on PDF parsing but not type check
        assert r.status_code != 400 or "Unsupported" not in r.json().get("detail", "")

    def test_report_contains_verified_false(self):
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        r = self.client.post(
            "/api/evaluate",
            files={"file": ("test.png", png_bytes, "image/png")},
            data={"teacher_score": "7"},
        )
        assert r.status_code == 200
        assert r.json()["verified"] is False
