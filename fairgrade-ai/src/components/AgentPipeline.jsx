import React from 'react';
import { FileText, Shield, Sparkles, AlertTriangle, CheckCircle, Check } from 'lucide-react';

/**
 * AgentPipeline — Shows the 5-agent processing steps with animations.
 */
const steps = [
  { title: "OCR Agent", desc: "Extracting text from image on secure server", icon: <FileText size={20} /> },
  { title: "Privacy Agent", desc: "Anonymizing personal identifiers", icon: <Shield size={20} /> },
  { title: "Evaluation Agent", desc: "Grading objectively with Gemini AI", icon: <Sparkles size={20} /> },
  { title: "Bias Agent", desc: "Comparing with teacher score", icon: <AlertTriangle size={20} /> },
  { title: "Reporting Agent", desc: "Generating bias assessment", icon: <CheckCircle size={20} /> }
];

const AgentPipeline = ({ currentStep, fileName }) => {
  return (
    <div className="glass-panel" style={{ marginBottom: "2rem" }}>
      <h2>Processing — {fileName}</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '1rem' }}>
        Running multi-agent evaluation pipeline
      </p>
      {currentStep === 0 && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(139, 92, 246, 0.1)', borderRadius: '8px', border: '1px solid rgba(139, 92, 246, 0.2)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div className="animate-spin" style={{ width: '16px', height: '16px', border: '2px solid var(--primary)', borderTopColor: 'transparent', borderRadius: '50%' }}></div>
          <span style={{ fontSize: '0.85rem', color: 'var(--primary)' }}>Waking up server... (This may take up to 30s on free hosting)</span>
        </div>
      )}
      <div className="progress-container">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={`agent-step ${currentStep === idx ? 'active animate-pulse' : ''} ${currentStep > idx ? 'completed' : ''}`}
            role="listitem"
            aria-label={`${step.title}: ${currentStep > idx ? 'completed' : currentStep === idx ? 'in progress' : 'pending'}`}
          >
            <div className="step-icon">
              {currentStep > idx ? <Check color="var(--green)" size={20} /> : step.icon}
            </div>
            <div className="step-content">
              <h4>{step.title}</h4>
              <p>{step.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentPipeline;
