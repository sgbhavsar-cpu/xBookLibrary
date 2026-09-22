import React, { useState, useEffect } from 'react';
import { Search, Loader2, X, Check, Image as ImageIcon } from 'lucide-react';
import { api } from '../../api/client';
import type { OnlineMetadataCandidate } from '../../types';

interface OnlineMetadataDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  bookId: number;
  initialTitle?: string;
  initialAuthor?: string;
  initialIsbn?: string;
  onApplyCandidate: (
    candidate: OnlineMetadataCandidate,
    fieldsToApply: {
      title: boolean;
      authors: boolean;
      publisher: boolean;
      published_date: boolean;
      description: boolean;
      tags: boolean;
      isbn: boolean;
      cover: boolean;
    }
  ) => void;
}

export const OnlineMetadataDrawer: React.FC<OnlineMetadataDrawerProps> = ({
  isOpen,
  onClose,
  bookId,
  initialTitle = '',
  initialAuthor = '',
  initialIsbn = '',
  onApplyCandidate,
}) => {
  const [title, setTitle] = useState(initialTitle);
  const [author, setAuthor] = useState(initialAuthor);
  const [isbn, setIsbn] = useState(initialIsbn);
  const [isLoading, setIsLoading] = useState(false);
  const [candidates, setCandidates] = useState<OnlineMetadataCandidate[]>([]);
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [fieldSelection, setFieldSelection] = useState({
    title: true,
    authors: true,
    publisher: true,
    published_date: true,
    description: true,
    tags: true,
    isbn: true,
    cover: true,
  });

  useEffect(() => {
    if (isOpen) {
      setTitle(initialTitle);
      setAuthor(initialAuthor);
      setIsbn(initialIsbn);
      if (initialTitle || initialIsbn) {
        handleSearch(initialTitle, initialAuthor, initialIsbn);
      }
    }
  }, [isOpen, bookId]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown, { capture: true });
    return () => window.removeEventListener('keydown', handleKeyDown, { capture: true });
  }, [isOpen, onClose]);

  const handleSearch = async (
    qTitle = title,
    qAuthor = author,
    qIsbn = isbn
  ) => {
    if (!qTitle.trim() && !qAuthor.trim() && !qIsbn.trim()) return;
    setIsLoading(true);
    setError(null);
    setSelectedCandidateIndex(null);

    try {
      const results = await api.queryOnlineMetadata(bookId, {
        title: qTitle.trim() || undefined,
        author: qAuthor.trim() || undefined,
        isbn: qIsbn.trim() || undefined,
      });
      setCandidates(results);
      if (results.length > 0) {
        setSelectedCandidateIndex(0);
      } else {
        setError('No matching online books found. Try adjusting your search query.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to query online metadata providers');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const selectedCandidate =
    selectedCandidateIndex !== null ? candidates[selectedCandidateIndex] : null;

  const toggleField = (field: keyof typeof fieldSelection) => {
    setFieldSelection((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const handleApply = () => {
    if (!selectedCandidate) return;
    onApplyCandidate(selectedCandidate, fieldSelection);
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 80,
        background: 'var(--bg-modal, rgba(0, 0, 0, 0.65))',
        backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
        display: 'flex',
        justifyContent: 'flex-end',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '640px',
          height: '100%',
          background: 'var(--bg-card)',
          borderLeft: '1px solid var(--border-default)',
          boxShadow: 'var(--shadow-glass)',
          display: 'flex',
          flexDirection: 'column',
          color: 'var(--text-primary)',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '14px 18px',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-surface)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-surface)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Search size={16} />
            </div>
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 700, margin: 0 }}>
                Download Metadata & Cover
              </h3>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
                Google Books & OpenLibrary online providers
              </p>
            </div>
          </div>
          <button onClick={onClose} className="btn-icon">
            <X size={16} />
          </button>
        </div>

        {/* Search Bar Inputs */}
        <div
          style={{
            padding: '14px 18px',
            background: 'var(--bg-surface-elevated)',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr auto', gap: '8px' }}>
            <div>
              <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '3px' }}>
                Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Book title..."
                className="input-text"
              />
            </div>
            <div>
              <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '3px' }}>
                Author
              </label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Author name..."
                className="input-text"
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button
                onClick={() => handleSearch()}
                disabled={isLoading}
                className="btn btn-primary"
                style={{ height: '34px', padding: '0 14px' }}
              >
                {isLoading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                <span>Search</span>
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="text"
              value={isbn}
              onChange={(e) => setIsbn(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Optional ISBN (e.g. 9780441172719)..."
              className="input-text"
              style={{ flex: 1, fontSize: '12px' }}
            />
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Press Enter to search
            </span>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {error && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#ef4444',
                fontSize: '12px',
              }}
            >
              {error}
            </div>
          )}

          {isLoading && (
            <div style={{ padding: '3rem 0', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
              <Loader2 size={28} className="animate-spin" color="var(--accent-primary)" />
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
                Querying Google Books and OpenLibrary...
              </p>
            </div>
          )}

          {!isLoading && candidates.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <h4 style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
                Matching Results ({candidates.length})
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {candidates.map((cand, idx) => {
                  const isSelected = selectedCandidateIndex === idx;
                  const confidencePct = Math.round(cand.confidence_score * 100);

                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedCandidateIndex(idx)}
                      style={{
                        padding: '10px',
                        borderRadius: 'var(--radius-md)',
                        border: isSelected
                          ? '1px solid var(--accent-primary)'
                          : '1px solid var(--border-default)',
                        background: isSelected
                          ? 'var(--accent-surface)'
                          : 'var(--bg-surface)',
                        cursor: 'pointer',
                        display: 'flex',
                        gap: '12px',
                        transition: 'all var(--transition-fast)',
                        boxShadow: isSelected ? '0 0 0 1px var(--accent-primary)' : undefined,
                      }}
                    >
                      {/* Thumbnail */}
                      <div
                        style={{
                          width: '52px',
                          height: '75px',
                          borderRadius: 'var(--radius-xs)',
                          border: '1px solid var(--border-subtle)',
                          overflow: 'hidden',
                          flexShrink: 0,
                          background: 'var(--bg-surface-elevated)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {cand.cover_url ? (
                          <img
                            src={cand.cover_url}
                            alt={cand.title}
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            onError={(e) => {
                              (e.target as HTMLElement).style.display = 'none';
                            }}
                          />
                        ) : (
                          <ImageIcon size={20} color="var(--text-muted)" />
                        )}
                      </div>

                      {/* Info */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                          <h5
                            style={{
                              fontSize: '13px',
                              fontWeight: 600,
                              margin: 0,
                              color: 'var(--text-primary)',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {cand.title}
                          </h5>
                          <span
                            style={{
                              fontSize: '10px',
                              fontWeight: 700,
                              padding: '2px 6px',
                              borderRadius: 'var(--radius-full)',
                              background: confidencePct >= 80 ? 'rgba(16, 185, 129, 0.2)' : 'var(--bg-surface-elevated)',
                              color: confidencePct >= 80 ? '#10b981' : 'var(--text-muted)',
                              flexShrink: 0,
                            }}
                          >
                            {confidencePct}% Match
                          </span>
                        </div>

                        <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: '2px 0 4px 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          by {cand.authors.join(', ') || 'Unknown'}
                        </p>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                          <span style={{ textTransform: 'capitalize', padding: '1px 5px', borderRadius: '3px', background: 'var(--bg-surface-elevated)', color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: '10px' }}>
                            {cand.source.replace('_', ' ')}
                          </span>
                          {cand.publisher && <span>{cand.publisher}</span>}
                          {cand.published_date && <span>({cand.published_date})</span>}
                          {cand.isbn && <span>ISBN: {cand.isbn}</span>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Selected Candidate Fields Merger */}
          {selectedCandidate && (
            <div
              style={{
                marginTop: '12px',
                padding: '14px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-default)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h4 style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
                  Fields to Import
                </h4>
                <div style={{ display: 'flex', gap: '8px', fontSize: '11px' }}>
                  <button
                    onClick={() =>
                      setFieldSelection({
                        title: true,
                        authors: true,
                        publisher: true,
                        published_date: true,
                        description: true,
                        tags: true,
                        isbn: true,
                        cover: true,
                      })
                    }
                    style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', padding: 0 }}
                  >
                    Select All
                  </button>
                  <span style={{ color: 'var(--text-muted)' }}>•</span>
                  <button
                    onClick={() =>
                      setFieldSelection({
                        title: false,
                        authors: false,
                        publisher: false,
                        published_date: false,
                        description: false,
                        tags: false,
                        isbn: false,
                        cover: false,
                      })
                    }
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}
                  >
                    Deselect All
                  </button>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.title}
                    onChange={() => toggleField('title')}
                  />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Title: <strong>{selectedCandidate.title}</strong>
                  </span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.authors}
                    onChange={() => toggleField('authors')}
                  />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Authors: <strong>{selectedCandidate.authors.join(', ')}</strong>
                  </span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.publisher}
                    onChange={() => toggleField('publisher')}
                  />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Publisher: <strong>{selectedCandidate.publisher || 'None'}</strong>
                  </span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.published_date}
                    onChange={() => toggleField('published_date')}
                  />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Year/Date: <strong>{selectedCandidate.published_date || 'None'}</strong>
                  </span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.tags}
                    onChange={() => toggleField('tags')}
                  />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Tags ({selectedCandidate.tags.length} subjects)
                  </span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.isbn}
                    onChange={() => toggleField('isbn')}
                  />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    ISBN: <strong>{selectedCandidate.isbn || 'None'}</strong>
                  </span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.cover}
                    onChange={() => toggleField('cover')}
                  />
                  <span>
                    Cover Image {selectedCandidate.cover_url ? '✓' : '(None)'}
                  </span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={fieldSelection.description}
                    onChange={() => toggleField('description')}
                  />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Description ({selectedCandidate.description ? `${selectedCandidate.description.length} chars` : 'None'})
                  </span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div
          style={{
            padding: '12px 18px',
            borderTop: '1px solid var(--border-default)',
            background: 'var(--bg-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {selectedCandidate ? 'Candidate selected ready to apply' : 'Choose a candidate to apply'}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              onClick={handleApply}
              disabled={!selectedCandidate}
              className="btn btn-primary"
            >
              <Check size={14} />
              <span>Apply Selected Metadata</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
