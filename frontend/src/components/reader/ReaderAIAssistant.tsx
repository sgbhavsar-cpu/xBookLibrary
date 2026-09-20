import React, { useEffect, useState } from 'react';
import { MessageSquare, Send, Sparkles, X } from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';
import type { ChatMessage, ChatSession } from '../../types';

interface ReaderAIAssistantProps {
  bookId: number;
  bookTitle: string;
}

export const ReaderAIAssistant: React.FC<ReaderAIAssistantProps> = ({
  bookId,
  bookTitle,
}) => {
  const { activeLibraryId, isReaderAIOpen, toggleReaderAI } = useStore();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!activeLibraryId || !isReaderAIOpen) return;
    api.createChatSession(activeLibraryId, bookId, `Reader QA: ${bookTitle}`)
      .then((s) => {
        setSession(s);
        return api.getChatMessages(s.id);
      })
      .then(setMessages)
      .catch((err) => console.error('Failed to init reader chat:', err));
  }, [activeLibraryId, bookId, bookTitle, isReaderAIOpen]);

  if (!isReaderAIOpen) return null;

  const handleSend = async () => {
    if (!input.trim() || !session || isLoading) return;
    const userPrompt = input.trim();
    setInput('');
    setIsLoading(true);

    // Optimistic user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: session.id,
      role: 'user',
      content: userPrompt,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const assistantMsg = await api.sendChatMessage(session.id, userPrompt);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside
      className="glass-panel"
      style={{
        width: '380px',
        height: 'calc(100vh - 56px)',
        borderLeft: '1px solid var(--border-default)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 30,
        position: 'absolute',
        right: 0,
        top: '56px',
        boxShadow: 'var(--shadow-lg)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={16} color="var(--accent-primary)" />
          <span style={{ fontWeight: 600, fontSize: '13px' }}>Book Reading Assistant</span>
        </div>
        <button className="btn-icon" onClick={toggleReaderAI} style={{ width: '28px', height: '28px' }}>
          <X size={14} />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          fontSize: '13px',
        }}
      >
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '2rem' }}>
            <MessageSquare size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
            <p>Ask questions about concepts, arguments, or chapters in <em>{bookTitle}</em>.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '88%',
              background: msg.role === 'user' ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
              color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              borderBottomRightRadius: msg.role === 'user' ? '2px' : 'var(--radius-md)',
              borderBottomLeftRadius: msg.role === 'assistant' ? '2px' : 'var(--radius-md)',
              lineHeight: 1.5,
            }}
          >
            <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>

            {/* Citations Footer */}
            {msg.citations && msg.citations.length > 0 && (
              <div
                style={{
                  marginTop: '8px',
                  paddingTop: '6px',
                  borderTop: '1px solid var(--border-subtle)',
                  fontSize: '11px',
                }}
              >
                <div style={{ fontWeight: 600, opacity: 0.8, marginBottom: '4px' }}>Citations:</div>
                {msg.citations.map((c, i) => (
                  <div key={i} style={{ opacity: 0.9, marginBottom: '2px' }}>
                    &bull; <strong>{c.chapter_title}</strong>: "{c.content.slice(0, 75)}..."
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div
            style={{
              alignSelf: 'flex-start',
              background: 'var(--bg-surface-elevated)',
              padding: '8px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
              color: 'var(--text-muted)',
            }}
          >
            Searching book passages & thinking...
          </div>
        )}
      </div>

      {/* Input Footer */}
      <div
        style={{
          padding: '10px 14px',
          borderTop: '1px solid var(--border-default)',
          display: 'flex',
          gap: '8px',
          background: 'var(--bg-surface)',
        }}
      >
        <input
          type="text"
          className="input-text"
          placeholder="Ask a question about this book..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          style={{ padding: '0 14px' }}
        >
          <Send size={14} />
        </button>
      </div>
    </aside>
  );
};
