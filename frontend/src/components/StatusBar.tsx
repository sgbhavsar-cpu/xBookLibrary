import React, { useEffect, useState } from 'react';
import { BookOpen, CheckCircle, Database, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';

export const StatusBar: React.FC = () => {
  const { books, libraries, activeLibraryId } = useStore();
  const [indexStatus, setIndexStatus] = useState<{
    total_books: number;
    indexed_books: number;
    total_chunks: number;
  } | null>(null);

  const activeLib = libraries.find((l) => l.id === activeLibraryId);

  useEffect(() => {
    if (!activeLibraryId) return;
    api.getLibraryIndexStatus(activeLibraryId)
      .then(setIndexStatus)
      .catch(() => setIndexStatus(null));
  }, [activeLibraryId, books]);

  const indexedPercent = indexStatus && indexStatus.total_books > 0
    ? Math.round((indexStatus.indexed_books / indexStatus.total_books) * 100)
    : 0;

  return (
    <footer
      style={{
        height: 'var(--status-bar-height)',
        background: 'var(--bg-surface-elevated)',
        borderTop: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1rem',
        fontSize: '11.5px',
        color: 'var(--text-secondary)',
        userSelect: 'none',
        zIndex: 20,
      }}
    >
      {/* Left Metrics */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <Database size={13} color="var(--accent-primary)" />
          <span>Library: <strong>{activeLib?.name || 'Default'}</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <BookOpen size={13} color="var(--text-muted)" />
          <span>Total Books: <strong>{books.length}</strong></span>
        </div>

        {indexStatus && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Sparkles size={13} color="var(--accent-primary)" />
            <span>
              RAG Vector Index: <strong>{indexStatus.indexed_books}/{indexStatus.total_books} ({indexedPercent}%)</strong> &bull; {indexStatus.total_chunks} chunks
            </span>
          </div>
        )}
      </div>

      {/* Center Shortcuts Hint */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: 'var(--text-muted)',
          fontSize: '11px',
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
          <kbd style={{ padding: '1px 4px', background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '3px', fontSize: '10px' }}>E</kbd> Edit
        </span>
        &bull;
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
          <kbd style={{ padding: '1px 4px', background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '3px', fontSize: '10px' }}>C</kbd> Convert
        </span>
        &bull;
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
          <kbd style={{ padding: '1px 4px', background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '3px', fontSize: '10px' }}>V</kbd> Read
        </span>
        &bull;
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
          <kbd style={{ padding: '1px 4px', background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '3px', fontSize: '10px' }}>Esc</kbd> Deselect
        </span>
      </div>

      {/* Right Ready Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
        <CheckCircle size={13} color="#10b981" />
        <span>Ready</span>
      </div>
    </footer>
  );
};
