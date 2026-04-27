import React, { useEffect, useState, useRef } from 'react';

/**
 * AIThoughtsStream — Animated "AI thinking" feed shown while the pipeline runs.
 * Cycles through FairGrade-specific thoughts with a typewriter + fade effect,
 * giving the user a sense of real AI work happening instead of a blank skeleton.
 */

const THOUGHTS: string[] = [
  "Reading handwriting patterns from the answer sheet…",
  "Identifying key concepts in the student's response…",
  "Checking answer completeness against the model solution…",
  "Applying Gemini 2.5 Pro vision for OCR extraction…",
  "Scanning for personally identifiable information to redact…",
  "Anonymizing student data before evaluation…",
  "Grading objectively — no name, no bias…",
  "Measuring semantic similarity to the expected answer…",
  "Calculating confidence score for the AI evaluation…",
  "Comparing AI score with teacher-provided benchmark…",
  "Computing gap between AI score and teacher score…",
  "Applying completeness factor to the bias formula…",
  "Checking if the student was undergraded or overgraded…",
  "Detecting potential implicit bias in the grading gap…",
  "Generating detailed bias explainability report…",
  "Preparing Human-in-the-Loop verification data for teacher…",
  "Ensuring UN SDG 4 — Quality Education — for every student…",
  "Building audit trail for this evaluation decision…",
];

interface TypewriterProps {
  text: string;
  speed?: number;
  onDone?: () => void;
}

const Typewriter: React.FC<TypewriterProps> = ({ text, speed = 28, onDone }) => {
  const [displayed, setDisplayed] = useState('');
  const idxRef = useRef(0);
  const timRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    idxRef.current = 0;

    const type = () => {
      if (idxRef.current < text.length) {
        setDisplayed(text.slice(0, idxRef.current + 1));
        idxRef.current += 1;
        timRef.current = setTimeout(type, speed);
      } else {
        onDone?.();
      }
    };

    // Reset display and start typing after a tiny delay (avoids sync setState-in-effect)
    timRef.current = setTimeout(() => {
      setDisplayed('');
      type();
    }, 80);
    return () => { if (timRef.current) clearTimeout(timRef.current); };
  }, [text, speed, onDone]);

  return (
    <span>
      {displayed}
      <span style={{
        display: 'inline-block',
        width: '2px',
        height: '1em',
        background: 'var(--primary)',
        marginLeft: '2px',
        verticalAlign: 'text-bottom',
        animation: 'blink-cursor 0.7s step-end infinite',
        borderRadius: '1px',
      }} />
    </span>
  );
};

const AIThoughtsStream: React.FC = () => {
  const [currentIdx, setCurrentIdx] = useState(() => Math.floor(Math.random() * THOUGHTS.length));
  const [visible, setVisible] = useState(true);
  const [history, setHistory] = useState<string[]>([]);

  const advance = () => {
    const current = THOUGHTS[currentIdx];
    setHistory(prev => [current, ...prev].slice(0, 4)); // keep last 4
    setVisible(false);
    setTimeout(() => {
      setCurrentIdx(prev => (prev + 1) % THOUGHTS.length);
      setVisible(true);
    }, 400);
  };

  return (
    <div style={{
      background: 'var(--panel-bg)',
      border: '1px solid var(--panel-border)',
      borderRadius: '20px',
      padding: '1.5rem 1.75rem',
      marginBottom: '1.25rem',
      backdropFilter: 'blur(24px)',
      boxShadow: 'var(--shadow-md)',
      minHeight: '200px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
        <div style={{
          width: 10, height: 10, borderRadius: '50%',
          background: 'var(--primary)',
          boxShadow: '0 0 8px rgba(139,92,246,0.6)',
          animation: 'pulse-dot 1.2s ease-in-out infinite',
        }} />
        <span style={{
          fontSize: '0.72rem', fontWeight: 700, letterSpacing: '1.5px',
          textTransform: 'uppercase', color: 'var(--accent)',
        }}>
          AI Pipeline — Live Thoughts
        </span>
      </div>

      {/* Current thought — typewriter */}
      <div style={{
        fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-main)',
        lineHeight: 1.6, minHeight: '1.6em',
        opacity: visible ? 1 : 0,
        transition: 'opacity 0.35s ease',
        marginBottom: '1.25rem',
      }}>
        {visible && (
          <Typewriter key={currentIdx} text={THOUGHTS[currentIdx]} speed={24} onDone={() => {
            // Linger 1.8s then advance
            setTimeout(advance, 1800);
          }} />
        )}
      </div>

      {/* History feed */}
      {history.length > 0 && (
        <div style={{ borderTop: '1px solid var(--panel-border)', paddingTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {history.map((t, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: '0.6rem',
              opacity: Math.max(0.15, 0.55 - i * 0.13),
              fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5,
              transition: 'opacity 0.4s ease',
            }}>
              <span style={{ color: 'var(--green)', flexShrink: 0, marginTop: '2px', fontSize: '0.7rem' }}>✓</span>
              <span>{t}</span>
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes pulse-dot {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.4); opacity: 0.7; }
        }
        @keyframes blink-cursor {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
};

export default AIThoughtsStream;
