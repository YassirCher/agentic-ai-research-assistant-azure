import React from 'react';
import { Send } from 'lucide-react';

export default function ChatInput({ input, setInput, onSubmit, loading, placeholder, disabled }) {
  return (
    <div className="input-area">
      <form onSubmit={onSubmit} className="input-form">
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder || (disabled ? "Désactivé" : "Posez votre question...")}
          disabled={loading || disabled}
        />
        <button type="submit" className="send-btn" disabled={!input.trim() || loading || disabled}>
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}
