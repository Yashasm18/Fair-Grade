"""
OCR Agent — Extracts text from uploaded answer sheet images/PDFs.

Google Cloud Technology: Google Gemini Vision API (gemini-2.5-flash)
Uses Gemini Vision multimodal API with automatic fallback across models.
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


FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

EXTRACT_PROMPT = (
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

    def extract_text(self, file_bytes: bytes, filename: str = "") -> str:
        """
        Extract text from image bytes or PDF using Gemini Vision API.

        Args:
            file_bytes: Raw bytes of the uploaded file.
            filename: Original filename (used to detect PDF format).

        Returns:
            Extracted text as a string, or a fallback demo string on failure.
        """
        file_bytes = self._pdf_to_image_bytes(file_bytes, filename)
        return self._run_gemini_ocr(file_bytes) or DEMO_FALLBACK_TEXT

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
