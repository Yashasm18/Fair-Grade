import os
import json
import re
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# ---------------------------------------------------------------------------
# Gemini Setup (new google-genai SDK)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None

if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[OK] Gemini client initialized.")
    except Exception as e:
        print(f"[WARN] Gemini init failed: {e}")

# ---------------------------------------------------------------------------
# Vision Setup (lazy import to avoid namespace conflicts)
# ---------------------------------------------------------------------------
vision_client = None
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if cred_path and os.path.exists(cred_path):
    try:
        import google.cloud.vision as vision_module
        vision_client = vision_module.ImageAnnotatorClient()
        print("[OK] Google Vision client initialized.")
    except Exception as e:
        print(f"[WARN] Vision init failed: {e}")
else:
    print("[WARN] Vision credentials not found - OCR will use fallback demo text.")

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(title="FairGrade AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Agent Classes
# ---------------------------------------------------------------------------

class OCRAgent:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str = "") -> str:
        """Extract text from image bytes or PDF using Gemini API."""
        if filename.lower().endswith('.pdf'):
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap()
                    file_bytes = pix.tobytes("png")
                doc.close()
            except ImportError:
                print("[WARN] PyMuPDF (fitz) not installed, cannot process PDF.")
            except Exception as e:
                print(f"[WARN] Failed to process PDF: {e}")
        
        if gemini_client:
            try:
                import PIL.Image
                import io
                image = PIL.Image.open(io.BytesIO(file_bytes))
                
                prompt = "Extract all the handwritten and printed text from this image exactly as written. Preserve the original formatting and line breaks as much as possible. Do not add any extra commentary, introductory text, or markdown formatting."
                
                fallback_models = [
                    "gemini-2.5-flash",
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                    "gemini-2.5-flash-lite",
                ]
                
                for model_name in fallback_models:
                    print(f"[OCR] Trying model: {model_name}")
                    for attempt in range(3):
                        try:
                            from google.genai import types
                            response = gemini_client.models.generate_content(
                                model=model_name,
                                contents=[image, prompt],
                                config=types.GenerateContentConfig(temperature=0.0)
                            )
                            if response and response.text:
                                print(f"[OCR] Success with model: {model_name}")
                                return response.text.strip()
                        except Exception as e:
                            err_str = str(e)
                            print(f"[OCR] Attempt {attempt+1} failed with {model_name}: {err_str[:120]}")
                            # If it's a quota issue or 503, maybe wait or break
                            if "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                                if "limit: 0" in err_str.lower() or "exceeded your current quota" in err_str.lower():
                                    break # Quota exhausted, try next model
                                import time
                                time.sleep(2) # transient error, backoff
                            else:
                                break # Other error, try next model
                    else:
                        continue # Retries exhausted, try next model
            except Exception as e:
                print(f"[WARN] Gemini OCR Setup Failed: {e}")

        # Fallback demo text if even Gemini fails
        return (
            "Name: [REDACTED]\nRoll No: 12345\n\n"
            "The student answer could not be extracted by the OCR."
        )


class PrivacyAgent:
    @staticmethod
    def anonymize(text: str) -> str:
        """Remove identity identifiers to prevent grader bias."""
        clean_text = text
        patterns = [
            r'(?i)(Name\s*[:\-]?\s*)([^\n]+)',
            r'(?i)(Roll\s*No[\.:]?\s*[:\-]?\s*)([^\n]+)',
            r'(?i)(ID\s*Number\s*[:\-]?\s*)([^\n]+)',
            r'(?i)(Student\s*ID\s*[:\-]?\s*)([^\n]+)',
            r'(?i)(Batch\s*[:\-]?\s*)([^\n]+)',
        ]
        for pattern in patterns:
            def replace_with_redacted(match):
                return match.group(1) + "[REDACTED]"
            clean_text = re.sub(pattern, replace_with_redacted, clean_text)
        return clean_text


