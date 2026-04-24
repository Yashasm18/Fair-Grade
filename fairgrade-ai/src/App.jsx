import React, { useState, useEffect } from 'react';
import { FileSearch, Download, PieChart, Home, FileType, Sparkles, Zap, LogIn, LogOut, ShieldCheck, UserCheck } from 'lucide-react';
import { auth, db } from "./config/firebase";
import { collection, addDoc } from "firebase/firestore";
import { onAuthStateChanged, signInWithPopup, GoogleAuthProvider, signOut } from "firebase/auth";
import Analytics from "./Analytics";
import EvaluationSetup from "./components/EvaluationSetup";
import AgentPipeline from "./components/AgentPipeline";
import ResultCard from "./components/ResultCard";
import Footer from "./components/Footer";
import DarkModeToggle from "./components/DarkModeToggle";

// ─── Configurable API URL ───
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
// Prompt template is handled server-side in app.py
// ─── Demo Mode Sample Data ───
const DEMO_RESULTS = [
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
      bias: { level: "Medium", status: "Undergraded", gap: 2.5, biasScorePercentage: 25.0, formulaUsed: "Bias Score (%) = (|Teacher Score - AI Score| / 10) * 100" },
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
      bias: { level: "Low", status: "Fair", gap: 0.5, biasScorePercentage: 5.0, formulaUsed: "Bias Score (%) = (|Teacher Score - AI Score| / 10) * 100" },
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
      bias: { level: "High", status: "Undergraded", gap: 4.5, biasScorePercentage: 45.0, formulaUsed: "Bias Score (%) = (|Teacher Score - AI Score| / 10) * 100" },
      verified: false
    },
    error: null
  }
];

