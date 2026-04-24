"""
FairGrade AI — FastAPI Backend (v2.0)
Google Cloud Technologies: Gemini 2.5 Flash (Vision), Gemini 2.0 Flash Lite, Firebase Firestore

Agents:
    1. OCRAgent        → Gemini Vision API text extraction
    2. PrivacyAgent    → PII redaction
    3. EvaluationAgent → Gemini AI grading with structured prompts
    4. BiasAgent       → Algorithmic bias detection
    5. ReportingAgent  → JSON report assembly
"""

import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Gemini client — Google Gemini AI SDK (google-genai)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None

if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[OK] Google Gemini AI client initialized (google-genai SDK).")
    except Exception as exc:
        print(f"[WARN] Gemini init failed: {exc}")
else:
    print("[WARN] GEMINI_API_KEY not set — AI features will use mock responses.")

# ---------------------------------------------------------------------------
# Agent instances
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
    version="2.0.0",
    description="Multi-agent pipeline powered by Google Gemini AI for UN SDG 4.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://team-vektor-fairgrade.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic model for Human-in-the-Loop override
# ---------------------------------------------------------------------------
class TeacherOverride(BaseModel):
    fileName: str
    originalAiScore: float
    originalTeacherScore: float
    finalScore: float
    action: str  # "accept_ai" | "override"
    overrideReason: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    """Liveness probe with Google tech details."""
    return {
        "status": "FairGrade AI backend is running",
        "gemini_ready": gemini_client is not None,
        "google_tech": {
            "ai_model": "Google Gemini 2.5 Flash / 2.0 Flash Lite",
            "sdk": "google-genai",
            "database": "Firebase Firestore",
        },
    }


@app.post("/api/evaluate", tags=["Pipeline"])
async def evaluate_answer(
    file: UploadFile = File(...),
    teacher_score: float = Form(...),
    question_context: str = Form(None),
):
    """
    Full 5-agent pipeline with granular per-agent error handling.
    Returns partial results even if an individual agent fails.
    """
    pipeline_errors = []
    extracted_text = ""
    clean_text = ""
    evaluation = {"score": 0, "explanation": "", "confidence": 0.0}
    bias_info = {"severity": "Unknown", "status": "Unknown", "difference": 0,
                 "bias_score_percentage": 0.0, "formula_used": ""}

    # ── Input Validation ───────────────────────────────────────────────
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif", "application/pdf"}

    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}. Allowed: images and PDFs.")

    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"File read failed: {exc}")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). Maximum allowed: 10 MB.")

    # Agent 1: OCR (Google Gemini Vision API)
    try:
        extracted_text = ocr_agent.extract_text(file_bytes, file.filename)
    except Exception as exc:
        pipeline_errors.append({"agent": "OCR Agent", "error": str(exc)})
        extracted_text = "[OCR FAILED] Unable to extract text."

    # Agent 2: Privacy (Regex PII redaction)
    try:
        clean_text = privacy_agent.anonymize(extracted_text)
    except Exception as exc:
        pipeline_errors.append({"agent": "Privacy Agent", "error": str(exc)})
        clean_text = extracted_text

    # Agent 3: Evaluation (Google Gemini AI)
    try:
        evaluation = evaluation_agent.evaluate(clean_text, question_context)
    except Exception as exc:
        pipeline_errors.append({"agent": "Evaluation Agent", "error": str(exc)})
        evaluation = {"score": 0, "explanation": f"Evaluation failed: {str(exc)[:200]}", "confidence": 0.0}

    # Agent 4: Bias Detection
    try:
        bias_info = bias_agent.detect_bias(
            teacher_score,
            evaluation["score"],
            ai_confidence=evaluation.get("confidence", 1.0),
            answer_length=len(clean_text),
        )
    except Exception as exc:
        pipeline_errors.append({"agent": "Bias Agent", "error": str(exc)})

    # Agent 5: Reporting
    try:
        report = reporting_agent.format_report(
            extracted_text, clean_text, evaluation, bias_info, teacher_score
        )
    except Exception as exc:
        pipeline_errors.append({"agent": "Reporting Agent", "error": str(exc)})
        report = {
            "originalTextLength": len(extracted_text),
            "anonymizedText": clean_text,
            "evaluation": {"aiScore": evaluation["score"], "teacherScore": teacher_score,
                           "explanation": evaluation["explanation"],
                           "confidenceScore": evaluation.get("confidence", 0.0)},
            "bias": {"level": bias_info.get("severity", "Unknown"),
                     "status": bias_info.get("status", "Unknown"),
                     "gap": bias_info.get("difference", 0),
                     "biasScorePercentage": bias_info.get("bias_score_percentage", 0.0),
                     "formulaUsed": bias_info.get("formula_used", "")},
        }

    if pipeline_errors:
        report["pipelineWarnings"] = pipeline_errors
    report["verified"] = False
    return report


@app.post("/api/verify", tags=["Human-in-the-Loop"])
async def verify_evaluation(override: TeacherOverride):
    """
    Responsible AI: Teacher accepts or overrides the AI grade.
    AI assists humans — humans make the final decision.
    """
    try:
        if override.action not in ("accept_ai", "override"):
            raise HTTPException(status_code=400, detail="Action must be 'accept_ai' or 'override'.")

        verified_bias = bias_agent.detect_bias(override.originalTeacherScore, override.finalScore)
        return {
            "fileName": override.fileName,
            "originalAiScore": override.originalAiScore,
            "originalTeacherScore": override.originalTeacherScore,
            "finalScore": override.finalScore,
            "action": override.action,
            "verified": True,
            "overrideReason": override.overrideReason,
            "verifiedBias": {
                "level": verified_bias["severity"],
                "status": verified_bias["status"],
                "gap": verified_bias["difference"],
                "biasScorePercentage": verified_bias.get("bias_score_percentage", 0.0),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {exc}")


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
