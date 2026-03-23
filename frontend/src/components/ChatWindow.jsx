import React, { useState, useRef, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { useParams, useLocation } from 'react-router-dom';
import CitationTag from './CitationTag';
import AgentTraceViewer from './AgentTraceViewer';
import ChatInput from './ChatInput';
import { apiFetch } from '../lib/apiClient';

export default function ChatWindow() {
  const { chatId } = useParams();
  const location = useLocation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const endOfMessagesRef = useRef(null);
  const uploadStatusUrl = chatId
    ? location.state?.uploadStatusUrl || sessionStorage.getItem(`uploadStatusUrl:${chatId}`)
    : null;

  // Gérer le message initial venant de la Home Page
  useEffect(() => {
    if (location.state?.initialMessage && chatId) {
      const msg = location.state.initialMessage;
      // Nettoyer le state pour éviter de renvoyer le msg au refresh
      window.history.replaceState({}, document.title);
      sendQuery(msg);
    }
  }, [chatId]);

  useEffect(() => {
    if (chatId) {
      fetchMessages();
    }
  }, [chatId]);

  useEffect(() => {
    if (!chatId || !uploadStatusUrl) {
      setUploadStatus(null);
      return;
    }

    let cancelled = false;
    let intervalId = null;

    const stopPolling = () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };

    const poll = async () => {
      try {
        const res = await apiFetch(uploadStatusUrl);
        if (!res.ok) {
          if (!cancelled) {
            setUploadStatus(null);
            if (res.status === 404) {
              sessionStorage.removeItem(`uploadStatusUrl:${chatId}`);
              stopPolling();
            }
          }
          return;
        }

        const data = await res.json();
        if (!cancelled) {
          setUploadStatus(data);
          if (data.status === 'ready' || data.status === 'failed') {
            sessionStorage.removeItem(`uploadStatusUrl:${chatId}`);
            stopPolling();
          }
        }
      } catch (_) {
        if (!cancelled) setUploadStatus(null);
      }
    };

    poll();
    intervalId = setInterval(poll, 2000);

    return () => {
      cancelled = true;
      stopPolling();
    };
  }, [chatId, uploadStatusUrl]);

  const fetchMessages = async () => {
    try {
      const res = await apiFetch(`/api/chats/${chatId}/messages`);
      if (res.ok) {
        const data = await res.json();
        if (data.length > 0) {
          setMessages(data);
        } else if (!location.state?.initialMessage) {
          setMessages([
            { role: 'ai', content: 'Conversation isolée créée. Posez votre première question sur les documents uploadés.' }
          ]);
        }
      }
    } catch (err) {
      console.error("Erreur historique:", err);
    }
  };

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const renderTextWithCitations = (text) => {
    const regex = /\[(.*?),\s*Page\s*(\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    
    text.replace(regex, (match, docName, pageNum, index) => {
      if (index > lastIndex) {
        parts.push(text.substring(lastIndex, index));
      }
      parts.push(<CitationTag key={index} source={docName} page={pageNum} />);
      lastIndex = index + match.length;
    });
    
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }
    
    return parts.length > 0 ? parts : text;
  };

  const sendQuery = async (queryText) => {
    if (loading || uploadStatus?.status === 'processing') return;
    const assistantMessageId = crypto.randomUUID();

    setMessages(prev => [
      ...prev,
      { role: 'user', content: queryText },
      {
        id: assistantMessageId,
        role: 'ai',
        content: 'Analyse en cours...',
        trace: [],
        metadata: { total_tokens: 0, loop_count: 0 },
        isStreaming: true,
      },
    ]);
    setLoading(true);

    try {
      const res = await apiFetch('/api/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: queryText,
          chat_id: chatId 
        })
      });

      if (!res.ok) throw new Error('API Error');
      if (!res.body) throw new Error('Stream indisponible');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamEnded = false;

      const updateAssistantMessage = (updater) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId ? updater(msg) : msg
          )
        );
      };

      while (!streamEnded) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        events.forEach((eventBlock) => {
          const dataLine = eventBlock
            .split('\n')
            .find((line) => line.startsWith('data: '));

          if (!dataLine) return;

          try {
            const payload = JSON.parse(dataLine.slice(6));

            if (payload.type === 'agent_step') {
              updateAssistantMessage((msg) => {
                const nextTrace = payload.step ? [...(msg.trace || []), payload.step] : (msg.trace || []);
                return {
                  ...msg,
                  content: payload.step?.detail || msg.content,
                  trace: nextTrace,
                  metadata: payload.metadata || msg.metadata,
                  isStreaming: true,
                };
              });
            }

            if (payload.type === 'done') {
              updateAssistantMessage((msg) => ({
                ...msg,
                content: payload.answer || msg.content,
                trace: payload.trace || msg.trace || [],
                metadata: payload.metadata || msg.metadata,
                isStreaming: false,
              }));
              streamEnded = true;
            }

            if (payload.type === 'error') {
              updateAssistantMessage((msg) => ({
                ...msg,
                content: payload.message || 'Desole, une erreur s\'est produite.',
                isStreaming: false,
              }));
              streamEnded = true;
            }
          } catch (parseErr) {
            console.error('Erreur parsing SSE:', parseErr);
          }
        });
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: "Désolé, une erreur s'est produite.", isStreaming: false }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !chatId) return;
    const msg = input.trim();
    setInput('');
    sendQuery(msg);
  };

  return (
    <div className="chat-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="chat-history">
        {uploadStatus?.status === 'processing' && (
          <div className="message ai" style={{ borderStyle: 'dashed' }}>
            <strong>Indexation en cours...</strong>
            <div style={{ marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              {uploadStatus?.stats?.processed_files || 0} / {uploadStatus?.stats?.total_files || 0} fichiers traites
              {' • '}Chunks ajoutes: {uploadStatus?.stats?.chunks_added || 0}
            </div>
          </div>
        )}

        {uploadStatus?.status === 'failed' && (
          <div className="message ai" style={{ borderColor: '#ef4444' }}>
            L'indexation a echoue pour tous les fichiers. Verifiez le format PDF puis reessayez.
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div style={{ whiteSpace: 'pre-wrap' }}>
              {m.role === 'user' ? m.content : renderTextWithCitations(m.content)}
            </div>
            {m.trace && m.trace.length > 0 && (
              <AgentTraceViewer steps={m.trace} totalTokens={m.metadata?.total_tokens} isLive={m.isStreaming} />
            )}
          </div>
        ))}
        {loading && (
          <div className="message ai" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
              <Loader2 className="animate-spin" size={20} color="var(--accent-primary)" /> 
              Analyse Multi-Agents en cours...
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      <ChatInput 
        input={input}
        setInput={setInput}
        onSubmit={handleSubmit}
        loading={loading}
        disabled={!chatId || uploadStatus?.status === 'processing'}
      />
    </div>
  );
}
