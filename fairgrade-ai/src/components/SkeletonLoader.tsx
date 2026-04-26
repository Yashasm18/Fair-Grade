import React from 'react';

/**
 * SkeletonLoader — Animated placeholder cards shown while results are loading.
 * Prevents layout shift and gives users a visual indication that content is coming.
 */

interface SkeletonBlockProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  style?: React.CSSProperties;
}

const SkeletonBlock: React.FC<SkeletonBlockProps> = ({
  width = '100%',
  height = '1rem',
  borderRadius = '6px',
  style = {},
}) => (
  <div
    aria-hidden="true"
    style={{
      width,
      height,
      borderRadius,
      background: 'linear-gradient(90deg, var(--skeleton-base, rgba(255,255,255,0.06)) 25%, var(--skeleton-shine, rgba(255,255,255,0.12)) 50%, var(--skeleton-base, rgba(255,255,255,0.06)) 75%)',
      backgroundSize: '200% 100%',
      animation: 'skeleton-shimmer 1.5s infinite',
      ...style,
    }}
  />
);

/** A single skeleton card that matches the ResultCard layout */
const ResultCardSkeleton: React.FC = () => (
  <div
    aria-label="Loading result..."
    className="glass-panel"
    style={{ marginBottom: '1.25rem', padding: '1.5rem' }}
  >
    {/* Header row */}
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
      <SkeletonBlock width="40%" height="1.1rem" />
      <SkeletonBlock width="20%" height="1.1rem" />
    </div>

    {/* Score row */}
    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem' }}>
      <SkeletonBlock width="30%" height="4rem" borderRadius="12px" />
      <SkeletonBlock width="30%" height="4rem" borderRadius="12px" />
      <SkeletonBlock width="30%" height="4rem" borderRadius="12px" />
    </div>

    {/* Explanation lines */}
    <SkeletonBlock width="100%" height="0.85rem" style={{ marginBottom: '0.5rem' }} />
    <SkeletonBlock width="88%" height="0.85rem" style={{ marginBottom: '0.5rem' }} />
    <SkeletonBlock width="72%" height="0.85rem" style={{ marginBottom: '1.25rem' }} />

    {/* Bias badge */}
    <SkeletonBlock width="50%" height="2.5rem" borderRadius="10px" />
  </div>
);

interface SkeletonLoaderProps {
  /** Number of skeleton cards to show */
  count?: number;
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ count = 1 }) => (
  <>
    {/* Inject keyframe if not already in stylesheet */}
    <style>{`
      @keyframes skeleton-shimmer {
        0%   { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
    `}</style>
    {Array.from({ length: count }).map((_, i) => (
      <ResultCardSkeleton key={i} />
    ))}
  </>
);

export default SkeletonLoader;
