import React from 'react';
import { GraduationCap, Heart, Sparkles } from 'lucide-react';

/**
 * Footer — SDG 4 badge, Gemini attribution, team info.
 */
const Footer: React.FC = () => {
  return (
    <footer className="app-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <GraduationCap size={18} />
          <span>FairGrade AI</span>
        </div>

        <div className="footer-badges">
          <span className="sdg-badge" title="UN Sustainable Development Goal 4: Quality Education">
            <span className="sdg-number">SDG 4</span>
            Quality Education
          </span>
          <span className="gemini-badge">
            <Sparkles size={13} />
            Built with Gemini
          </span>
        </div>

        <div className="footer-meta">
          <span>Google Solution Challenge 2026</span>
          <span className="footer-divider">·</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            Made with <Heart size={12} color="#ec4899" fill="#ec4899" /> by Team VEKTOR ⚡
          </span>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
