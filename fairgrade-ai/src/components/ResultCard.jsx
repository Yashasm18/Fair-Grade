import React from 'react';
import { RotateCcw, AlertTriangle, Clock } from 'lucide-react';

/**
 * ResultCard — Displays a single evaluation result with scores, bias, and retry.
 */

/** Detect and render quota/error explanations with a styled banner. */
const RenderExplanation = ({ explanation }) => {
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

const ResultCard = ({ result, studentId, onRetry, truncateName }) => {
  const { fileName, data: report, error } = result;
  const displayName = truncateName(fileName);

  if (error) {
    return (
      <div className="result-card" style={{ borderLeft: '3px solid var(--red)', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>{displayName} — Failed</h3>
          {onRetry && (
            <button
              className="retry-btn"
              onClick={() => onRetry(fileName)}
              aria-label={`Retry evaluation for ${fileName}`}
              title="Retry this file"
            >
              <RotateCcw size={14} />
              Retry
            </button>
          )}
        </div>
        <p style={{ color: 'var(--red)', fontSize: '0.9rem' }}>{error}</p>
      </div>
    );
  }

  const isQuotaIssue = report.evaluation.explanation?.startsWith('QUOTA_EXHAUSTED:') ||
                        report.evaluation.explanation?.startsWith('Evaluation failed:');

  return (
    <div className="result-card" style={{ animation: "fadeInUp 0.5s ease-out", marginBottom: '1.25rem' }}>
      <h3>{displayName}</h3>

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
            </>
          )}
        </div>
      </div>

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
