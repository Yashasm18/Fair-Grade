"""
Evaluation Agent — Grades anonymized student answers using Google Gemini AI.

Google Cloud Technology: Google Gemini API (google-genai SDK)
Primary model: gemini-2.5-pro (best reasoning for nuanced rubric scoring).
Fallback chain: gemini-2.5-flash → gemini-2.0-flash → gemini-2.0-flash-lite.
Supports per-question weight multipliers for a realistic weighted rubric.
"""

import json
import re
import time
from typing import Optional, Union

# gemini-2.5-pro is the primary model: best at following rubric instructions.
# Falls back to flash models if Pro quota is exhausted on the free tier.
FALLBACK_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",  # gemini-2.5-flash-lite removed: unverified model name
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


def _build_prompt(text: str, question_context: Optional[str], question_weight: float = 1.0) -> str:
    # Effective total marks available after weight adjustment
    weight_note = (
        f"\nWEIGHT: This question is worth {question_weight:.1f}x. "
        f"Your raw score (0–10) will be multiplied by {question_weight:.1f} by the system — "
        "grade as normal on the 0–10 scale; the weighting is applied externally."
        if question_weight != 1.0 else ""
    )
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
Note: Use decimals (e.g., 4.5, 7.5) for nuanced scoring.{weight_note}

WEIGHTED RUBRIC GUIDANCE:
- Consider the cognitive demand implied by the question context.
- Higher-weight questions typically require deeper analysis or multi-step reasoning.
- Apply stricter partial-credit logic proportional to the question complexity.

<QUESTION_AND_CONTEXT>
{question_context if question_context else "No specific context provided. Grade based on general factual correctness."}
</QUESTION_AND_CONTEXT>

<STUDENT_ANSWER>
{text}
</STUDENT_ANSWER>

Respond in valid JSON with exactly five keys in this specific order:
- "thought_process": Write 1-2 sentences analyzing what is literally written inside the <STUDENT_ANSWER> tags. Does it contain a real answer, or just the question/junk?
- "score": a number from 0 to 10
- "explanation": a concise explanation to show the teacher. If the answer is just dates/junk/repeating the question, state that clearly.
- "confidence": a number from 0.0 to 1.0
- "bias_indicators": an array of short strings (max 3) listing specific phrases or omissions that most influenced the score, to support bias explainability. E.g. ["Missing: definition of ATP", "Correct: electron transport chain named", "Vague: 'produces energy' without mechanism"]
"""


class EvaluationAgent:
    """Agent 3 — AI-powered grader that evaluates anonymized student answers."""

    def __init__(self, gemini_client=None):
        self.client = gemini_client

    def evaluate(
        self,
        text: str,
        question_context: Optional[str] = None,
        question_weight: float = 1.0,
    ) -> dict:
        """
        Grade the anonymized student answer out of 10, with optional weight multiplier.

        Args:
            text: Anonymized student answer text.
            question_context: Optional rubric / expected answer from the teacher.
            question_weight: Multiplier applied to the raw score (e.g. 2.0 for a
                double-weighted question). Must be between 0.1 and 5.0. The raw
                AI score is always 0–10; the weighted score is returned separately
                so the UI can display both values.

        Returns:
            dict with keys:
                - 'score': raw AI score (0–10, float)
                - 'weighted_score': score × weight, capped at 10 (float)
                - 'question_weight': the weight applied (float)
                - 'explanation': AI reasoning string
                - 'confidence': self-reported confidence (0.0–1.0)
                - 'bias_indicators': list of strings explaining the scoring decision
        """
        question_weight = max(0.1, min(5.0, float(question_weight)))  # clamp
        if not self.client:
            return {
                "score": 8,
                "weighted_score": min(10.0, 8 * question_weight),
                "question_weight": question_weight,
                "explanation": "Mocked score — Gemini API key is not configured.",
                "confidence": 0.0,
                "bias_indicators": [],
            }

        prompt = _build_prompt(text, question_context, question_weight)
        return self._run_with_fallback(prompt, question_weight)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_with_fallback(self, prompt: str, question_weight: float = 1.0) -> dict:
        from google.genai import types

        last_error = None

        for model_name in FALLBACK_MODELS:
            print(f"[EVAL] Trying model: {model_name}")
            result = self._try_model(model_name, prompt, types, question_weight)
            if isinstance(result, dict):
                return result
            last_error = result  # result is the exception on failure

        return {
            "score": 0,
            "weighted_score": 0.0,
            "question_weight": question_weight,
            "explanation": (
                "QUOTA_EXHAUSTED: All Gemini model quotas have been exhausted on the free tier. "
                "Please wait for the quota to reset (~24 hours) or enable billing at "
                "https://aistudio.google.com/api-keys."
            ),
            "confidence": 0.0,
            "bias_indicators": [],
        }

    def _try_model(self, model_name: str, prompt: str, types, question_weight: float = 1.0) -> Union[dict, Exception]:
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
                raw_score = float(data.get("score", 0))
                weighted = round(min(10.0, raw_score * question_weight), 2)
                print(f"[EVAL] ✓ Success with {model_name} | score={raw_score} weight={question_weight} weighted={weighted}")
                return {
                    "score": raw_score,
                    "weighted_score": weighted,
                    "question_weight": question_weight,
                    "explanation": data.get("explanation", ""),
                    "confidence": data.get("confidence", 1.0),
                    "bias_indicators": data.get("bias_indicators", []),
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
