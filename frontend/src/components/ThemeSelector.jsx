import React, { useEffect, useState, useRef } from 'react';
import { Moon, Sun, Droplets, Zap, Trees, ChevronUp, Check } from 'lucide-react';

const themes = [
  { id: 'dark', icon: Moon, label: 'Sombre Classique' },
  { id: 'light', icon: Sun, label: 'Clair Épuré' },
  { id: 'midnight', icon: Droplets, label: 'Océan Profond' },
  { id: 'cyberpunk', icon: Zap, label: 'Néon Cyber' },
  { id: 'forest', icon: Trees, label: 'Forêt Émeraude' }
];

export default function ThemeSelector({ currentThemeId, setTheme }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentTheme = themes.find(t => t.id === currentThemeId) || themes[0];

  useEffect(() => {
    console.log("ThemeSelector rendering with:", currentThemeId, "Themes available:", themes.length);
    document.documentElement.setAttribute('data-theme', currentThemeId);
    localStorage.setItem('theme', currentThemeId);
  }, [currentThemeId]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const Icon = currentTheme.icon;

  return (
    <div className="theme-selector-container" ref={dropdownRef}>
      
      {isOpen && (
        <div className="theme-dropdown">
          {themes.map((t) => {
            const TIcon = t.icon;
            const isActive = t.id === currentThemeId;
            return (
              <button
                key={t.id}
                onClick={() => {
                  setTheme(t.id);
                  setIsOpen(false);
                }}
                className={`theme-option ${isActive ? 'active' : ''}`}
              >
                <div className="theme-option-info">
                  <TIcon size={16} />
                  {t.label}
                </div>
                {isActive && <Check size={16} />}
              </button>
            );
          })}
        </div>
      )}

      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="theme-toggle-btn"
        title="Ouvrir le menu des thèmes"
      >
        <div className="theme-btn-content">
          <div className="theme-icon-wrapper">
            <Icon size={18} strokeWidth={2.5} />
          </div>
          <div className="theme-text-info">
            <span className="theme-label-top">Thème Actif</span>
            <span className="theme-current-name">{currentTheme.label}</span>
          </div>
        </div>
        
        <ChevronUp 
          size={18} 
          className="sparkle-icon"
          style={{ transform: isOpen ? 'rotate(180deg)' : 'none' }}
        />
      </button>
    </div>
  );
}
