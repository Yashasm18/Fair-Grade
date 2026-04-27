"""
OCR Agent — Extracts text from uploaded answer sheet images/PDFs.

Google Cloud Technology: Google Gemini Vision API (gemini-2.5-pro)
Primary model: gemini-2.5-pro (93% OCR accuracy on handwritten text).
Fallback chain: gemini-2.5-flash → gemini-2.0-flash → gemini-2.0-flash-lite.
Images are processed entirely in-memory and never written to disk.
"""

import io
import time
import os
from typing import Optional


def _get_gemini_client():
    """Lazy import to avoid circular dependencies."""
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


# gemini-2.5-pro is the primary model for maximum OCR accuracy (93% on handwritten text).
# Falls back to flash models if Pro quota is exhausted on the free tier.
FALLBACK_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

# Prompt asks Gemini to output JSON with both text AND self-reported confidence.
# This replaces keyword heuristics with the model's own epistemic assessment.
EXTRACT_PROMPT = (
    "Extract all the handwritten and printed text from this image exactly as written. "
    "Preserve the original formatting and line breaks. "
    "CRITICAL: Pay extremely close attention to mathematical operators (÷, /, +, -) and "
    "numerical figures to ensure calculations are transcribed accurately. "
    "Respond ONLY with a JSON object in this exact format (no markdown fences):\n"
    '{"text": "<full extracted text>", "confidence": <integer 0-100>}\n'
    "Where confidence is YOUR honest estimate of how accurately you read the handwriting: "
    "100 = perfectly clear print, 80-99 = mostly clear with minor uncertainty, "
    "60-79 = some words unclear, 40-59 = significant portions hard to read, "
    "0-39 = mostly illegible. "
    "If the image is completely unreadable, return: "
    '{"text": "[OCR FAILED]", "confidence": 0}'
)

# Legacy plain-text prompt — used as fallback if JSON parsing fails
_EXTRACT_PROMPT_PLAIN = (
    "Extract all the handwritten and printed text from this image exactly as written. "
    "Preserve the original formatting and line breaks. "
    "CRITICAL: Pay extremely close attention to mathematical operators (÷, /, +, -) and "
    "numerical figures to ensure calculations are transcribed accurately. "
    "Do not add any extra commentary or markdown formatting."
)

DEMO_FALLBACK_TEXT = (
    "Name: [REDACTED]\nRoll No: 12345\n\n"
    "The student answer could not be extracted by the OCR."
)


