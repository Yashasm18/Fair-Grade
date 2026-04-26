import React, { useState, useEffect } from 'react';
import { FileSearch, Download, PieChart, Home, FileType, Sparkles, Zap, LogIn, LogOut, ShieldCheck, UserCheck, Wifi, WifiOff } from 'lucide-react';
import { auth, db } from "./config/firebase";
import { collection, addDoc } from "firebase/firestore";
import { onAuthStateChanged, signInWithPopup, GoogleAuthProvider, signOut, User } from "firebase/auth";
import Analytics from "./Analytics";
import EvaluationSetup from "./components/EvaluationSetup";
import AgentPipeline from "./components/AgentPipeline";
import ResultCard from "./components/ResultCard";
import Footer from "./components/Footer";
import DarkModeToggle from "./components/DarkModeToggle";
import SkeletonLoader from "./components/SkeletonLoader";
import { useToast } from "./components/Toast";
import type { FileResult, VerifyPayload } from './types';

// ─── Configurable API URL ───
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
// ─── API key sent as X-API-Key header (matches backend FAIRGRADE_API_KEY) ───
const FAIRGRADE_API_KEY = import.meta.env.VITE_FAIRGRADE_API_KEY || "";

// ─── App-level constants (replace magic numbers scattered inline) ───
const RATE_LIMIT_DELAY_MS   = 3000;  // ms to wait between batch files (Gemini 429 guard)
const MAX_TEACHER_SCORE     = 10;   // maximum score on the 0–10 scale
const FILENAME_TRUNCATE_LEN = 28;   // max chars before truncation with ellipsis
// Pipeline animation: each step shown for 3 s so it doesn't finish before real backend work
const PIPELINE_STEP_MS      = 3000;

// ─── Demo Mode Sample Data ───
const DEMO_RESULTS: FileResult[] = [
  {
    fileName: "demo_answer_biology.jpg",
    data: {
      originalTextLength: 312,
      anonymizedText: "The mitochondria is the powerhouse of the cell. It generates most of the chemical energy needed to power the cell's biochemical reactions. Through oxidative phosphorylation, ATP is produced which serves as the energy currency. The process involves the electron transport chain located on the inner mitochondrial membrane.",
      evaluation: {
        aiScore: 8.5,
        teacherScore: 6,
        explanation: "The student demonstrates strong understanding of mitochondrial function, correctly identifying ATP production via oxidative phosphorylation and the electron transport chain. Minor deduction for not mentioning the citric acid cycle. Overall, a comprehensive and factually accurate response.",
        confidenceScore: 0.95
      },
      bias: { level: "Medium", status: "Undergraded", gap: 2.5, biasScorePercentage: 25.0, completenessFactor: 1.0, formulaUsed: "Bias Score (%) = min(100, |6 − 8.5| × 10) × Completeness Factor (1.0)" },
      verified: false
    },
    error: null
  },
  {
    fileName: "demo_answer_history.png",
    data: {
      originalTextLength: 256,
      anonymizedText: "The French Revolution began in 1789 and was caused by social inequality, financial crisis, and Enlightenment ideas. The storming of the Bastille on July 14 marked a turning point. Key outcomes included the Declaration of the Rights of Man and the rise of Napoleon.",
      evaluation: {
        aiScore: 7,
        teacherScore: 7.5,
        explanation: "Good overview of the French Revolution's causes and key events. The student correctly identifies the main triggers and outcomes. Slight gap in discussing the Reign of Terror and its significance. The response is well-structured but could benefit from more specific dates and figures.",
        confidenceScore: 0.88
      },
      bias: { level: "Low", status: "Fair", gap: 0.5, biasScorePercentage: 4.5, completenessFactor: 0.9, formulaUsed: "Bias Score (%) = min(100, |7.5 − 7| × 10) × Completeness Factor (0.9)" },
      verified: false
    },
    error: null
  },
  {
    fileName: "demo_answer_math.pdf",
    data: {
      originalTextLength: 189,
      anonymizedText: "To solve the quadratic equation x² + 5x + 6 = 0, I factored it as (x+2)(x+3) = 0. Therefore x = -2 or x = -3. I verified by substituting both values back into the original equation.",
      evaluation: {
        aiScore: 9.5,
        teacherScore: 5,
        explanation: "Excellent mathematical reasoning. The factoring approach is correct, both solutions are accurate, and the student demonstrates good practice by verifying the answers. Near-perfect response with clear logical steps.",
        confidenceScore: 0.99
      },
      bias: { level: "High", status: "Undergraded", gap: 4.5, biasScorePercentage: 40.5, completenessFactor: 0.9, formulaUsed: "Bias Score (%) = min(100, |5 − 9.5| × 10) × Completeness Factor (0.9)" },
      verified: false
    },
    error: null
  }
];

