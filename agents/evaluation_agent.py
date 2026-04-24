"""
Evaluation Agent — Grades anonymized student answers using Google Gemini AI.

Google Cloud Technology: Google Gemini API (google-genai SDK)
Models: gemini-2.5-flash, gemini-2.0-flash, gemini-2.0-flash-lite, gemini-2.5-flash-lite
Evaluates factual correctness against the teacher's rubric/context.
Implements multi-model fallback with exponential backoff to handle
free-tier quota limits gracefully.
"""

import json
import re
import time
from typing import Optional, Union

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
]

_BASE_RETRY_DELAY = 5  # seconds
_MAX_RETRIES = 3


def _is_quota_exhausted(err: str) -> bool:
    return "limit: 0" in err or "exceeded your current quota" in err.lower()


def _extract_retry_delay(err: str) -> Optional[float]:
    match = re.search(r"retryDelay.*?(\d+\.?\d*)s", err)
    if match:
        return float(match.group(1))
    match = re.search(r"retry in (\d+\.?\d*)s", err, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _build_prompt(text: str, question_context: Optional[str]) -> str:
    context_block = (
        f"QUESTION AND EXPECTED ANSWER CONTEXT:\n{question_context}\n\n"
        if question_context
        else ""
    )
    context_instruction = (
        "Use the provided question and model answer context as the source of truth."
        if question_context
        else ""
    )
    return f"""You are an expert, objective AI grader. Grade the following student answer. {context_instruction}

CRITICAL INSTRUCTIONS:
- Completely ignore grammar, handwriting, formatting, or language style.
- Focus ONLY on factual correctness and depth of understanding.
- You MUST use the FULL scoring range. DO NOT default to 0 or 10.
- Use half-point increments (e.g., 3.5, 6.5, 7.5) when appropriate.
- STRICT RULE: If the text is just metadata (dates, names, "Question and answer"), a cover page, irrelevant, or does not contain an actual attempt to answer the question, you MUST score it exactly 0.

SCORING RUBRIC (you MUST follow this):
  10:   Perfect — Flawless, deep understanding, no missing details. (RARE)
  8-9:  Excellent — Mostly correct with very minor gaps.
  5-7:  Adequate — Partially correct, demonstrates basic understanding but misses key points.
  2-4:  Below Average — Significant gaps, barely touches on the correct topic.
  1:    Poor — Completely incorrect attempt at an answer.
  0:    No Answer — Blank, strictly metadata (dates/headers), off-topic, or gibberish.

IMPORTANT: A score of exactly 10 should be extremely RARE and reserved only for perfect, comprehensive answers. Evaluate genuinely.

{context_block}STUDENT ANSWER:
{text}

Respond in valid JSON with exactly three keys:
- "score": a number from 0 to 10 (use decimals like 6.5, 7.5 for nuance)
- "explanation": a concise explanation referencing specific parts of the answer
- "confidence": a number from 0.0 to 1.0 representing your confidence in this evaluation
"""


class EvaluationAgent:
    """Agent 3 — AI-powered grader that evaluates anonymized student answers."""

    def __init__(self, gemini_client=None):
        self.client = gemini_client

    def evaluate(self, text: str, question_context: Optional[str] = None) -> dict:
        """
        Grade the anonymized student answer out of 10.

        Args:
            text: Anonymized student answer text.
            question_context: Optional rubric / expected answer from the teacher.

        Returns:
            dict with keys 'score' (int), 'explanation' (str), and 'confidence' (float).
        """
        if not self.client:
            return {"score": 8, "explanation": "Mocked score — Gemini API key is not configured.", "confidence": 0.0}

        prompt = _build_prompt(text, question_context)
        return self._run_with_fallback(prompt)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_with_fallback(self, prompt: str) -> dict:
        from google.genai import types

        last_error = None

        for model_name in FALLBACK_MODELS:
            print(f"[EVAL] Trying model: {model_name}")
            result = self._try_model(model_name, prompt, types)
            if isinstance(result, dict):
                return result
            last_error = result  # result is the exception on failure

        return {
            "score": 0,
            "explanation": (
                "QUOTA_EXHAUSTED: All Gemini model quotas have been exhausted on the free tier. "
                "Please wait for the quota to reset (~24 hours) or enable billing at "
                "https://aistudio.google.com/api-keys."
            ),
            "confidence": 0.0,
        }

    def _try_model(self, model_name: str, prompt: str, types) -> Union[dict, Exception]:
        """Attempt generation on a single model with retry backoff. Returns dict on success."""
        for attempt in range(_MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                    ),
                )
                result_text = response.text

                # Strip markdown code fences if present
                fence = re.search(r"```(?:json)?\n?([\s\S]*?)```", result_text)
                if fence:
                    result_text = fence.group(1).strip()

                data = json.loads(result_text)
                print(f"[EVAL] ✓ Success with {model_name}")
                return {
                    "score": data.get("score", 0), 
                    "explanation": data.get("explanation", ""),
                    "confidence": data.get("confidence", 1.0)
                }

            except Exception as exc:
                err = str(exc)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    if _is_quota_exhausted(err):
                        print(f"[EVAL] Quota exhausted for {model_name} — trying next model.")
                        return exc  # Signal to try next model
                    delay = _extract_retry_delay(err) or _BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"[EVAL] Rate limit on {model_name}, retrying in {delay:.0f}s...")
                    time.sleep(delay)
                else:
                    print(f"[EVAL] {model_name} error: {err[:120]} — trying next model.")
                    return exc  # Non-retryable, try next model

        return Exception(f"Max retries exceeded for {model_name}")
