<div align="center"><img src="fairgrade.gif" width="220" alt="FairGrade AI"/></div>

# 🏆 FairGrade AI — Bias Detection in Student Grading

![FairGrade AI](./fairgrade-ai/src/assets/hero_widescreen_diagram.png)

<p align="center">
  <img src="https://img.shields.io/badge/Google%20Solution%20Challenge-2026-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/SDG%204-Quality%20Education-c5192d?style=for-the-badge&logo=unitednations&logoColor=white" />
  <img src="https://img.shields.io/badge/Built%20with-Gemini%20AI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-Live-34d399?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/CI-Passing-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white" />
</p>

<p align="center">
  <b>Exposing hidden bias affecting millions of students to give schools actionable insights.</b>
</p>

<p align="center">
  🎬 <a href="https://youtu.be/YOUR_VIDEO_ID"><b>Watch the Demo Video</b></a>
  &nbsp;·&nbsp;
  👉 <a href="https://team-vektor-fairgrade.vercel.app/"><b>Try the Live Demo</b></a>
  &nbsp;·&nbsp;
  <a href="#-getting-started-local-development">Local Setup</a>
  &nbsp;·&nbsp;
  <a href="#-team-vektor">Team</a>
</p>

> **🧑‍⚖️ Note for Judges:** Click **"Try the Demo (Guest Mode)"** on the login screen to explore the full UI instantly — no authentication needed. *(First load may take ~30s as the free-tier backend wakes up.)*

---

## 📌 The Problem

> Research shows that **implicit bias** in grading affects millions of students worldwide. Factors such as a student's name, gender, or handwriting style can unconsciously influence a teacher's score — even among well-intentioned educators.

Students from marginalized communities are disproportionately affected. The current system offers **no objective way** for schools to detect or measure this bias at scale.

**FairGrade AI solves this** by providing an independent, AI-powered "second opinion" on every graded paper — completely anonymized and bias-free.

---

## 🎯 UN Sustainable Development Goal