class EvaluationAgent:
    @staticmethod
    def _is_quota_exhausted(err_str: str) -> bool:
        """Check if error indicates daily quota is fully exhausted (limit: 0)."""
        return "limit: 0" in err_str or "exceeded your current quota" in err_str.lower()

    @staticmethod
    def _extract_retry_delay(err_str: str):
        """Extract suggested retry delay from API error response."""
        match = re.search(r'retryDelay.*?(\d+\.?\d*)s', err_str)
        if match:
            return float(match.group(1))
        match = re.search(r'retry in (\d+\.?\d*)s', err_str, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    # Models to try in order — each has its own separate free tier quota
    FALLBACK_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-lite",
    ]

    @staticmethod
    def evaluate(text: str, question_context: str = None) -> dict:
        """Evaluate student answer out of 10 using Gemini with model fallback."""
        if not gemini_client:
            return {"score": 8, "explanation": "Mocked score — Gemini API key is not configured."}

        try:
            from google import genai
            context_prompt = f"QUESTION AND EXPECTED ANSWER CONTEXT:\n{question_context}\n\n" if question_context else ""
            use_context_blurb = "Use the provided question and model answer context as the source of truth." if question_context else ""

            prompt = f"""
You are an objective AI grader. Grade the following student answer. {use_context_blurb}

CRITICAL INSTRUCTIONS:
- Completely ignore grammar, handwriting, formatting, or language style.
- Focus ONLY on factual correctness and grasp of concepts.
- Evaluate out of 10 maximum points.

{context_prompt}STUDENT ANSWER:
{text}

Respond in valid JSON with exactly two keys:
- "score": a number from 0 to 10
- "explanation": a concise explanation based on factual correctness only
"""
            # Try each model — if one's quota is exhausted, fall back to the next
            all_exhausted = True
            last_error = None

            for model_name in EvaluationAgent.FALLBACK_MODELS:
                print(f"[EVAL] Trying model: {model_name}")

                # Retry with exponential backoff for transient rate-limit errors
                max_retries = 3
                base_delay = 5  # seconds

                for attempt in range(max_retries):
                    try:
                        from google.genai import types
                        response = gemini_client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.0,
                                response_mime_type="application/json"
                            )
                        )
                        result_text = response.text

                        # Strip markdown code fences if present
                        match = re.search(r"```(?:json)?\n?([\s\S]*?)```", result_text)
                        if match:
                            result_text = match.group(1).strip()

                        data = json.loads(result_text)
                        print(f"[EVAL] Success with model: {model_name}")
                        return {"score": data.get("score", 0), "explanation": data.get("explanation", "")}
                    except Exception as api_err:
                        last_error = api_err
                        err_str = str(api_err)

                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            # Daily quota exhausted for this model — try next model
                            if EvaluationAgent._is_quota_exhausted(err_str):
                                print(f"[QUOTA EXHAUSTED] {model_name} free tier quota is 0. Trying next model...")
                                break  # Break retry loop, try next model
                            else:
                                # Transient per-minute rate limit — retry with backoff
                                all_exhausted = False
                                suggested_delay = EvaluationAgent._extract_retry_delay(err_str)
                                wait_time = suggested_delay if suggested_delay else base_delay * (2 ** attempt)
                                print(f"[RATE LIMIT] {model_name} attempt {attempt + 1}/{max_retries}. Retrying in {wait_time:.0f}s...")
                                time.sleep(wait_time)
                        else:
                            # Non-rate-limit error — try next model
                            print(f"[ERROR] {model_name} failed: {err_str[:120]}")
                            break
                else:
                    # All retries exhausted for this model (transient rate limits)
                    continue
                # break from retry loop hit — try next model
                continue

            # All models exhausted
            if all_exhausted:
                return {
                    "score": 0,
                    "explanation": (
                        "QUOTA_EXHAUSTED: All Gemini model quotas (gemini-2.0-flash, "
                        "gemini-2.0-flash-lite, gemini-1.5-flash) have been exhausted on the free tier. "
                        "Please wait for the quota to reset (usually resets every 24 hours), or "
                        "link billing to your API key project at https://aistudio.google.com/api-keys."
                    )
                }

            return {"score": 0, "explanation": f"Evaluation failed after trying all models: {last_error}"}
        except Exception as e:
            return {"score": 0, "explanation": f"Evaluation failed: {e}"}


class BiasAgent:
    @staticmethod
    def detect_bias(teacher_mark: float, ai_mark: float) -> dict:
        """Detect grading inconsistencies between teacher and AI scores."""
        diff = abs(teacher_mark - ai_mark)

        severity = "High" if diff > 3 else ("Medium" if diff > 1 else "Low")

        if teacher_mark < ai_mark - 1:
            status = "Undergraded"
        elif teacher_mark > ai_mark + 1:
            status = "Overgraded"
        else:
            status = "Fair"

        return {"severity": severity, "status": status, "difference": diff}