class OCRAgent:
    """Agent 1 — Extracts raw text from answer sheet images or PDFs."""

    def __init__(self, gemini_client=None):
        self.client = gemini_client

    # Minimum character count for a response to be considered high-confidence
    _MIN_HIGH_CONFIDENCE_CHARS = 50
    # Indicators of OCR failure or low quality
    _LOW_QUALITY_INDICATORS = ("could not be extracted", "[ocr failed]", "unable to read", "illegible")

    def extract_text(self, file_bytes: bytes, filename: str = "") -> str:
        """
        Extract text from image bytes or PDF using Gemini Vision API.
        Returns plain text string. Use extract_text_with_confidence() for
        the full result including model-self-reported confidence.
        """
        result = self.extract_text_with_confidence(file_bytes, filename)
        return result["text"]

    def extract_text_with_confidence(
        self, file_bytes: bytes, filename: str = ""
    ) -> dict:
        """
        Extract text AND Gemini's self-reported confidence in one call.

        Gemini is prompted to output structured JSON:
            {"text": "...", "confidence": 87}

        The confidence integer (0-100) represents the model's own epistemic
        assessment of how well it could read the handwriting — replacing the
        keyword-heuristic estimate_confidence() method.

        Falls back to estimate_confidence() heuristic only if JSON parsing fails.

        Returns:
            dict with keys:
                - 'text':       str  — extracted text
                - 'confidence': float — model-reported confidence 0.0-1.0
                - 'source':     'model' | 'heuristic' — where the confidence came from
        """
        file_bytes = self._pdf_to_image_bytes(file_bytes, filename)
        raw = self._run_gemini_ocr(file_bytes)

        if not raw:
            return {"text": DEMO_FALLBACK_TEXT, "confidence": 0.0, "source": "heuristic"}

        # Try to parse model-reported JSON response
        parsed = self._parse_ocr_json(raw)
        if parsed is not None:
            text = parsed.get("text", "") or DEMO_FALLBACK_TEXT
            confidence = max(0.0, min(1.0, parsed.get("confidence", 95) / 100.0))
            return {"text": text, "confidence": confidence, "source": "model"}

        # JSON parse failed — model returned plain text (older fallback models)
        # Fall back to heuristic confidence estimation
        confidence = self.estimate_confidence(raw)
        return {"text": raw, "confidence": confidence, "source": "heuristic"}

    def estimate_confidence(self, extracted_text: str) -> float:
        """
        Estimate OCR confidence based on heuristic quality signals.

        This is a proxy metric — a proper confidence score would require
        a character-level recognition model. This heuristic covers the
        most common failure modes in practice.

        Rules (all apply independently; lowest score wins):
          - Fallback / failure text          → 0.0
          - Too short (< 50 chars)           → 0.4  (likely partial extraction)
          - Contains low-quality indicators  → 0.5
          - Looks like pure metadata (name/roll only) → 0.6
          - Otherwise                        → 0.95 (high confidence)

        Returns:
            float in [0.0, 1.0]
        """
        if not extracted_text or extracted_text.strip() == "":
            return 0.0

        lower = extracted_text.lower()

        # Hard failure — fallback text was returned
        if "could not be extracted" in lower or "[ocr failed]" in lower:
            return 0.0

        # Very short extraction — likely partial or empty page
        if len(extracted_text.strip()) < self._MIN_HIGH_CONFIDENCE_CHARS:
            return 0.4

        # Low-quality indicator phrases
        for indicator in self._LOW_QUALITY_INDICATORS:
            if indicator in lower:
                return 0.5

        # Only metadata lines (name/roll/date) — no substantive content
        lines = [l.strip() for l in extracted_text.splitlines() if l.strip()]
        metadata_keywords = ("name:", "roll", "date:", "class:", "subject:", "exam")
        substantive = [l for l in lines if not any(k in l.lower() for k in metadata_keywords)]
        if len(substantive) == 0:
            return 0.6

        return 0.95

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_ocr_json(self, raw: str) -> Optional[dict]:
        """
        Parse the structured JSON response from the OCR prompt.
        Strips markdown fences if the model wraps the response.
        Returns None if parsing fails (triggers heuristic fallback).
        """
        import json
        text = raw.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "text" in data:
                return data
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _pdf_to_image_bytes(self, file_bytes: bytes, filename: str) -> bytes:
        """Convert the first page of a PDF to PNG bytes for vision processing."""
        if not filename.lower().endswith(".pdf"):
            return file_bytes
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if len(doc) > 0:
                page = doc[0]
                pix = page.get_pixmap()
                file_bytes = pix.tobytes("png")
            doc.close()
        except ImportError:
            print("[OCR] PyMuPDF not installed — cannot convert PDF to image.")
        except Exception as exc:
            print(f"[OCR] PDF conversion failed: {exc}")
        return file_bytes

    def _run_gemini_ocr(self, file_bytes: bytes) -> Optional[str]:
        """Attempt OCR using Gemini Vision with model fallback."""
        if not self.client:
            return None

        try:
            import PIL.Image
            from google.genai import types

            image = PIL.Image.open(io.BytesIO(file_bytes))

            for model_name in FALLBACK_MODELS:
                print(f"[OCR] Trying model: {model_name}")
                for attempt in range(3):
                    try:
                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=[image, EXTRACT_PROMPT],
                            config=types.GenerateContentConfig(temperature=0.0),
                        )
                        if response and response.text:
                            print(f"[OCR] ✓ Success with {model_name}")
                            return response.text.strip()
                    except Exception as exc:
                        err = str(exc)
                        print(f"[OCR] Attempt {attempt + 1}/3 failed ({model_name}): {err[:120]}")
                        if "429" in err or "RESOURCE_EXHAUSTED" in err:
                            if "limit: 0" in err or "exceeded your current quota" in err.lower():
                                break  # Hard quota — try next model
                            time.sleep(2)  # Transient — backoff and retry
                        else:
                            break  # Non-rate-limit error — try next model

        except Exception as exc:
            print(f"[OCR] Gemini setup error: {exc}")

        return None
