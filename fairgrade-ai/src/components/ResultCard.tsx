import React, { useState } from 'react';
import { RotateCcw, AlertTriangle, Clock, CheckCircle, Edit3, ShieldCheck } from 'lucide-react';
import type { ResultCardProps, EvaluationReport } from '../types';

/**
 * ResultCard — Displays evaluation results with Human-in-the-Loop controls.
 * Teachers can Accept or Override AI grades (Responsible AI pattern).
 */

interface RenderExplanationProps {
  explanation: string;
}

const RenderExplanation: React.FC<RenderExplanationProps> = ({ explanation }) => {
  if (!explanation) return <span>Waiting for AI pipeline...</span>;

  const isQuotaExhausted = explanation.startsWith('QUOTA_EXHAUSTED:');
  const isEvalFailed = explanation.startsWith('Evaluation failed:');

  if (isQuotaExhausted) {
    return (
      <div style={{
        background: 'rgba(255, 152, 0, 0.08)',
        border: '1px solid rgba(255, 152, 0, 0.3)',
        borderRadius: '8px',
        padding: '0.85rem 1rem',
        display: 'flex',
        gap: '0.65rem',
        alignItems: 'flex-start',
      }}>
        <AlertTriangle size={18} style={{ color: '#ff9800', flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.85rem', lineHeight: '1.5' }}>
          <strong style={{ color: '#ff9800' }}>API Quota Exhausted</strong>
          <p style={{ margin: '0.4rem 0 0', color: 'var(--text-muted)' }}>
            Your Gemini API free tier daily quota has been exceeded.
          </p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.1rem', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            <li style={{ marginBottom: '0.2rem' }}>
              <Clock size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
              Wait for the quota to reset (~24 hours)
            </li>
            <li style={{ marginBottom: '0.2rem' }}>Upgrade to a paid plan at <a href="https://ai.google.dev/pricing" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)' }}>ai.google.dev/pricing</a></li>
            <li>Use a different API key in <code style={{ fontSize: '0.8rem' }}>.env</code></li>
          </ul>
        </div>
      </div>
    );
  }

  if (isEvalFailed) {
    const errorDetail = explanation.replace('Evaluation failed: ', '');
    return (
      <div style={{
        background: 'rgba(244, 67, 54, 0.06)',
        border: '1px solid rgba(244, 67, 54, 0.2)',
        borderRadius: '8px',
        padding: '0.85rem 1rem',
        display: 'flex',
        gap: '0.65rem',
        alignItems: 'flex-start',
      }}>
        <AlertTriangle size={18} style={{ color: 'var(--red)', flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.85rem', lineHeight: '1.5' }}>
          <strong style={{ color: 'var(--red)' }}>Evaluation Failed</strong>
          <p style={{ margin: '0.4rem 0 0', color: 'var(--text-muted)', wordBreak: 'break-word' }}>
            {errorDetail.length > 200 ? errorDetail.substring(0, 200) + '…' : errorDetail}
          </p>
        </div>
      </div>
    );
  }

  return <span>{explanation}</span>;
};

const ResultCard: React.FC<ResultCardProps> = ({ result, studentId, onRetry, onVerify, truncateName }) => {
  const { fileName, data: report, error } = result;
  const displayName = truncateName(fileName);

  // Human-in-the-Loop state
  const [showOverride, setShowOverride] = useState(false);
  const [overrideScore, setOverrideScore] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [verified, setVerified] = useState(report?.verified || false);
  const [verifyAction, setVerifyAction] = useState<'accept_ai' | 'override' | null>(null);

  const handleAcceptAi = (): void => {
    if (!report) return;
    setVerified(true);
    setVerifyAction('accept_ai');
    if (onVerify) {
      onVerify(fileName, {
        action: 'accept_ai',
        finalScore: report.evaluation.aiScore,
        originalAiScore: report.evaluation.aiScore,
        originalTeacherScore: report.evaluation.teacherScore,
      });
    }
  };

  const handleOverrideSubmit = (): void => {
    if (!report) return;
    const score = parseFloat(overrideScore);
    if (isNaN(score) || score < 0 || score > 10) return;
    setVerified(true);
    setVerifyAction('override');
    setShowOverride(false);
    if (onVerify) {
      onVerify(fileName, {
        action: 'override',
        finalScore: score,
        originalAiScore: report.evaluation.aiScore,
        originalTeacherScore: report.evaluation.teacherScore,
        overrideReason: overrideReason || null,
      });
    }
  };

  if (error) {
    return (
      <div className="result-card" style={{ borderLeft: '3px solid var(--red)', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>{displayName} — Failed</h3>
          {onRetry && (
            <button className="retry-btn" onClick={() => onRetry(fileName)} aria-label={`Retry evaluation for ${fileName}`} title="Retry this file">
              <RotateCcw size={14} /> Retry
            </button>
          )}
        </div>
        <p style={{ color: 'var(--red)', fontSize: '0.9rem' }}>{error}</p>
      </div>
    );
  }

  if (!report) return null;

  const isQuotaIssue = report.evaluation.explanation?.startsWith('QUOTA_EXHAUSTED:') ||
                        report.evaluation.explanation?.startsWith('Evaluation failed:');

  return (
    <div className="result-card" style={{ animation: "fadeInUp 0.5s ease-out", marginBottom: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <h3 style={{ marginBottom: 0 }}>{displayName}</h3>
        {verified && (
          <span className="verified-badge">
            <ShieldCheck size={14} /> Verified by Teacher
          </span>
        )}
      </div>

      <div className="score-display">
        <div className="score-item">
          <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Student ID</p>
          <p style={{ fontSize: '1.1rem', fontWeight: 'bold', marginTop: '0.4rem', color: 'var(--text-main)' }}>{studentId || 'N/A'}</p>
        </div>
        <div className="score-item">
          <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Teacher Score</p>
          <p className="score-value">{report.evaluation.teacherScore}<span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>/10</span></p>
        </div>
        <div className="score-item">
          <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>AI Score</p>
          <p className="score-value" style={{ color: isQuotaIssue ? 'var(--text-muted)' : 'var(--primary)' }}>
            {isQuotaIssue ? '—' : report.evaluation.aiScore}
            {!isQuotaIssue && <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>/10</span>}
          </p>
          {!isQuotaIssue && report.evaluation.confidenceScore && (
            <div style={{ marginTop: '0.2rem', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
               <span>Confidence: {(report.evaluation.confidenceScore * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
        <div className="score-item" style={{ marginLeft: "auto" }}>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Bias Indicator</p>
          {isQuotaIssue ? (
            <div className="bias-level" style={{ background: 'rgba(158,158,158,0.15)', color: 'var(--text-muted)' }}>
              N/A
            </div>
          ) : (
            <>
              <div className={`bias-level bias-${report.bias.level}`}>
                {report.bias.level} Risk
              </div>
              <p style={{ marginTop: '0.4rem', fontWeight: 'bold', fontSize: '0.85rem' }} className={`status-${report.bias.status}`}>&rarr; {report.bias.status}</p>
              {report.bias.biasScorePercentage !== undefined && (
                <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--text-muted)' }} title={report.bias.formulaUsed}>
                  Bias Score: <strong style={{ color: 'var(--text-main)' }}>{report.bias.biasScorePercentage}%</strong>
                  {report.bias.confidenceWeight && (
                    <div style={{ marginTop: '0.2rem', fontSize: '0.65rem', opacity: 0.8 }}>
                      CW: {report.bias.confidenceWeight} · CF: {report.bias.completenessFactor}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Human-in-the-Loop: Accept / Override ── */}
      {!isQuotaIssue && !verified && (
        <div className="hitl-actions">
          <div className="hitl-label">
            <ShieldCheck size={14} />
            <span>Teacher Verification <em>(Responsible AI)</em></span>
          </div>
          <div className="hitl-buttons">
            <button className="hitl-accept" onClick={handleAcceptAi} id={`accept-${fileName}`}>
              <CheckCircle size={14} /> Accept AI Score
            </button>
            <button className="hitl-override" onClick={() => setShowOverride(!showOverride)} id={`override-${fileName}`}>
              <Edit3 size={14} /> Override Score
            </button>
          </div>
          {showOverride && (
            <div className="hitl-override-form">
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  type="number" min="0" max="10" step="0.5"
                  placeholder="Final score (0-10)"
                  value={overrideScore}
                  onChange={e => setOverrideScore(e.target.value)}
                  className="hitl-score-input"
                  id={`override-score-${fileName}`}
                />
                <button className="hitl-submit" onClick={handleOverrideSubmit} disabled={!overrideScore}>
                  Confirm
                </button>
              </div>
              <input
                type="text"
                placeholder="Reason for override (optional)"
                value={overrideReason}
                onChange={e => setOverrideReason(e.target.value)}
                className="hitl-reason-input"
                id={`override-reason-${fileName}`}
              />
            </div>
          )}
        </div>
      )}

      {verified && verifyAction && (
        <div className={`hitl-verified-banner ${verifyAction === 'override' ? 'hitl-overridden' : ''}`}>
          <ShieldCheck size={16} />
          <span>
            {verifyAction === 'accept_ai'
              ? `Teacher accepted AI score of ${report.evaluation.aiScore}/10`
              : `Teacher overrode to ${overrideScore || report.evaluation.aiScore}/10${overrideReason ? ` — "${overrideReason}"` : ''}`
            }
          </span>
        </div>
      )}

      {/* Pipeline warnings */}
      {report.pipelineWarnings && report.pipelineWarnings.length > 0 && (
        <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.85rem', borderRadius: '10px', background: 'rgba(255, 152, 0, 0.06)', border: '1px solid rgba(255, 152, 0, 0.15)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <strong style={{ color: '#ff9800' }}>⚠ Partial Result:</strong>{' '}
          {report.pipelineWarnings.map(w => w.agent).join(', ')} had issues but other agents succeeded.
        </div>
      )}

      <div className="results-grid">
        <div>
          <h4>Anonymized Trajectory</h4>
          <div className="text-box" style={{ minHeight: '110px', maxHeight: '170px', overflowY: 'auto' }}>
            {report.anonymizedText || "No text available."}
          </div>
        </div>
        <div>
          <h4>AI Reasoning Process</h4>
          <div className="text-box" style={{ minHeight: '110px', maxHeight: '170px', overflowY: 'auto' }}>
            <RenderExplanation explanation={report.evaluation.explanation} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultCard;
