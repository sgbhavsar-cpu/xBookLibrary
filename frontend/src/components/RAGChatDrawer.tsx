import React, { useEffect, useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import type { ChatMessage, ChatSession } from '../types';

export const RAGChatDrawer: React.FC = () => {
  const { activeLibraryId, isRAGChatOpen, setRAGChatOpen } = useStore();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedCitation, setExpandedCitation] = useState<string | null>(null);

  useEffect(() => {
    if (!activeLibraryId || !isRAGChatOpen) return;
    api.createChatSession(activeLibraryId, undefined, 'Library General QA')
      .then((s) => {
        setSession(s);
        return api.getChatMessages(s.id);
      })
      .then(setMessages)
      .catch((err) => console.error('Failed to init library chat:', err));
  }, [activeLibraryId, isRAGChatOpen]);

  if (!isRAGChatOpen) return null;

  const handleSend = async () => {
    if (!input.trim() || !session || isLoading) return;
    const prompt = input.trim();
    setInput('');
    setIsLoading(true);

    const tempMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: session.id,
      role: 'user',
      content: prompt,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMsg]);

    try {
      const reply = await api.sendChatMessage(session.id, prompt);
      setMessages((prev) => [...prev, reply]);
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSession = async () => {
    if (!activeLibraryId) return;
    try {
      const s = await api.createChatSession(activeLibraryId, undefined, `Chat Session ${Date.now()}`);
      setSession(s);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  };

  return (
    <aside
      className="glass-panel"
      style={{
        position: 'fixed',
        right: 0,
        top: 0,
        width: '420px',
        height: '100vh',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: 'var(--shadow-glass)',
        borderLeft: '1px solid var(--border-glass)',
      }}
    >
      {/* Header */}
      <div
        style={{
          height: 'var(--header-height)',
          padding: '0 1.25rem',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="var(--accent-primary)" />
          <span style={{ fontWeight: 700, fontSize: '14px' }}>Library Conversational QA</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            className="btn-icon"
            onClick={handleNewSession}
            title="New Chat Session"
            style={{ width: '30px', height: '30px' }}
          >
            <Plus size={15} />
          </button>
          <button
            className="btn-icon"
            onClick={() => setRAGChatOpen(false)}
            title="Close Drawer"
            style={{ width: '30px', height: '30px' }}
          >
            <X size={15} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          fontSize: '13px',
        }}
      >
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '4rem' }}>
            <MessageSquare size={40} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            <h4 style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
              Ask Your Library Anything
            </h4>
            <p style={{ fontSize: '12px', maxWidth: '280px', margin: '0 auto' }}>
              Answers are synthesized with LanceDB hybrid vector search and grounded with exact book citations.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '90%',
              background: msg.role === 'user' ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
              color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              borderBottomRightRadius: msg.role === 'user' ? '2px' : 'var(--radius-md)',
              borderBottomLeftRadius: msg.role === 'assistant' ? '2px' : 'var(--radius-md)',
              lineHeight: 1.5,
              border: msg.role === 'assistant' ? '1px solid var(--border-subtle)' : undefined,
            }}
          >
            <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>

            {/* Expandable Citations */}
            {msg.citations && msg.citations.length > 0 && (
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, opacity: 0.85, marginBottom: '4px' }}>
                  Grounded Citations ({msg.citations.length}):
                </div>
                {msg.citations.map((c, i) => {
                  const citKey = `${msg.id}-${i}`;
                  const isExp = expandedCitation === citKey;
                  return (
                    <div
                      key={i}
                      style={{
                        fontSize: '11px',
                        marginBottom: '4px',
                        background: 'var(--bg-card)',
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--border-subtle)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      <div
                        onClick={() => setExpandedCitation(isExp ? null : citKey)}
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
                      >
                        <span>
                          <strong>{c.book_title}</strong> &bull; {c.chapter_title}
                        </span>
                        {isExp ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      </div>
                      {isExp && (
                        <div style={{ marginTop: '4px', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                          "{c.content}"
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div style={{ alignSelf: 'flex-start', background: 'var(--bg-surface-elevated)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontSize: '12px', color: 'var(--text-muted)' }}>
            Searching across library vectors...
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '12px', borderTop: '1px solid var(--border-default)', display: 'flex', gap: '8px', background: 'var(--bg-surface)' }}>
        <input
          type="text"
          className="input-text"
          placeholder="Ask a question across all books..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
        >
          <Send size={14} />
        </button>
      </div>
    </aside>
  );
};
