"""
FairGrade AI — FastAPI Backend
Entry point: orchestrates the 5-agent pipeline.

Agents live in agents/ — each with a single responsibility:
    1. OCRAgent        → extracts text from uploaded image/PDF
    2. PrivacyAgent    → anonymizes student identity fields
    3. EvaluationAgent → AI grading via Gemini (with model fallback)
    4. BiasAgent       → compares AI score vs. teacher score
    5. ReportingAgent  → formats the final JSON response
"""

import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Gemini client (shared across agents)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None

if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[OK] Gemini client initialized.")
    except Exception as exc:
        print(f"[WARN] Gemini init failed: {exc}")
else:
    print("[WARN] GEMINI_API_KEY not set — AI features will use mock responses.")

# ---------------------------------------------------------------------------
# Agent instances (dependency injection via constructor)
# ---------------------------------------------------------------------------
from agents import OCRAgent, PrivacyAgent, EvaluationAgent, BiasAgent, ReportingAgent

ocr_agent = OCRAgent(gemini_client=gemini_client)
privacy_agent = PrivacyAgent()
evaluation_agent = EvaluationAgent(gemini_client=gemini_client)
bias_agent = BiasAgent()
reporting_agent = ReportingAgent()

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FairGrade AI Backend",
    version="1.0.0",
    description=(
        "Multi-agent pipeline for bias-free student answer evaluation. "
        "Powered by Google Gemini AI."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    """Liveness probe — confirms the backend is running."""
    return {
        "status": "FairGrade AI backend is running",
        "gemini_ready": gemini_client is not None,
    }


@app.post("/api/evaluate", tags=["Pipeline"])
async def evaluate_answer(
    file: UploadFile = File(...),
    teacher_score: float = Form(...),
    question_context: str = Form(None),
):
    """
    Full 5-agent pipeline: OCR → Privacy → Evaluate → Bias → Report.

    - **file**: Uploaded answer sheet (JPEG, PNG, or PDF).
    - **teacher_score**: Human-assigned mark (0–10).
    - **question_context**: Optional rubric / expected answer for evaluation.
    """
    try:
        file_bytes = await file.read()

        # Agent Pipeline
        extracted_text = ocr_agent.extract_text(file_bytes, file.filename)
        clean_text = privacy_agent.anonymize(extracted_text)
        evaluation = evaluation_agent.evaluate(clean_text, question_context)
        bias_info = bias_agent.detect_bias(teacher_score, evaluation["score"])
        report = reporting_agent.format_report(
            extracted_text, clean_text, evaluation, bias_info, teacher_score
        )
        return report

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/analyze", tags=["Lightweight"])
async def analyze(file: UploadFile = File(...)):
    """Lightweight endpoint: OCR + quick Gemini analysis only (no bias detection)."""
    try:
        content = await file.read()
        extracted_text = ocr_agent.extract_text(content, file.filename)

        if not gemini_client:
            return {"text": extracted_text, "analysis": "Gemini API key not configured."}

        from google import genai
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Evaluate this student answer and suggest a mark out of 10:\n{extracted_text}",
        )
        return {"text": extracted_text, "analysis": response.text}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
