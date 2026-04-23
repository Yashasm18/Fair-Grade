# 🏆 FairGrade AI — Bias Detection in Student Grading

FairGrade AI ensures fair evaluation by removing identity bias and using AI to detect grading inconsistencies — all while keeping data secure and private.

## New Features
- **Question Context**: Teachers can now paste the question and model answer to guide the AI for more accurate grading.
- **Batch Processing**: Supports uploading multiple answer sheets at once. The system will process them sequentially.
- **PDF Support**: Upload PDF documents; the application will automatically extract the first page for OCR.
- **Analytics Dashboard**: Tracks the aggregated average scores, bias distribution (Overgraded, Undergraded, Fair) over time, and history of recent evaluations.
- **Firestore Integration**: Persistently stores evaluation data mapped by timestamp and scores.

## Architecture

This project is fully divided into a Client-Server model for privacy and security.

- **Frontend:** React + Vite (No API Keys ever exposed, directly stores eval metrics to Firestore)
- **Backend:** Python + FastAPI (Secure AI agent orchestration handling PDFs and images)
- **AI Core:** Gemini-2.0-Flash & Google Cloud Vision API

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (optional, for backend deployment)

## Setup Instructions

### 1. Backend Setup

The backend handles the core Antigravity multi-agent system.

1. Navigate to the root level `gdc proj` directory.
2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and fill in your API details:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   GOOGLE_APPLICATION_CREDENTIALS=your_service_account_json_path
   ```
   *(Note: If Google Vision is not configured, a demo fallback text will be used automatically).*
4. Start the FastAPI backend server:
   ```bash
   uvicorn app:app --reload --port 8000
   ```

### 2. Frontend Setup

The frontend connects to the local backend `http://localhost:8000`.

1. Open a new terminal and navigate to the `fairgrade-ai` directory:
   ```bash
   cd fairgrade-ai
   ```
2. Install Node dependencies (Make sure to run this if you recently cloned or added new UI packages like `recharts`!):
   ```bash
   npm install
   ```
3. Provide your Firebase Configuration in `.env` (maps to `src/config/firebase.js`).
4. Start the Vite React development server:
   ```bash
   npm run dev
   ```
5. Go to `http://localhost:5173` to test the application!

## Deployment Guides

### Deploying the Backend to Google Cloud Run
A `.Dockerfile` is provided at the root folder.
1. Build the Docker image:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/fairgrade-backend
   ```
2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy fairgrade-backend \
     --image gcr.io/YOUR_PROJECT_ID/fairgrade-backend \
     --platform managed \
     --allow-unauthenticated \
     --port 8080 \
     --set-env-vars GEMINI_API_KEY=your_key
   ```

### Deploying the Frontend to Firebase Hosting
Firebase configuration files (`firebase.json` and `.firebaserc`) are set up for Single Page App routing.
1. Build the production files:
   ```bash
   npm run build
   ```
2. Initialize and deploy:
   ```bash
   firebase login
   firebase use --add  # Select your project
   firebase deploy --only hosting
   ```

## How it works

1. You upload answer sheets (or PDFs) and enter the real Teacher's score.
2. The UI sends the images/PDFs to `/api/evaluate` securely sequentially via batch processing.
3. The **OCR Agent** extracts text from the image/PDF.
4. The **Privacy Agent** anonymizes names, IDs, and roll numbers.
5. The **Evaluation Agent** assesses the answer content via Gemini AI out of 10 points using your provided specific question context.
6. The **Bias Agent** checks the discrepancy between the Teacher and the AI mark.
7. A generated report is sent back, displayed interactively, and logged to the global **Analytics Dashboard** and Firebase Firestore!
