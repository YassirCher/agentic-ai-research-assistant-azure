import React from 'react';
import { Orbit, Sparkles } from 'lucide-react';

export default function LogoMark() {
  return (
    <div className="brand-pro" aria-label="Research AI">
      <div className="brand-mark" aria-hidden="true">
        <Orbit size={20} className="brand-main-icon" />
        <span className="brand-badge">
          <Sparkles size={10} />
        </span>
      </div>
      <div className="brand-text-wrap">
        <div className="brand-title">Research AI</div>
        <div className="brand-subtitle">Advanced Multi-Agent Research Assistant</div>
      </div>
    </div>
  );
}
