import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, FileText, Globe, Zap } from 'lucide-react';
import PDFUploader from './PDFUploader';
import ChatInput from './ChatInput';

export default function HomeView({ onUploadSuccess }) {
  const [input, setInput] = useState('');
  const navigate = useNavigate();

  const handleInitialChat = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    // Créer un nouvel ID de chat et naviguer vers lui avec le message en state
    const newChatId = crypto.randomUUID();
    navigate(`/c/${newChatId}`, { state: { initialMessage: input.trim() } });
  };

  return (
    <div className="chat-container home-view" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="home-content" style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        padding: '2rem',
        gap: '3rem',
        maxWidth: '1000px',
        margin: '0 auto',
        width: '100%'
      }}>
        <div className="hero-section" style={{ textAlign: 'center' }}>
          <div className="hero-icon" style={{ 
            background: 'var(--accent-primary)', 
            width: '60px', 
            height: '60px', 
            borderRadius: '16px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            margin: '0 auto 1.5rem',
            boxShadow: '0 8px 16px rgba(59, 130, 246, 0.3)'
          }}>
            <Sparkles size={32} color="white" />
          </div>
          <h1 style={{ fontSize: '3.5rem', fontWeight: 800, marginBottom: '1rem', letterSpacing: '-0.02em', background: 'linear-gradient(to bottom right, var(--text-main) 30%, var(--text-muted) 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            Comment puis-je vous aider ?
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto' }}>
            Posez une question pour commencer une recherche, ou uploadez des documents pour une analyse approfondie.
          </p>
        </div>

        <div className="upload-container-home" style={{ 
          width: '100%', 
          maxWidth: '800px',
          padding: '2rem', 
          background: 'var(--bg-secondary)', 
          borderRadius: '2rem',
          border: '1px solid var(--border-color)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 20px 40px var(--shadow-color)'
        }}>
          <PDFUploader onUploadSuccess={onUploadSuccess} />
        </div>

        <div className="features-grid" style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '1.5rem',
          width: '100%',
          maxWidth: '800px'
        }}>
          <div className="feature-card" style={{ padding: '1.5rem', borderRadius: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
            <FileText size={20} color="var(--accent-primary)" style={{ marginBottom: '0.75rem' }} />
            <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Analyse de PDF</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Multi-fichiers, extraction intelligente.</p>
          </div>
          <div className="feature-card" style={{ padding: '1.5rem', borderRadius: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
            <Globe size={20} color="var(--accent-primary)" style={{ marginBottom: '0.75rem' }} />
            <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Recherche Web</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Agents autonomes pour trouver l'info.</p>
          </div>
          <div className="feature-card" style={{ padding: '1.5rem', borderRadius: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
            <Zap size={20} color="var(--accent-primary)" style={{ marginBottom: '0.75rem' }} />
            <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Groq LPU™</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Vitesse de réponse ultra-rapide.</p>
          </div>
        </div>
      </div>

      <ChatInput 
        input={input} 
        setInput={setInput} 
        onSubmit={handleInitialChat} 
        placeholder="Posez votre question pour commencer..." 
      />
    </div>
  );
}