class ReportingAgent:
    @staticmethod
    def format_report(
        extracted_text: str,
        clean_text: str,
        evaluation: dict,
        bias_info: dict,
        teacher_score: float,
    ) -> dict:
        return {
            "originalTextLength": len(extracted_text),
            "anonymizedText": clean_text,
            "evaluation": {
                "aiScore": evaluation["score"],
                "teacherScore": teacher_score,
                "explanation": evaluation["explanation"],
            },
            "bias": {
                "level": bias_info["severity"],
                "status": bias_info["status"],
                "gap": bias_info["difference"],
            },
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def health_check():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FairGrade AI — Backend API</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Inter', sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                color: #fff;
                overflow: hidden;
            }
            .container {
                text-align: center;
                padding: 3rem 2rem;
                max-width: 600px;
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.4);
                padding: 8px 20px;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 600;
                color: #34d399;
                margin-bottom: 2rem;
                animation: pulse-glow 2s ease-in-out infinite;
            }
            .status-dot {
                width: 10px; height: 10px;
                background: #34d399;
                border-radius: 50%;
                animation: pulse 1.5s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.5; transform: scale(1.3); }
            }
            @keyframes pulse-glow {
                0%, 100% { box-shadow: 0 0 10px rgba(16, 185, 129, 0.1); }
                50% { box-shadow: 0 0 25px rgba(16, 185, 129, 0.25); }
            }
            h1 {
                font-size: 2.8rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #a78bfa, #818cf8, #6366f1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                font-size: 1rem;
                color: rgba(255,255,255,0.5);
                margin-bottom: 2.5rem;
            }
            .card {
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 2rem;
                margin-bottom: 2rem;
            }
            .endpoints { text-align: left; }
            .endpoint {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 0;
                border-bottom: 1px solid rgba(255,255,255,0.06);
            }
            .endpoint:last-child { border-bottom: none; }
            .method {
                font-size: 0.7rem;
                font-weight: 700;
                padding: 4px 10px;
                border-radius: 6px;
                min-width: 50px;
                text-align: center;
            }
            .method.get { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
            .method.post { background: rgba(16, 185, 129, 0.2); color: #34d399; }
            .path { font-family: 'Courier New', monospace; font-size: 0.9rem; color: #e2e8f0; }
            .desc { font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-left: auto; }
            .tech-stack {
                display: flex;
                gap: 10px;
                justify-content: center;
                flex-wrap: wrap;
                margin-bottom: 1.5rem;
            }
            .tech-tag {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.1);
                padding: 6px 14px;
                border-radius: 8px;
                font-size: 0.75rem;
                color: rgba(255,255,255,0.6);
            }
            .footer {
                font-size: 0.8rem;
                color: rgba(255,255,255,0.3);
            }
            .footer a { color: #818cf8; text-decoration: none; }
            .footer a:hover { text-decoration: underline; }
            .bg-orb {
                position: fixed;
                border-radius: 50%;
                filter: blur(100px);
                opacity: 0.15;
                z-index: -1;
            }
            .orb1 { width: 400px; height: 400px; background: #6366f1; top: -100px; right: -100px; }
            .orb2 { width: 300px; height: 300px; background: #ec4899; bottom: -80px; left: -80px; }
        </style>
    </head>
    <body>
        <div class="bg-orb orb1"></div>
        <div class="bg-orb orb2"></div>
        <div class="container">
            <div class="status-badge">
                <div class="status-dot"></div>
                All Systems Operational
            </div>
            <h1>FairGrade AI</h1>
            <p class="subtitle">Backend API Server &mdash; Google Solution Challenge 2026</p>

            <div class="card endpoints">
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <span class="path">/</span>
                    <span class="desc">Health check</span>
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <span class="path">/api/evaluate</span>
                    <span class="desc">Full AI pipeline</span>
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <span class="path">/analyze</span>
                    <span class="desc">Quick OCR + analysis</span>
                </div>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <span class="path">/docs</span>
                    <span class="desc">Interactive API docs</span>
                </div>
            </div>

            <div class="tech-stack">
                <span class="tech-tag">Python</span>
                <span class="tech-tag">FastAPI</span>
                <span class="tech-tag">Gemini 2.5</span>
                <span class="tech-tag">Multi-Agent AI</span>
            </div>

            <p class="footer">
                Team VEKTOR ⚡ &mdash; <a href="https://github.com/Yashasm18/Fair-Grade" target="_blank">View Source on GitHub</a>
            </p>
        </div>
    </body>
    </html>
    """


@app.post("/api/evaluate")
async def evaluate_answer(
    file: UploadFile = File(...),
    teacher_score: float = Form(...),
    question_context: str = Form(None),
):
    """Full 5-agent pipeline: OCR → Privacy → Evaluate → Bias → Report."""
    try:
        file_bytes = await file.read()
        extracted_text = OCRAgent.extract_text(file_bytes, file.filename)
        clean_text = PrivacyAgent.anonymize(extracted_text)
        evaluation = EvaluationAgent.evaluate(clean_text, question_context)
        bias_info = BiasAgent.detect_bias(teacher_score, evaluation["score"])
        report = ReportingAgent.format_report(
            extracted_text, clean_text, evaluation, bias_info, teacher_score
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """Lightweight endpoint: OCR + Gemini analysis only."""
    try:
        content = await file.read()
        extracted_text = OCRAgent.extract_text(content, file.filename)

        if not gemini_client:
            return {"text": extracted_text, "analysis": "Gemini API key not configured."}

        from google import genai
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Evaluate this student answer and suggest a mark out of 10:\n{extracted_text}",
        )
        return {"text": extracted_text, "analysis": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
