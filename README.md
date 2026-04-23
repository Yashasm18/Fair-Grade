# 🏆 FairGrade AI — Bias Detection in Student Grading

![FairGrade AI](./fairgrade-ai/src/assets/hero.png)

<p align="center">
  <img src="https://img.shields.io/badge/Google%20Solution%20Challenge-2026-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/SDG%204-Quality%20Education-c5192d?style=for-the-badge&logo=unitednations&logoColor=white" />
  <img src="https://img.shields.io/badge/Built%20with-Gemini%20AI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-Live-34d399?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/CI-Passing-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white" />
</p>

<p align="center">
  <b>An intelligent, multi-agent evaluation platform that detects and mitigates systemic bias in student grading.</b>
</p>

<p align="center">
  👉 <a href="https://team-vektor-fairgrade.vercel.app/"><b>Try the Live Demo</b></a>
  &nbsp;·&nbsp;
  <a href="#-getting-started-local-development">Local Setup</a>
  &nbsp;·&nbsp;
  <a href="#-team-vektor">Team</a>
</p>

> **⚠️ Cold Start Notice:** The backend is hosted on Render's free tier, which spins down after 15 minutes of inactivity. If the demo feels slow on first load, please allow ~30 seconds for the backend to wake up before trying again.

---

## 📌 The Problem

> Research shows that **implicit bias** in grading affects millions of students worldwide. Factors such as a student's name, gender, or handwriting style can unconsciously influence a teacher's score — even among well-intentioned educators.

Students from marginalized communities are disproportionately affected. The current system offers **no objective way** for schools to detect or measure this bias at scale.

**FairGrade AI solves this** by providing an independent, AI-powered "second opinion" on every graded paper — completely anonymized and bias-free.

---

## 🎯 UN Sustainable Development Goal

This project directly addresses **[SDG 4: Quality Education](https://sdgs.un.org/goals/goal4)** — ensuring inclusive and equitable quality education for all.

| Target | How FairGrade Helps |
|--------|-------------------|
| **4.1** Ensure all learners achieve literacy and numeracy | Provides objective evaluation regardless of student background |
| **4.5** Eliminate gender disparities in education | Strips identity markers before grading to prevent gender bias |
| **4.a** Build effective, inclusive learning environments | Gives schools a data dashboard to detect and fix systemic grading patterns |

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 👁️ **Multimodal OCR** | Extracts handwriting from images and PDFs using Gemini 2.5 Flash Vision |
| 🛡️ **Privacy Engine** | Automatically redacts Names, Student IDs, and Roll Numbers before grading |
| 🧠 **AI Evaluation** | Grades answers based purely on factual correctness against a rubric |
| ⚖️ **Bias Detection** | Compares AI score vs. Teacher score and flags *Undergraded*, *Overgraded*, or *Fair* |
| 📊 **Analytics Dashboard** | Aggregates all results into interactive charts to spot systemic classroom bias |
| 🔄 **Fault-Tolerant Pipeline** | Auto-fallback across multiple Gemini models to ensure 100% uptime |

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
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef agents fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef database fill:#ec4899,stroke:#be185d,stroke-width:2px,color:#fff;

    subgraph "React Frontend"
        A["Teacher uploads Answer Sheet + Rubric"]:::frontend
        B["Analytics Dashboard"]:::frontend
    end

    subgraph "FastAPI Backend"
        C["API Gateway"]:::backend

        subgraph "AI Agent Pipeline"
            D["1. OCR Agent"]:::agents
            E["2. Privacy Agent"]:::agents
            F["3. Evaluation Agent"]:::agents
            G["4. Bias Agent"]:::agents
            H["5. Reporting Agent"]:::agents
        end
    end

    I[("Firebase Firestore")]:::database

    A -- "POST /api/evaluate" --> C
    C --> D
    D -- "Raw Text" --> E
    E -- "Anonymized Text" --> F
    F -- "AI Score + Reasoning" --> G
    G -- "Bias Classification" --> H
    H -- "Final Report JSON" --> C
    C -- "JSON Response" --> B
    B -- "Saves Metrics" --> I
```

---

## 🛠️ Tech Stack

<p align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini%20AI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" />
  <img src="https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" />
  <img src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black" />
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" />
</p>

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, Vite, CSS3 (Glassmorphism), Recharts |
| **Backend** | Python, FastAPI, Uvicorn |
| **AI Engine** | Google Gemini 2.5 Flash, Gemini 2.0 Flash Lite (with automatic fallback) |
| **Database** | Firebase Firestore (real-time) |
| **Deployment** | Vercel (Frontend) + Render (Backend) |
| **CI/CD** | GitHub Actions (lint + test + build on every push) |

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
# From the project root
pip install pytest
pytest tests/ -v
```

---

## 📂 Project Structure

```
Fair-Grade/
├── app.py                      # FastAPI entry point (orchestrates agents)
├── agents/                     # 5-agent pipeline (one responsibility each)
│   ├── __init__.py
│   ├── ocr_agent.py            # Agent 1 — Gemini Vision OCR
│   ├── privacy_agent.py        # Agent 2 — Identity redaction
│   ├── evaluation_agent.py     # Agent 3 — AI grading with model fallback
│   ├── bias_agent.py           # Agent 4 — Bias classification
│   └── reporting_agent.py      # Agent 5 — Final report assembly
├── tests/
│   └── test_agents.py          # Unit tests (Privacy, Bias, Reporting agents)
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container deployment config
├── .env.example                # Environment variable template
├── .github/workflows/ci.yml    # GitHub Actions CI pipeline
├── CONTRIBUTING.md
├── LICENSE
└── fairgrade-ai/               # React frontend
    ├── src/
    │   ├── App.jsx             # Main application
    │   ├── Analytics.jsx       # Bias analytics dashboard
    │   ├── components/         # Reusable UI components
    │   └── config/             # Firebase configuration
    ├── .env.example
    ├── package.json
    └── vite.config.js
```

---

## 👥 Team VEKTOR ⚡

<p align="center">
  <i>Built with ❤️ for the Google Solution Challenge 2026</i>
</p>

| Name | Role | GitHub |
|------|------|--------|
| **Yashas M** | Full-Stack & AI Engineer | [@Yashasm18](https://github.com/Yashasm18) |

> *Team VEKTOR — building technology for equitable education.*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
