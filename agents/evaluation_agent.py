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
    return f"""You are an expert, strict AI grader evaluating a student's handwritten answer that has been extracted via OCR.

CRITICAL ANTI-HALLUCINATION INSTRUCTIONS:
1. You are evaluating ONLY the text inside the <STUDENT_ANSWER> tags.
2. DO NOT grade the context or the question itself.
3. DO NOT hallucinate, invent, or assume facts. If the <STUDENT_ANSWER> does not explicitly contain the correct information, you MUST score it a 0.
4. If the <STUDENT_ANSWER> is just metadata (dates, names, "papergrid"), gibberish, or simply repeats the question, you MUST score it a 0.
5. Completely ignore grammar, handwriting, and formatting.

GRADING RUBRIC (0 to 10):
- 10: Flawless, deep understanding. (EXTREMELY RARE)
- 8-9: Mostly correct, minor gaps.
- 5-7: Partially correct, basic understanding.
- 2-4: Significant gaps.
- 1: Completely incorrect attempt.
- 0: Strictly metadata, off-topic, gibberish, or empty. 
Note: Use decimals (e.g., 4.5, 7.5) for nuanced scoring.

<QUESTION_AND_CONTEXT>
{question_context if question_context else "No specific context provided. Grade based on general factual correctness."}
</QUESTION_AND_CONTEXT>

<STUDENT_ANSWER>
{text}
</STUDENT_ANSWER>

Respond in valid JSON with exactly four keys in this specific order:
- "thought_process": Write 1-2 sentences analyzing what is literally written inside the <STUDENT_ANSWER> tags. Does it contain a real answer, or just the question/junk?
- "score": a number from 0 to 10
- "explanation": a concise explanation to show the teacher. If the answer is just dates/junk/repeating the question, state that clearly.
- "confidence": a number from 0.0 to 1.0
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
                    "explanation": f"[v2.1-CoT] {data.get('explanation', '')}",
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
