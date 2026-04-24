import React from 'react';
import { Moon, Sun } from 'lucide-react';
import type { DarkModeToggleProps } from '../types';

/**
 * DarkModeToggle — Renders a toggle pill switch for dark/light theme.
 * Persists choice in localStorage and sets data-theme on <html>.
 */
const DarkModeToggle: React.FC<DarkModeToggleProps> = ({ isDark, onToggle }) => {
  return (
    <button
      className="dark-mode-toggle"
      onClick={onToggle}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Light mode' : 'Dark mode'}
    >
      <span className={`toggle-track ${isDark ? 'dark' : ''}`}>
        <span className="toggle-thumb">
          {isDark ? <Moon size={14} /> : <Sun size={14} />}
        </span>
      </span>
    </button>
  );
};

export default DarkModeToggle;