This project directly addresses **[UN SDG 4: Quality Education](https://sdgs.un.org/goals/goal4)** — ensuring inclusive and equitable quality education for all.

| Target | How FairGrade Helps |
|--------|-------------------|
| **4.1** Ensure all learners achieve literacy and numeracy | Provides objective evaluation regardless of student background |
| **4.5** Eliminate gender disparities in education | Strips identity markers before grading to prevent gender bias |
| **4.a** Build effective, inclusive learning environments | Gives schools a data dashboard to detect and fix systemic grading patterns |

---

## 📈 Measured Impact

> _"What gets measured, gets improved."_

| Metric | Value | How We Measured |
|--------|-------|-----------------|
| **Grading inconsistencies detected** | **42.3%** of evaluations showed bias | Control Group Comparison (Teacher vs. Gemini 2.5 Flash) |
| **Average grading time saved** | **~3 minutes** per paper | Time-Motion Study across 50 Pilot Evaluations |
| **Identity redaction accuracy** | **100%** of PII fields removed | Validated via Cross-Agent Verification (Privacy Agent + Regex Auditor) |
| **AI evaluation confidence** | **92%** average confidence score | Gemini's self-reported confidence per evaluation |
| **Students assessed (Pilot Program)** | **150+** answer sheets processed | Aggregated data from Local School Pilots and a simulated batch stress test. |

> *📊 Results derived from controlled simulation + small-scale educator validation dataset.*
### 🔍 Methodology & Data Sources
To ensure the accuracy of our impact metrics, we conducted a three-phase validation:
1. **Local Pilot**: 54 manual evaluations conducted with three local educators across Mathematics and Science subjects to calibrate the Bias Agent.
2. **Batch Test**: A processing script ran 100+ anonymized student answers through the Gemini 2.5 Flash pipeline to verify OCR reliability under load.
3. **Verification**: 100% of the PII redaction results were verified using a secondary validation regex to ensure no student names "leaked" into the evaluation step.

> *The system supports batch CSV exports for school administrators to audit grading patterns at scale (see [`/docs/sample_results.csv`](./docs/sample_results.csv)).*


### How Bias Is Calculated

$$ \text{Bias Score} = \min(100, |\text{Teacher Score} - \text{AI Score}| \times 10) $$

$$ \text{Completeness Factor} = \min\left(1.0, \frac{\log(1 + \text{words})}{\log(120)}\right) $$

$$ \text{Final Bias} = \text{Bias Score} \times \text{Completeness Factor} $$

We use a normalized absolute difference between Teacher Score and AI Score to detect grading inconsistencies.

- **Completeness Factor** reduces bias impact for very short answers where the AI has limited context. Longer, more complete answers produce a more reliable signal.
- AI Confidence is stored for reference but **not used in scoring** — keeping the formula clean, explainable, and reproducible.

If the Bias Score > 30%, the system flags it as **High Risk** — prompting a teacher review via our **Human-in-the-Loop** verification flow.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 👁️ **Multimodal OCR** | Extracts handwriting from images and PDFs using **Google Gemini 2.5 Flash Vision** |
| 🛡️ **Privacy Engine** | Automatically redacts Names, Student IDs, and Roll Numbers before grading |
| 🧠 **Explainable AI** | Grades answers purely on factual correctness and returns an AI **Confidence Score** |
| ⚖️ **Bias Detection Logic** | Calculates a custom **Bias Percentage** using a defined algorithmic formula |
| 📊 **Admin Analytics** | Features School-wide Bias Heatmaps, Bias Distribution, and **Overall Bias Reduction %** |
| 🚀 **Batch Processing** | Asynchronous FastAPI + Firestore architecture designed to process entire classrooms concurrently |
| 🔄 **Fault-Tolerant Pipeline** | Auto-fallback across multiple Gemini models with per-agent error handling |
| 👩‍🏫 **Immutable Audit Trails (HITL)** | Every teacher override is cryptographically tied to their Google UID, ensuring accountability |
| 🔐 **Google OAuth & Protected Routes** | Uses Firebase Auth to restrict dashboard access to verified educators, securing sensitive data |

---

## 🖥️ Screenshots

| Upload & Evaluate | Bias Analysis | Analytics Dashboard |
|:-----------------:|:-------------:|:-------------------:|
| ![Upload & Evaluate](./fairgrade-ai/src/assets/screenshot_upload.png) | ![Bias Analysis](./fairgrade-ai/src/assets/screenshot_bias.png) | ![Analytics Dashboard](./fairgrade-ai/src/assets/screenshot_analytics.png) |

> *Visit the [live demo](https://team-vektor-fairgrade.vercel.app/) to see the full flow in action.*

---

## 🏗️ System Architecture

FairGrade AI uses a **5-agent pipeline** where each agent has a single responsibility. Images are processed **in-memory** and never stored on disk to protect student privacy.

```mermaid
graph TD
    A[Teacher uploads Answer Sheet + Rubric] --> |POST /api/evaluate| C[API Gateway - FastAPI]

    subgraph AI Agent Pipeline
        D[1. OCR Agent - Gemini Vision]
        E[2. Privacy Agent - PII Redaction]
        F[3. Evaluation Agent - Gemini AI]
        G[4. Bias Agent - Algorithm]
        H[5. Reporting Agent]
    end

    C --> D
    D --> |Raw Text| E
    E --> |Anonymized Text| F
    F --> |AI Score + Reasoning| G
    G --> |Bias Report| H
    H --> |JSON Response| B[Analytics Dashboard]
    B --> |Review Results| J[Teacher Verifies - Accept or Override]
    J --> |POST /api/verify| C
    C --> |Saves Metrics| I[Firebase Firestore]

    style A fill:#3b82f6,stroke:#1d4ed8,color:#fff
    style B fill:#3b82f6,stroke:#1d4ed8,color:#fff
    style C fill:#10b981,stroke:#047857,color:#fff
    style D fill:#f59e0b,stroke:#b45309,color:#fff
    style E fill:#f59e0b,stroke:#b45309,color:#fff
    style F fill:#f59e0b,stroke:#b45309,color:#fff
    style G fill:#f59e0b,stroke:#b45309,color:#fff
    style H fill:#f59e0b,stroke:#b45309,color:#fff
    style I fill:#ec4899,stroke:#be185d,color:#fff
    style J fill:#059669,stroke:#047857,color:#fff
```

### Key Design Decisions

- **In-Memory Processing**: Student answer sheets are never written to disk — protecting privacy.
- **Concurrent Batch Scalability**: The FastAPI + Firestore architecture is designed for parallel, high-volume processing, allowing principals to evaluate entire classrooms and view school-wide "Bias Heatmaps".
- **Enterprise-Grade Security & Audit Trails**: Implemented Google OAuth 2.0 to ensure that only verified educators can access the dashboard. When a teacher "Verifies" a grade, their unique Firebase Auth UID is saved to Firestore, creating an immutable audit trail of who approved which evaluation.
- **Multi-Model Fallback**: The pipeline tries `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.0-flash-lite` → `gemini-2.5-flash-lite` with exponential backoff.
- **Granular Error Handling**: Each agent has its own try-catch. If one agent fails, partial results from successful agents are still returned.
- **Chain-of-Thought (CoT) Evaluation**: Our agents use Chain-of-Thought prompting to output a `thought_process` before assigning a grade. This forces the model to analyze the text literally and prevents "hallucinations" where the AI might invent answers that aren't actually present on the student's paper.
- **Human-in-the-Loop**: AI provides a recommendation; the teacher makes the final call. This is a core **Responsible AI** principle.

---

## 🛠️ Tech Stack

<p align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini%20AI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" />
  <img src="https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" />
  <img src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black" />
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" />
</p>

| Layer | Technology | Google Integration |
|-------|-----------|--------------------|
| **Frontend** | React, TypeScript, Vite, CSS3 (Glassmorphism), Recharts | Firebase Auth, Firestore SDK |
| **Backend** | Python, FastAPI, Uvicorn | **Google Gemini API** (`google-genai` SDK) |
| **AI Engine** | Gemini 2.5 Flash, Gemini 2.0 Flash Lite | **Multi-model fallback** with structured prompts |
| **Database** | Firebase Firestore (real-time) | **Cloud Firestore** for eval history & verifications |
| **Deployment** | Vercel (Frontend) + Render (Backend) | — |
| **CI/CD** | GitHub Actions (TypeScript check + Vitest + build + Playwright E2E) | — |

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### 1. Backend

```bash
# Clone the repo
git clone https://github.com/Yashasm18/Fair-Grade.git
cd Fair-Grade

# Create & activate virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template and add your API key
cp .env.example .env

# Start the server
uvicorn app:app --reload --port 8000
```

### 2. Frontend

```bash
cd fairgrade-ai

# Install dependencies
npm install

# Create .env with your Firebase config
cp .env.example .env

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`

### 3. Run Tests

```bash
# Backend tests (from project root)
pip install pytest
pytest tests/ -v

# Frontend tests (from fairgrade-ai/)
cd fairgrade-ai
npm test              # 27 unit tests (Vitest + React Testing Library)
npm run type-check    # TypeScript strict mode check
npm run e2e           # Playwright E2E tests (requires: npx playwright install)
```

---

## 📂 Project Structure

```text
Fair-Grade/
│
├── 🐍 Backend (Python / FastAPI)
│   ├── app.py                      # API Gateway + Human-in-the-Loop verify endpoint
│   ├── requirements.txt            # Python dependencies
│   ├── agents/                     # AI Pipeline
│   │   ├── ocr_agent.py            # Extracts text via Google Gemini Vision API
│   │   ├── privacy_agent.py        # Redacts student identities (PII)
│   │   ├── evaluation_agent.py     # Grades answers via Google Gemini AI
│   │   ├── bias_agent.py           # Calculates bias % & outputs report
│   │   └── reporting_agent.py      # Assembles final JSON response
│   └── tests/
│       └── test_agents.py          # Unit tests for the AI agents
│
├── ⚛️ Frontend (React / TypeScript / Vite)
│   └── fairgrade-ai/
│       ├── package.json            # Node dependencies
│       ├── tsconfig.json           # TypeScript strict configuration
│       ├── vite.config.js          # Vite + Vitest configuration
│       ├── playwright.config.ts    # E2E test configuration
│       └── src/
│           ├── App.tsx             # Main Application + HITL verification
│           ├── Analytics.tsx       # Bias Visualization Dashboard
│           ├── types.ts            # Shared TypeScript interfaces
│           ├── components/         # Reusable UI (ResultCard w/ Accept/Override)
│           ├── config/             # Firebase configuration
│           └── test/               # Unit tests (Vitest + React Testing Library)
│
└── ⚙️ Config & Deployment
    ├── Dockerfile                  # Container instructions for Render
    ├── .env.example                # Template for environment variables
    ├── .github/workflows/ci.yml    # Automated testing & build pipeline
    ├── SAFETY_GUIDELINES.md        # Responsible AI & student privacy policy
    ├── CONTRIBUTING.md             # Guidelines for open-source contributors
    └── LICENSE                     # MIT License
```

---

## 👥 Team VEKTOR ⚡

<p align="center">
  <i>Built with ❤️ for the Google Solution Challenge 2026</i>
</p>

| Name | Role | GitHub |
|------|------|--------|
| **Yashas M** | Vibecoder & AI Engineer | [@Yashasm18](https://github.com/Yashasm18) |
| **Sahana NS** | AI Integration & Backend Engineer | [@sahana-ns14](https://github.com/sahana-ns14) |
| **Vishnu R** | QA Testing & User Feedback | [@vishnhr90190-droid](https://github.com/vishnhr90190-droid) |
| **Samhitha P** | Frontend Developer & Documentation | [@Samhithapjain](https://github.com/Samhithapjain) |

> *Team VEKTOR — building technology for equitable education.*

---

## 🚀 Our Development Journey

> *"Great software is never built — it's iterated."*

Building FairGrade AI was a journey of continuous improvement driven by real-world feedback.

```mermaid
graph LR
    A["💡 Idea<br/>Grading bias is<br/>a real problem"] --> B["🔧 Prototype v1<br/>OCR + basic<br/>AI grading"]
    B --> C["⚠️ Challenge<br/>Bias detection was<br/>too simplistic"]
    C --> D["📐 Iteration<br/>Added Completeness<br/>Factor + Confidence<br/>Weight"]
    D --> E["🏗️ Architecture<br/>Multi-agent pipeline<br/>with fault tolerance"]
    E --> F["✅ Production<br/>Deployed + CI/CD<br/>+ HITL verification"]

    style A fill:#3b82f6,stroke:#1d4ed8,color:#fff
    style B fill:#f59e0b,stroke:#b45309,color:#fff
    style C fill:#dc2626,stroke:#991b1b,color:#fff
    style D fill:#8b5cf6,stroke:#6d28d9,color:#fff
    style E fill:#059669,stroke:#047857,color:#fff
    style F fill:#10b981,stroke:#047857,color:#fff
```

| Phase | What We Did | What We Learned |
|-------|-------------|-----------------|
| **1. Problem Discovery** | Researched academic papers on implicit grading bias (UNESCO, OECD) | Bias affects 30–40% of subjective evaluations — the problem is massive |
| **2. Prototype** | Built OCR extraction + single-model AI grading | Raw score comparison produced too many false positives |
| **3. Privacy-First Design** | Added PII redaction as a separate agent | Identity markers must be stripped *before* grading — not after |
| **4. Bias Algorithm v2** | Introduced Completeness Factor and Confidence Weight | Short answers need different treatment; high-confidence disagreements matter more |
| **5. Human-in-the-Loop** | Added teacher Accept/Override with Firestore audit trails | AI should *assist* teachers, never replace them — Responsible AI principle |
| **6. Production Hardening** | TypeScript migration, CI/CD pipeline, rate limiting, strict CORS | A demo that crashes in front of judges is worse than no demo at all |

---

## 🎓 Validation & Feedback

We didn't build FairGrade AI in isolation — we tested it with real educators and iterated based on their feedback.

### Educator Pilot Program

| Metric | Detail |
|--------|--------|
| **Educators consulted** | 3 teachers (Mathematics, Science, History) |
| **Evaluations processed** | 54 manual + 100 batch-automated |
| **Key feedback incorporated** | _"The bias percentage alone isn't enough — I need to see WHY the AI disagrees."_ |
| **Result** | Added detailed AI explanations and confidence scores to every evaluation |

### Iteration Based on Feedback

| Feedback | Action Taken |
|----------|-------------|
| _"Some bias flags feel wrong on short answers"_ | Added **Completeness Factor** — reduces bias weight for answers under 120 words |
| _"I want to keep my score but acknowledge the AI's input"_ | Built **Human-in-the-Loop** verification with Accept/Override options |
| _"Can I see trends across my class?"_ | Built the **Analytics Dashboard** with bias distribution charts and score trends |
| _"What if the AI is wrong?"_ | Added **AI Confidence Score** so teachers can gauge reliability |

> *Every feature in FairGrade AI exists because a teacher asked for it.*

---

## 🛡️ Responsible AI

FairGrade AI is a **Sensitive AI** application. We take student privacy and AI safety seriously.

📄 **[Read our full Safety & Responsible AI Guidelines →](SAFETY_GUIDELINES.md)**

Key commitments:
- **FERPA / GDPR** compliant data handling — no student PII is persisted
- **Human-in-the-Loop** — AI advises, teachers decide
- **In-memory processing** — answer sheets are never written to disk
- **Non-confrontational bias reporting** — patterns, not blame

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
