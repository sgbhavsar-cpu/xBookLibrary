import React, { useEffect } from 'react';
import { AlertCircle, CopyPlus, GitMerge, SkipForward, X } from 'lucide-react';

export interface DuplicateConflictInfo {
  file: File;
  match: {
    matched_by: string;
    book_id: number;
    title: string;
    authors: string[];
    existing_formats: string[];
  };
}

interface ImportConflictModalProps {
  isOpen: boolean;
  conflict: DuplicateConflictInfo | null;
  onResolve: (action: 'merge' | 'create_new' | 'skip') => void;
  onClose: () => void;
}

export const ImportConflictModal: React.FC<ImportConflictModalProps> = ({
  isOpen,
  conflict,
  onResolve,
  onClose,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !conflict) return null;

  const { file, match } = conflict;
  const incomingExt = file.name.split('.').pop()?.toUpperCase() || 'FILE';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'var(--bg-modal, rgba(0, 0, 0, 0.75))',
        backdropFilter: 'blur(8px)',
        zIndex: 90,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '520px',
          borderRadius: 'var(--radius-lg, 12px)',
          background: 'var(--bg-surface, #18181b)',
          border: '1px solid var(--border-default, #27272a)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
          color: 'var(--text-primary, #f4f4f5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-subtle, #27272a)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-surface-elevated, #27272a)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} color="#f59e0b" />
            <h3 style={{ fontSize: '15px', fontWeight: 600, margin: 0 }}>
              Duplicate Book Detected
            </h3>
          </div>
          <button
            className="btn-icon"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted, #a1a1aa)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '4px',
              borderRadius: '4px',
            }}
            title="Cancel (Esc)"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary, #d4d4d8)', margin: 0 }}>
            The file you are importing matches an existing title and author in your library:
          </p>

          <div
            style={{
              padding: '12px 14px',
              borderRadius: 'var(--radius-sm, 6px)',
              background: 'var(--bg-card, #202024)',
              border: '1px solid var(--border-subtle, #2e2e33)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              fontSize: '12.5px',
            }}
          >
            <div>
              <span style={{ color: 'var(--text-muted, #71717a)' }}>Existing Title: </span>
              <strong>{match.title}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted, #71717a)' }}>Authors: </span>
              <span>{match.authors.join(', ') || 'Unknown'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', marginTop: '2px' }}>
              <span style={{ color: 'var(--text-muted, #71717a)' }}>Current Formats:</span>
              {match.existing_formats.map((f) => (
                <span
                  key={f}
                  style={{
                    background: 'var(--accent-surface, rgba(99, 102, 241, 0.15))',
                    color: 'var(--accent-primary, #818cf8)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 600,
                  }}
                >
                  {f}
                </span>
              ))}
            </div>
            <div style={{ borderTop: '1px dashed var(--border-subtle, #2e2e33)', paddingTop: '6px', marginTop: '4px' }}>
              <span style={{ color: 'var(--text-muted, #71717a)' }}>Incoming File: </span>
              <strong style={{ color: '#38bdf8' }}>{file.name}</strong> ({incomingExt})
            </div>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text-muted, #a1a1aa)', margin: 0 }}>
            How would you like to handle this duplicate?
          </p>

          {/* Action Choices */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              className="btn btn-primary"
              onClick={() => onResolve('merge')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                gap: '10px',
                padding: '10px 14px',
                textAlign: 'left',
              }}
            >
              <GitMerge size={16} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px' }}>Merge format into existing book</div>
                <div style={{ fontSize: '11px', opacity: 0.85 }}>
                  Attaches {incomingExt} to &quot;{match.title}&quot; without creating a separate entry.
                </div>
              </div>
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => onResolve('create_new')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                gap: '10px',
                padding: '10px 14px',
                textAlign: 'left',
              }}
            >
              <CopyPlus size={16} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px' }}>Create new separate book</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted, #a1a1aa)' }}>
                  Keeps existing book unchanged and adds a distinct duplicate entry in your library.
                </div>
              </div>
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => onResolve('skip')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                gap: '10px',
                padding: '10px 14px',
                textAlign: 'left',
              }}
            >
              <SkipForward size={16} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px' }}>Skip this file</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted, #a1a1aa)' }}>
                  Do not import this file.
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
