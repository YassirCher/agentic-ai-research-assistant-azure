import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, AlertCircle } from 'lucide-react';

export default function AgentTraceViewer({ steps = [], totalTokens = 0, isLive = false }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="trace-container">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="trace-header-btn"
      >
        <div className="trace-header-left">
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span>
            Thought Process
            <span className="trace-badge">
              {steps.length} {steps.length > 1 ? 'étapes' : 'étape'}
            </span>
            {isLive && (
              <span className="trace-badge trace-live-badge">
                En cours...
              </span>
            )}
            {totalTokens > 0 && (
              <span className="trace-badge" style={{ backgroundColor: 'rgba(var(--accent-primary), 0.05)', color: 'var(--text-muted)', borderStyle: 'dashed' }}>
                ⚡ {totalTokens} tokens
              </span>
            )}
          </span>
        </div>
      </button>
      
      {isOpen && (
        <div className="trace-content">
          <div className="trace-timeline">
            {steps.map((step, index) => {
              const isFallback = step.detail && (step.detail.toLowerCase().includes('échec') || step.detail?.toLowerCase().includes('hallucination'));
              
              return (
                <div key={index} className="trace-step">
                  <span className={`trace-dot ${isFallback ? 'fallback' : ''}`}>
                    {step.icon ? (
                      <span style={{ fontSize: '0.75rem' }}>{step.icon}</span>
                    ) : (
                      isFallback ? <AlertCircle size={10} color="#f59e0b" /> : <CheckCircle2 size={10} color="var(--accent-primary)" />
                    )}
                  </span>
                  
                  <div className="flex flex-col">
                    <div className="flex items-center justify-between">
                      <span className="trace-step-agent">
                        {step.agent}
                      </span>
                      {step.tokens > 0 && (
                        <span className="token-badge">
                          {step.tokens} tokens
                        </span>
                      )}
                    </div>
                    <h4 className="trace-step-action">
                      {step.action}
                    </h4>
                    {step.detail && (
                      <p className={`trace-step-detail ${isFallback ? 'fallback' : ''}`}>
                        {step.detail}
                      </p>
                    )}

                    {(step.prompt || step.response) && (
                      <div className="technical-details">
                        <details>
                          <summary>
                            Détails Techniques
                          </summary>
                          <div className="technical-details-box">
                            {step.prompt && (
                              <div>
                                <div className="tech-detail-label">PROMPT AGENT:</div>
                                <div className="tech-detail-content">{step.prompt}</div>
                              </div>
                            )}
                            {step.response && (
                              <div>
                                <div className="tech-detail-label">SORTIE / RAISONNEMENT:</div>
                                <div className="tech-detail-content">{step.response}</div>
                              </div>
                            )}
                          </div>
                        </details>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
