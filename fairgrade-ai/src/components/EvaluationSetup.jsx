import React, { useState } from 'react';
import { Upload, Shield, Loader2, Sparkles, X, BookOpen, Save, Trash2 } from 'lucide-react';

/**
 * Question presets saved in localStorage.
 */
const PRESETS_KEY = 'fairgrade_question_presets';

const loadPresets = () => {
  try {
    return JSON.parse(localStorage.getItem(PRESETS_KEY) || '[]');
  } catch { return []; }
};

const savePresets = (presets) => {
  localStorage.setItem(PRESETS_KEY, JSON.stringify(presets));
};

/**
 * EvaluationSetup — Left sidebar with scoring, question bank, file upload, and run button.
 */
const EvaluationSetup = ({
  teacherScore,
  setTeacherScore,
  questionContext,
  setQuestionContext,
  files,
  studentIds,
  handleStudentIdChange,
  handleChange,
  handleDrag,
  handleDrop,
  dragActive,
  removeFile,
  isProcessing,
  currentFileIndex,
  runAgents,
  globalError,
  truncateName,
}) => {
  const [presets, setPresets] = useState(loadPresets());
  const [presetName, setPresetName] = useState('');
  const [showPresets, setShowPresets] = useState(false);

  const handleSavePreset = () => {
    if (!presetName.trim() || !questionContext.trim()) return;
    const updated = [...presets, { name: presetName.trim(), context: questionContext }];
    setPresets(updated);
    savePresets(updated);
    setPresetName('');
  };

  const handleLoadPreset = (preset) => {
    setQuestionContext(preset.context);
    setShowPresets(false);
  };

  const handleDeletePreset = (idx) => {
    const updated = presets.filter((_, i) => i !== idx);
    setPresets(updated);
    savePresets(updated);
  };

  return (
    <div className="glass-panel">
      <h2>Evaluation Setup</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '1.5rem' }}>
        Configure scoring parameters and upload answer sheets
      </p>

      <div className="section-label">Scoring</div>

      <div className="input-group">
        <label htmlFor="teacher-score">Teacher's Score (out of 10)</label>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input
            id="teacher-score"
            type="number"
            min="0"
            max="10"
            value={teacherScore}
            onChange={e => setTeacherScore(e.target.value)}
            placeholder="e.g. 7"
            style={{ width: '80px', textAlign: 'center' }}
            aria-label="Teacher score out of 10"
          />
          <input
            type="range"
            className="score-slider"
            min="0"
            max="10"
            step="0.5"
            value={teacherScore || 0}
            onChange={e => setTeacherScore(e.target.value)}
            aria-label="Teacher score slider"
          />
        </div>
      </div>

      <div className="input-group">
        <label htmlFor="question-context">
          Question & Model Answer
          <button
            className="preset-toggle-btn"
            onClick={() => setShowPresets(!showPresets)}
            title="Question Bank"
            type="button"
          >
            <BookOpen size={14} />
            Presets {presets.length > 0 && `(${presets.length})`}
          </button>
        </label>

        {showPresets && (
          <div className="preset-panel">
            {presets.length === 0 ? (
              <p className="preset-empty">No saved presets yet. Type a question below and save it.</p>
            ) : (
              <div className="preset-list">
                {presets.map((p, idx) => (
                  <div key={idx} className="preset-item">
                    <button
                      className="preset-load-btn"
                      onClick={() => handleLoadPreset(p)}
                      title={p.context.substring(0, 100)}
                    >
                      {p.name}
                    </button>
                    <button
                      className="preset-delete-btn"
                      onClick={() => handleDeletePreset(idx)}
                      title="Delete preset"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="preset-save-row">
              <input
                type="text"
                placeholder="Preset name..."
                value={presetName}
                onChange={e => setPresetName(e.target.value)}
                className="preset-name-input"
              />
              <button
                className="preset-save-btn"
                onClick={handleSavePreset}
                disabled={!presetName.trim() || !questionContext.trim()}
                title="Save current question as preset"
              >
                <Save size={13} /> Save
              </button>
            </div>
          </div>
        )}

        <textarea
          id="question-context"
          value={questionContext}
          onChange={e => setQuestionContext(e.target.value)}
          placeholder="Paste the question and expected answer here to guide the AI..."
          rows={3}
          style={{
            width: '100%', padding: '0.75rem', borderRadius: '12px',
            background: 'var(--bg-input)', border: '1.5px solid var(--border-color)',
            color: 'var(--text-color)', resize: 'vertical', fontFamily: 'inherit'
          }}
          aria-label="Question and model answer context"
        />
      </div>

      <div className="section-label" style={{ marginTop: '0.5rem' }}>Upload</div>

      <div
        className={`uploader ${dragActive ? "drag-active" : ""}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-upload").click()}
        role="button"
        tabIndex={0}
        aria-label="Upload answer sheets. Drag and drop or click to browse."
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') document.getElementById("file-upload").click(); }}
      >
        <Upload size={28} />
        <p>{files.length > 0 ? `${files.length} file(s) selected` : "Drag & drop images/PDFs or click to browse"}</p>

        {files.length > 0 && (
          <div style={{ marginTop: '1rem', textAlign: 'left', width: '100%' }} onClick={e => e.stopPropagation()}>
            {files.map(f => (
              <div key={f.name} className="file-list-item">
                <span style={{ fontSize: '0.8rem', color: 'var(--text-main)', maxWidth: '130px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={f.name}>
                  {truncateName(f.name, 20)}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <input
                    type="text"
                    placeholder="Student ID"
                    value={studentIds[f.name] || ''}
                    onChange={e => handleStudentIdChange(f.name, e.target.value)}
                    style={{
                      padding: '0.35rem 0.5rem', borderRadius: '8px',
                      border: '1.5px solid var(--panel-border)',
                      background: 'var(--bg-input)', color: 'var(--text-main)',
                      fontSize: '0.75rem', width: '100px'
                    }}
                    aria-label={`Student ID for ${f.name}`}
                  />
                  <button
                    onClick={() => removeFile(f.name)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                    title="Remove file"
                    aria-label={`Remove ${f.name}`}
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        <input id="file-upload" type="file" multiple style={{ display: "none" }} onChange={handleChange} accept="image/*,application/pdf" />
      </div>

      <div className="security-badge">
        <Shield size={14} style={{ flexShrink: 0 }} />
        <span>API keys & grading are securely managed by the backend server.</span>
      </div>

      <button
        className="btn-primary"
        onClick={runAgents}
        disabled={isProcessing || files.length === 0 || teacherScore === ''}
        style={{ padding: '1rem', fontSize: '1rem', marginTop: '1.25rem' }}
        aria-label="Run agent evaluation pipeline"
      >
        {isProcessing ? (
          <><Loader2 className="animate-spin" size={18} /> Processing {currentFileIndex + 1} of {files.length}...</>
        ) : (
          <><Sparkles size={18} /> Run Agent Pipeline</>
        )}
      </button>

      {globalError && (
        <div role="alert" style={{
          color: "var(--red)", marginTop: "0.75rem", fontSize: '0.85rem',
          padding: '0.6rem 0.8rem', background: 'var(--red-bg)',
          borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.15)'
        }}>
          {globalError}
        </div>
      )}
    </div>
  );
};

export default EvaluationSetup;
