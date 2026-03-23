import React, { useEffect, useState } from 'react';
import { Plus, MessageSquare, Trash2, AlertTriangle } from 'lucide-react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import ThemeSelector from './ThemeSelector';
import LogoMark from './LogoMark';
import { apiFetch } from '../lib/apiClient';

export default function Sidebar({ theme, setTheme, isCollapsed, setIsCollapsed, refreshSignal }) {
  const [chats, setChats] = useState([]);
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, chatId: null, chatTitle: '' });
  const [isDeleting, setIsDeleting] = useState(false);
  const { chatId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    fetchChats();
  }, [refreshSignal]);

  const fetchChats = async () => {
    try {
      const res = await apiFetch('/api/chats');
      const data = await res.json();
      if (Array.isArray(data)) {
        setChats(data);
      } else {
        console.error("Format de données invalide pour les chats:", data);
        setChats([]);
      }
    } catch (err) {
      console.error("Erreur lors de la récupération des chats:", err);
    }
  };

  const openDeleteModal = (id, title, e) => {
    e.preventDefault();
    e.stopPropagation();
    setDeleteModal({ isOpen: true, chatId: id, chatTitle: title });
  };

  const closeDeleteModal = () => {
    if (isDeleting) return;
    setDeleteModal({ isOpen: false, chatId: null, chatTitle: '' });
  };

  const confirmDeleteChat = async () => {
    if (!deleteModal.chatId) return;

    setIsDeleting(true);
    try {
      await apiFetch(`/api/chats/${deleteModal.chatId}`, { method: 'DELETE' });
      setChats((prev) => prev.filter((c) => c.id !== deleteModal.chatId));
      if (chatId === deleteModal.chatId) navigate('/');
      closeDeleteModal();
    } catch (err) {
      console.error("Erreur lors de la suppression:", err);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <LogoMark />
          <button className="new-chat-btn" onClick={() => navigate('/')}>
            <Plus size={18} />
            Nouveau Chat
          </button>
        </div>

        <div className="chat-list">
          {chats.map(chat => (
            <Link 
              key={chat.id} 
              to={`/c/${chat.id}`} 
              className={`chat-item ${chatId === chat.id ? 'active' : ''}`}
            >
              <div className="chat-item-content">
                <MessageSquare size={20} className="chat-item-icon" />
                <span className="chat-item-title">{chat.title}</span>
              </div>
              <button 
                className="delete-chat-btn" 
                onClick={(e) => openDeleteModal(chat.id, chat.title, e)}
                title="Supprimer la conversation"
              >
                <Trash2 size={14} />
              </button>
            </Link>
          ))}
        </div>

        <div className="sidebar-footer" style={{ padding: '1rem' }}>
          <ThemeSelector currentThemeId={theme} setTheme={setTheme} />
        </div>
      </aside>

      {deleteModal.isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(2, 6, 23, 0.55)',
            backdropFilter: 'blur(8px)',
          }}
          onClick={closeDeleteModal}
        >
          <div
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
            style={{
              width: 'min(92vw, 520px)',
              borderRadius: '1rem',
              background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
              padding: '1.5rem',
              boxShadow: '0 30px 80px rgba(2, 6, 23, 0.45)',
              border: '1px solid rgba(15, 23, 42, 0.08)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', gap: '0.9rem', alignItems: 'flex-start' }}>
              <div
                style={{
                  width: '2.4rem',
                  height: '2.4rem',
                  borderRadius: '999px',
                  background: 'rgba(239, 68, 68, 0.12)',
                  color: '#dc2626',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <AlertTriangle size={20} />
              </div>
              <div>
                <h3 style={{ color: '#0f172a', fontSize: '1.05rem', fontWeight: 800 }}>
                  Supprimer la conversation ?
                </h3>
                <p style={{ color: '#475569', marginTop: '0.45rem', lineHeight: 1.5, fontSize: '0.92rem' }}>
                  Cette action est irreversible et supprimera egalement les documents associes.
                </p>
                {deleteModal.chatTitle && (
                  <p style={{ color: '#0f172a', marginTop: '0.4rem', fontSize: '0.86rem', fontWeight: 600 }}>
                    {deleteModal.chatTitle}
                  </p>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.35rem' }}>
              <button
                type="button"
                onClick={closeDeleteModal}
                disabled={isDeleting}
                style={{
                  border: '1px solid rgba(15, 23, 42, 0.15)',
                  borderRadius: '0.7rem',
                  background: '#ffffff',
                  color: '#0f172a',
                  fontWeight: 700,
                  padding: '0.62rem 0.92rem',
                  cursor: isDeleting ? 'not-allowed' : 'pointer',
                  opacity: isDeleting ? 0.7 : 1,
                }}
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={confirmDeleteChat}
                disabled={isDeleting}
                style={{
                  border: 'none',
                  borderRadius: '0.7rem',
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  color: '#ffffff',
                  fontWeight: 800,
                  padding: '0.62rem 0.96rem',
                  cursor: isDeleting ? 'not-allowed' : 'pointer',
                  opacity: isDeleting ? 0.8 : 1,
                }}
              >
                {isDeleting ? 'Suppression...' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