function App() {
  // ─── Dark Mode ───
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem('fairgrade_theme');
    if (stored) return stored === 'dark';
    return false; // Default to light mode
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('fairgrade_theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // ─── Pre-warm Backend ───
  useEffect(() => {
    fetch(`${API_URL}/`).catch(() => { /* ignore pre-warm errors */ });
  }, []);

  // ─── Navigation & Demo Mode ───
  const [activeTab, setActiveTab] = useState('evaluate');
  const [demoMode, setDemoMode] = useState(false);

  // ─── Authentication State ───
  const [user, setUser] = useState(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  const handleLogin = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error("Login failed:", error);
      setGlobalError("Google Login failed. Please try again.");
    }
  };

  const handleLogout = () => signOut(auth);

  // ─── Evaluation State ───
  const [teacherScore, setTeacherScore] = useState('');
  const [questionContext, setQuestionContext] = useState('');
  const [studentIds, setStudentIds] = useState({});
  const [files, setFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);

  // ─── Processing State ───
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(-1);
  const [results, setResults] = useState([]);
  const [currentStep, setCurrentStep] = useState(-1);
  const [globalError, setGlobalError] = useState('');

  const handleStudentIdChange = (fileName, value) => {
    setStudentIds(prev => ({ ...prev, [fileName]: value }));
  };

  const handleDrag = function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = function (e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = function (e) {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (fileName) => {
    setFiles(prev => prev.filter(f => f.name !== fileName));
    setStudentIds(prev => {
      const next = { ...prev };
      delete next[fileName];
      return next;
    });
  };

  const truncateName = (name, max = 28) => {
    if (!name || name.length <= max) return name || '';
    const ext = name.substring(name.lastIndexOf('.'));
    return name.substring(0, max - ext.length - 3) + '...' + ext;
  };

  // ─── Retry a single failed file ───
  const retryFile = async (fileName) => {
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
            teacher_score: Number(teacherScore),
            bias_status: data.bias.status,
            bias_level: data.bias.level,
            anonymized_text: data.anonymizedText,
            explanation: data.evaluation.explanation,
            timestamp: new Date()
          });
        }
      } catch (fsErr) {
        console.error("Failed to save to Firestore:", fsErr);
      }
    } catch (err) {
      updatedResults[idx] = { fileName: file.name, data: null, error: err.message };
    }

    setResults(updatedResults);
  };

  // ─── Main Pipeline ───
  const runAgents = async () => {
    if (files.length === 0) {
      setGlobalError("Please upload at least one answer sheet.");
      return;
    }
    if (teacherScore === '' || teacherScore < 0 || teacherScore > 10) {
      setGlobalError("Please provide a valid teacher score between 0 and 10.");
      return;
    }

    try {
      setIsProcessing(true);
      setGlobalError('');
      setResults([]);

      const sessionResults = [];

      for (let i = 0; i < files.length; i++) {
        setCurrentFileIndex(i);
        setCurrentStep(0);

        // Rate-limit guard: wait 3s between files to avoid Gemini 429 errors
        if (i > 0) {
          await new Promise(resolve => setTimeout(resolve, 3000));
        }

        const file = files[i];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("teacher_score", teacherScore);
        if (questionContext) {
          formData.append("question_context", questionContext);
        }

        // Animate steps visually
        const stepInterval = setInterval(() => {
          setCurrentStep(prev => (prev < 4 ? prev + 1 : prev));
        }, 800);

        try {
          const response = await fetch(`${API_URL}/api/evaluate`, {
            method: "POST",
            body: formData,
          });

          clearInterval(stepInterval);
          setCurrentStep(5); // Complete

          if (!response.ok) {
            throw new Error(await response.text() || `Failed to process ${file.name}.`);
          }

          const data = await response.json();
          const reportObj = { fileName: file.name, data, error: null };
          sessionResults.push(reportObj);

          // --- Save to Firestore ---
          try {
            if (import.meta.env.VITE_FIREBASE_API_KEY) {
              await addDoc(collection(db, "evaluations"), {
                student_identifier: studentIds[file.name] || 'N/A',
                teacher_uid: user?.uid || 'anonymous',
                teacher_email: user?.email || 'anonymous',
                ai_score: data.evaluation.aiScore,
                teacher_score: Number(teacherScore),
                bias_status: data.bias.status,
                bias_level: data.bias.level,
                anonymized_text: data.anonymizedText,
                explanation: data.evaluation.explanation,
                timestamp: new Date()
              });
              console.log("Saved evaluation to Firestore!");
            } else {
              console.warn("Firebase not configured. Skipping Firestore upload.");
            }
          } catch (fsErr) {
            console.error("Failed to save to Firestore:", fsErr);
          }

        } catch (err) {
          clearInterval(stepInterval);
          sessionResults.push({ fileName: file.name, data: null, error: err.message });
        }

        setResults([...sessionResults]);
      }
    } catch (err) {
      setGlobalError(err.message || "An unexpected error occurred during batch evaluation.");
    } finally {
      setIsProcessing(false);
      setCurrentFileIndex(-1);
      setCurrentStep(-1);
    }
  };

  // ─── CSV Export ───
  const exportToCSV = () => {
    const data = demoMode ? DEMO_RESULTS : results;
    if (data.length === 0) return;
    const headers = ['File Name', 'Student Tracking ID', 'Teacher Score', 'AI Score', 'Bias Level', 'Bias Status', 'AI Explanation'];
    const rows = data.map(r => {
      if (r.error) return [r.fileName, '', '', '', '', 'Error', r.error];
      const id = studentIds[r.fileName] || 'N/A';
      return [
        r.fileName,
        id,
        r.data.evaluation.teacherScore,
        r.data.evaluation.aiScore,
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
  const exportToPDF = () => {
    window.print();
  };

  // ─── Human-in-the-Loop: Teacher Verification ───
  const verifyEvaluation = async (fileName, verifyData) => {
    try {
      const response = await fetch(`${API_URL}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName, ...verifyData }),
      });
      if (response.ok) {
        const result = await response.json();
        console.log('Verification saved:', result);
        // Save verification to Firestore
        try {
          if (import.meta.env.VITE_FIREBASE_API_KEY) {
            await addDoc(collection(db, 'verifications'), {
              fileName,
              teacher_uid: user?.uid || 'anonymous',
              action: verifyData.action,
              finalScore: verifyData.finalScore,
              originalAiScore: verifyData.originalAiScore,
              originalTeacherScore: verifyData.originalTeacherScore,
              overrideReason: verifyData.overrideReason || null,
              timestamp: new Date(),
            });
          }
        } catch (fsErr) {
          console.error('Failed to save verification to Firestore:', fsErr);
        }
      }
    } catch (err) {
      console.error('Verification request failed:', err);
    }
  };

  // ─── Demo Mode ───
  const activateDemo = () => {
    setDemoMode(true);
    setTeacherScore('6');
    setStudentIds({
      'demo_answer_biology.jpg': 'STU-001',
      'demo_answer_history.png': 'STU-002',
      'demo_answer_math.pdf': 'STU-003'
    });
  };

  const exitDemo = () => {
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
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginRight: '1rem', padding: '0.4rem 0.8rem', background: 'rgba(5, 150, 105, 0.05)', borderRadius: '8px', border: '1px solid rgba(5, 150, 105, 0.1)' }}>
              <UserCheck size={14} color="#059669" />
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-main)' }}>{user.displayName?.split(' ')[0]}</span>
              <button onClick={handleLogout} style={{ background: 'none', border: 'none', padding: 0, color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', marginLeft: '0.5rem' }} title="Logout">
                <LogOut size={14} />
              </button>
            </div>
          ) : (
             <button 
                onClick={handleLogin}
                className="btn-primary" 
                style={{ marginRight: '1rem', padding: '0.4rem 0.8rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <LogIn size={14} /> Educator Login
              </button>
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

      {/* ─── Main App (Unlocked for Demo Purposes) ─── */}
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
            {!demoMode && (isProcessing || currentStep > -1) ? (
              <AgentPipeline currentStep={currentStep} fileName={truncateName(files[currentFileIndex]?.name || '')} />
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

      {/* ─── Footer ─── */}
      <Footer />
    </div>
  );
}

export default App;