function App() {
  // ─── Dark Mode ───
  const [isDark, setIsDark] = useState<boolean>(() => {
    const stored = localStorage.getItem('fairgrade_theme');
    if (stored) return stored === 'dark';
    return false; // Default to light mode
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('fairgrade_theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // ─── Backend connection state (pre-warm indicator) ───
  // Initialized as 'connecting' — no need to call setBackendStatus() inside
  // the effect body (that triggers a cascading render and the lint rule).
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'online' | 'offline'>('connecting');

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then(r => { if (r.ok) setBackendStatus('online'); else setBackendStatus('offline'); })
      .catch(() => setBackendStatus('offline'));
  }, []);

  // ─── Navigation & Demo Mode ───
  const [activeTab, setActiveTab] = useState<'evaluate' | 'analytics'>('evaluate');
  const [demoMode, setDemoMode] = useState(false);

  // ─── Authentication State ───
  const [user, setUser] = useState<User | null>(null);
  const [isGuest, setIsGuest] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setIsAuthLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const handleLogin = async (): Promise<void> => {
    const provider = new GoogleAuthProvider();
    setIsAuthLoading(true);
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error("Login failed:", error);
      setGlobalError("Google Login failed. Please try again.");
      setIsAuthLoading(false);
    }
  };

  const handleLogout = (): void => { signOut(auth); };

  // ─── Evaluation State ───
  const [teacherScore, setTeacherScore] = useState('');
  const [questionContext, setQuestionContext] = useState('');
  const [questionWeight, setQuestionWeight] = useState<number>(1.0);
  const [studentIds, setStudentIds] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);

  // ─── Processing State ───
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(-1);
  const [results, setResults] = useState<FileResult[]>([]);
  const [currentStep, setCurrentStep] = useState(-1);
  const [globalError, setGlobalError] = useState('');
  const [isRateLimiting, setIsRateLimiting] = useState(false);

  const { showToast } = useToast();

  const handleStudentIdChange = (fileName: string, value: string): void => {
    setStudentIds(prev => ({ ...prev, [fileName]: value }));
  };

  const handleDrag = function (e: React.DragEvent<HTMLDivElement>): void {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = function (e: React.DragEvent<HTMLDivElement>): void {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = function (e: React.ChangeEvent<HTMLInputElement>): void {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (fileName: string): void => {
    setFiles(prev => prev.filter(f => f.name !== fileName));
    setStudentIds(prev => {
      const next = { ...prev };
      delete next[fileName];
      return next;
    });
  };

  const truncateName = (name: string, max: number = FILENAME_TRUNCATE_LEN): string => {
    if (!name || name.length <= max) return name || '';
    const ext = name.substring(name.lastIndexOf('.'));
    return name.substring(0, max - ext.length - 3) + '...' + ext;
  };

  // ─── Retry a single failed file ───
  const retryFile = async (fileName: string): Promise<void> => {
    const file = files.find(f => f.name === fileName);
    if (!file) return;

    const idx = results.findIndex(r => r.fileName === fileName);
    if (idx === -1) return;

    // Mark as processing
    const updatedResults = [...results];

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("teacher_score", teacherScore);
      if (questionContext) formData.append("question_context", questionContext);

      const response = await fetch(`${API_URL}/api/evaluate`, {
        method: "POST",
        headers: FAIRGRADE_API_KEY ? { 'X-API-Key': FAIRGRADE_API_KEY } : {},
        body: formData,
      });

      if (!response.ok) throw new Error(await response.text() || `Failed to process ${file.name}.`);

      const data = await response.json();
      updatedResults[idx] = { fileName: file.name, data, error: null };

      // Save to Firestore
      try {
        if (import.meta.env.VITE_FIREBASE_API_KEY) {
          await addDoc(collection(db, "evaluations"), {
            student_identifier: studentIds[file.name] || 'N/A',
            ai_score: data.evaluation.aiScore,
            weighted_score: data.weightedScore ?? data.evaluation.aiScore,
            question_weight: data.questionWeight ?? 1.0,
            teacher_score: Number(teacherScore),
            bias_status: data.bias.status,
            bias_level: data.bias.level,
            bias_indicators: data.biasIndicators ?? [],
            anonymized_text: data.anonymizedText,
            explanation: data.evaluation.explanation,
            timestamp: new Date()
          });
        }
      } catch (fsErr) {
        console.error("Failed to save to Firestore:", fsErr);
      }
    } catch (err) {
      updatedResults[idx] = { fileName: file.name, data: null, error: (err as Error).message };
    }

    setResults(updatedResults);
  };

  // ─── Main Pipeline ───
  const runAgents = async (): Promise<void> => {
    if (files.length === 0) {
      setGlobalError("Please upload at least one answer sheet.");
      return;
    }
    if (teacherScore === '' || Number(teacherScore) < 0 || Number(teacherScore) > MAX_TEACHER_SCORE) {
      setGlobalError(`Please provide a valid teacher score between 0 and ${MAX_TEACHER_SCORE}.`);
      return;
    }

    try {
      setIsProcessing(true);
      setGlobalError('');
      setResults([]);

      const sessionResults: FileResult[] = [];

      for (let i = 0; i < files.length; i++) {
        setCurrentFileIndex(i);
        setCurrentStep(0);

        // Rate-limit guard: wait between files to avoid Gemini 429 errors
        if (i > 0) {
          setIsRateLimiting(true);
          showToast(`Rate limiting — waiting ${RATE_LIMIT_DELAY_MS / 1000}s for API quota before next file…`, 'info', RATE_LIMIT_DELAY_MS);
          await new Promise(resolve => setTimeout(resolve, RATE_LIMIT_DELAY_MS));
          setIsRateLimiting(false);
        }

        const file = files[i];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("teacher_score", teacherScore);
        if (questionContext) {
          formData.append("question_context", questionContext);
        }
        formData.append("question_weight", String(questionWeight));

        // Animate pipeline steps. PIPELINE_STEP_MS keeps the animation
        // in sync with actual backend processing time (OCR alone can take 5-15s).
        const stepInterval = setInterval(() => {
          setCurrentStep(prev => (prev < 4 ? prev + 1 : prev));
        }, PIPELINE_STEP_MS);

        try {
          const response = await fetch(`${API_URL}/api/evaluate`, {
            method: "POST",
            headers: FAIRGRADE_API_KEY ? { 'X-API-Key': FAIRGRADE_API_KEY } : {},
            body: formData,
          });

          clearInterval(stepInterval);
          setCurrentStep(5); // Complete

          if (!response.ok) {
            const errText = await response.text();
            // Surface Gemini quota errors with specific guidance
            if (errText.includes('QUOTA_EXHAUSTED') || errText.includes('429')) {
              throw new Error('Gemini API quota exhausted. Please wait ~1 minute and retry, or enable billing at aistudio.google.com/api-keys.');
            }
            throw new Error(errText || `Failed to process ${file.name}.`);
          }

          const data = await response.json();

          // Warn if backend reported any agent failures
          if (data.pipelineWarnings?.length) {
            data.pipelineWarnings.forEach((w: { agent: string; error: string }) =>
              showToast(`${w.agent}: ${w.error.slice(0, 80)}`, 'warning', 6000)
            );
          }

          // Show quota exhaustion even in partial success (score=0 with QUOTA message)
          if (data.evaluation?.explanation?.includes('QUOTA_EXHAUSTED')) {
            showToast('Gemini quota exhausted — AI grading unavailable. Wait ~1 min or enable billing.', 'error', 8000);
          } else {
            showToast(`✓ ${truncateName(file.name)} evaluated — AI score: ${data.evaluation?.aiScore ?? '?'}/10`, 'success');
          }

          const reportObj: FileResult = { fileName: file.name, data, error: null };
          sessionResults.push(reportObj);

          // Save to Firestore (fire-and-forget)
          if (import.meta.env.VITE_FIREBASE_API_KEY) {
            addDoc(collection(db, 'evaluations'), {
              student_identifier: studentIds[file.name] || 'N/A',
              teacher_uid: user?.uid || 'anonymous',
              teacher_email: user?.email || 'anonymous',
              ai_score: data.evaluation.aiScore,
              weighted_score: data.weightedScore ?? data.evaluation.aiScore,
              question_weight: data.questionWeight ?? 1.0,
              teacher_score: Number(teacherScore),
              bias_status: data.bias.status,
              bias_level: data.bias.level,
              bias_indicators: data.biasIndicators ?? [],
              anonymized_text: data.anonymizedText,
              explanation: data.evaluation.explanation,
              timestamp: new Date(),
            }).catch(fsErr => console.error('Firestore write failed:', fsErr));
          }

        } catch (err) {
          clearInterval(stepInterval);
          const errMsg = (err as Error).message;
          showToast(`${truncateName(file.name)}: ${errMsg.slice(0, 100)}`, 'error', 7000);
          sessionResults.push({ fileName: file.name, data: null, error: errMsg });
        }

        setResults([...sessionResults]);
      }
    } catch (err) {
      setGlobalError((err as Error).message || "An unexpected error occurred during batch evaluation.");
    } finally {
      setIsProcessing(false);
      setCurrentFileIndex(-1);
      setCurrentStep(-1);
    }
  };

  // ─── CSV Export ───
  const exportToCSV = (): void => {
    const data = demoMode ? DEMO_RESULTS : results;
    if (data.length === 0) return;
    const headers = ['File Name', 'Student Tracking ID', 'Teacher Score', 'AI Score', 'Bias Level', 'Bias Status', 'AI Explanation'];
    const rows = data.map(r => {
      if (r.error || !r.data) return [r.fileName, '', '', '', '', 'Error', r.error || ''];
      const id = studentIds[r.fileName] || 'N/A';
      return [
        r.fileName,
        id,
        String(r.data.evaluation.teacherScore),
        String(r.data.evaluation.aiScore),
        r.data.bias.level,
        r.data.bias.status,
        `"${r.data.evaluation.explanation.replace(/"/g, '""')}"`
      ];
    });
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "fairgrade_batch_results.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ─── PDF Export (print-friendly) ───
  const exportToPDF = (): void => {
    window.print();
  };

  // ─── Human-in-the-Loop: Teacher Verification ───
  const verifyEvaluation = async (fileName: string, verifyData: VerifyPayload): Promise<void> => {
    try {
      const response = await fetch(`${API_URL}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName, ...verifyData }),
      });
      if (response.ok) {
        const result = await response.json();
        console.log('Verification saved:', result);

        // ── Update local results state so the UI reflects verified=true immediately ──
        setResults(prev =>
          prev.map(r =>
            r.fileName === fileName && r.data
              ? {
                  ...r,
                  data: {
                    ...r.data,
                    verified: true,
                    evaluation: {
                      ...r.data.evaluation,
                      // Reflect the final score chosen by the teacher
                      teacherScore: verifyData.finalScore,
                    },
                  },
                }
              : r
          )
        );

        // Save verification to Firestore (fire-and-forget is acceptable here;
        // the UI has already updated optimistically above)
        if (import.meta.env.VITE_FIREBASE_API_KEY) {
          addDoc(collection(db, 'verifications'), {
            fileName,
            teacher_uid: user?.uid || 'anonymous',
            action: verifyData.action,
            finalScore: verifyData.finalScore,
            originalAiScore: verifyData.originalAiScore,
            originalTeacherScore: verifyData.originalTeacherScore,
            overrideReason: verifyData.overrideReason || null,
            timestamp: new Date(),
          }).catch(fsErr => console.error('Failed to save verification to Firestore:', fsErr));
        }
      }
    } catch (err) {
      console.error('Verification request failed:', err);
    }
  };

  // ─── Demo Mode ───
  const activateDemo = (): void => {
    setDemoMode(true);
    setTeacherScore('6');
    setStudentIds({
      'demo_answer_biology.jpg': 'STU-001',
      'demo_answer_history.png': 'STU-002',
      'demo_answer_math.pdf': 'STU-003'
    });
  };

  const exitDemo = (): void => {
    setDemoMode(false);
    setResults([]);
    setTeacherScore('');
    setStudentIds({});
    setFiles([]);
  };

  const displayResults = demoMode ? DEMO_RESULTS : results;

  return (
    <div className="app-container">
      {/* ─── Header ─── */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="logo-text">FairGrade AI</h1>
          <p className="subtitle">Exposing hidden bias affecting millions of students to give schools actionable insights.</p>
          {/* Backend connection status pill */}
          <span
            aria-label={`Backend status: ${backendStatus}`}
            title={backendStatus === 'offline' ? 'Backend is offline — results may be slow or unavailable' : ''}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
              fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.03em',
              padding: '0.15rem 0.55rem', borderRadius: '999px', marginTop: '0.3rem',
              background: backendStatus === 'online' ? 'rgba(5,150,105,0.1)' : backendStatus === 'offline' ? 'rgba(239,68,68,0.1)' : 'rgba(124,58,237,0.1)',
              color: backendStatus === 'online' ? '#059669' : backendStatus === 'offline' ? '#ef4444' : 'var(--primary)',
              border: `1px solid ${backendStatus === 'online' ? 'rgba(5,150,105,0.25)' : backendStatus === 'offline' ? 'rgba(239,68,68,0.25)' : 'rgba(124,58,237,0.2)'}`,
            }}
          >
            {backendStatus === 'online' ? <Wifi size={10} /> : backendStatus === 'offline' ? <WifiOff size={10} /> : (
              <span style={{ display: 'inline-block', width: 8, height: 8, border: '1.5px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
            )}
            {backendStatus === 'connecting' ? 'Connecting to server…' : backendStatus === 'online' ? 'Server online' : 'Server offline'}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginRight: '1rem', padding: '0.4rem 0.8rem', background: 'rgba(5, 150, 105, 0.05)', borderRadius: '8px', border: '1px solid rgba(5, 150, 105, 0.1)' }}>
              <UserCheck size={14} color="#059669" />
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-main)' }}>{user.displayName?.split(' ')[0]}</span>
              <button onClick={handleLogout} style={{ background: 'none', border: 'none', padding: 0, color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', marginLeft: '0.5rem' }} title="Logout">
                <LogOut size={14} />
              </button>
            </div>
          )}
          <DarkModeToggle isDark={isDark} onToggle={() => setIsDark(!isDark)} />
          <button
            className={`nav-btn ${activeTab === 'evaluate' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluate')}
            aria-label="Evaluate tab"
          >
            <Home size={16} /> Evaluate
          </button>
          <button
            className={`nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
            aria-label="Analytics tab"
          >
            <PieChart size={16} /> Analytics
          </button>
        </div>
      </header>

      {/* ─── Login Screen ─── */}
      {!user && !isGuest && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem 2rem', maxWidth: '500px', margin: '4rem auto' }}>
          <div style={{ display: 'inline-flex', padding: '1rem', borderRadius: '20px', background: 'rgba(139, 92, 246, 0.1)', marginBottom: '1.5rem' }}>
            <ShieldCheck size={48} color="var(--primary)" />
          </div>
          <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>Educator Portal</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
            Sign in with your educational account to access the FairGrade AI pipeline and bias analytics dashboard.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <button 
              onClick={handleLogin}
              disabled={isAuthLoading}
              className="btn-primary" 
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', padding: '1rem', width: '100%', opacity: isAuthLoading ? 0.7 : 1, cursor: isAuthLoading ? 'not-allowed' : 'pointer' }}
            >
              {isAuthLoading ? (
                <span style={{ display: 'inline-block', width: 20, height: 20, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
              ) : (
                <LogIn size={20} />
              )}
              {isAuthLoading ? 'Signing in…' : 'Sign in with Google'}
            </button>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', margin: '0.5rem 0' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }}></div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>or</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }}></div>
            </div>

            <button 
              onClick={() => setIsGuest(true)}
              className="btn-primary" 
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', padding: '1rem', width: '100%', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-main)' }}
            >
              <Zap size={20} /> Try the Demo (Guest Mode)
            </button>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1.5rem' }}>
            Secure authentication powered by Firebase Auth (Google OAuth 2.0)
          </p>
        </div>
      )}

      {/* ─── Main App (Visible if logged in or guest mode) ─── */}
      {(user || isGuest) && (
        <>
          {/* ─── Demo Mode Banner ─── */}
      {activeTab === 'evaluate' && !demoMode && results.length === 0 && !isProcessing && (
        <div className="demo-banner">
          <div className="demo-banner-content">
            <Zap size={18} />
            <span><strong>New here?</strong> Try our interactive demo with preloaded sample data</span>
          </div>
          <button className="demo-btn" onClick={activateDemo}>
            <Sparkles size={14} /> Launch Demo
          </button>
        </div>
      )}
      {demoMode && (
        <div className="demo-banner demo-active">
          <div className="demo-banner-content">
            <Zap size={18} />
            <span><strong>Demo Mode Active</strong> — Showing sample evaluation results</span>
          </div>
          <button className="demo-btn demo-exit" onClick={exitDemo}>
            Exit Demo
          </button>
        </div>
      )}

      {/* ─── Main Content ─── */}
      {activeTab === 'analytics' ? (
        <Analytics />
      ) : (
        <div className="grid-layout" style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: '2rem' }}>

          {/* Sidebar */}
          {!demoMode && (
            <EvaluationSetup
              teacherScore={teacherScore}
              setTeacherScore={setTeacherScore}
              questionContext={questionContext}
              setQuestionContext={setQuestionContext}
              questionWeight={questionWeight}
              setQuestionWeight={setQuestionWeight}
              files={files}
              studentIds={studentIds}
              handleStudentIdChange={handleStudentIdChange}
              handleChange={handleChange}
              handleDrag={handleDrag}
              handleDrop={handleDrop}
              dragActive={dragActive}
              removeFile={removeFile}
              isProcessing={isProcessing}
              currentFileIndex={currentFileIndex}
              runAgents={runAgents}
              globalError={globalError}
              truncateName={truncateName}
            />
          )}

          {/* Main Content Area */}
          <div style={demoMode ? { gridColumn: '1 / -1' } : {}}>
            {/* Rate-limiting banner — shown during inter-file delay */}
            {isRateLimiting && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.65rem 1rem', marginBottom: '1rem', background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.2)', borderRadius: '10px', fontSize: '0.82rem', color: 'var(--primary)' }}>
                <span style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
                Rate limiting — waiting {RATE_LIMIT_DELAY_MS / 1000}s for Gemini API quota before processing next file…
              </div>
            )}

            {!demoMode && (isProcessing || currentStep > -1) ? (
              <>
                <AgentPipeline currentStep={currentStep} fileName={truncateName(files[currentFileIndex]?.name || '')} />
                {/* Skeleton cards preview the result layout while backend runs */}
                <SkeletonLoader count={Math.max(1, files.length - results.length)} />
              </>
            ) : !demoMode && displayResults.length === 0 && (
              <div className="glass-panel empty-state">
                <FileSearch size={56} />
                <h3>No Evaluations Yet</h3>
                <p>Upload answer sheet(s) and run the pipeline to begin secure server-side evaluation.</p>
              </div>
            )}

            {displayResults.length > 0 && (
              <div className="results-container" id="printable-results">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: "1.25rem", flexWrap: 'wrap', gap: '0.5rem' }}>
                  <h2>
                    {demoMode ? 'Demo Results' : `Batch Results (${results.length}/${files.length})`}
                  </h2>
                  <div style={{ display: 'flex', gap: '0.5rem' }} className="no-print">
                    <button className="btn-primary" style={{ width: 'auto', padding: '0.5rem 1rem', fontSize: '0.85rem' }} onClick={exportToCSV}>
                      <Download size={14} /> Export CSV
                    </button>
                    <button className="btn-primary btn-secondary" style={{ width: 'auto', padding: '0.5rem 1rem', fontSize: '0.85rem' }} onClick={exportToPDF}>
                      <FileType size={14} /> Export PDF
                    </button>
                  </div>
                </div>
                {displayResults.map((res, i) => (
                  <ResultCard
                    key={i}
                    result={res}
                    studentId={studentIds[res.fileName] || (demoMode ? ['STU-001', 'STU-002', 'STU-003'][i] : 'N/A')}
                    onRetry={!demoMode ? retryFile : null}
                    onVerify={verifyEvaluation}
                    truncateName={truncateName}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      </>
      )}

      {/* ─── Footer ─── */}
      <Footer />
    </div>
  );
}

export default App;
