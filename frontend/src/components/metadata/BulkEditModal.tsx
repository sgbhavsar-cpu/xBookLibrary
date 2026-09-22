import React, { useState, useEffect } from 'react';
import { X, Layers, Save, Star, Tag, Plus, Loader2 } from 'lucide-react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';

interface BulkEditModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BulkEditModal: React.FC<BulkEditModalProps> = ({ isOpen, onClose }) => {
  const {
    selectedBookIds,
    clearSelectedBooks,
    loadBooks,
    setToastMessage,
  } = useStore();

  const [addTagInput, setAddTagInput] = useState('');
  const [addTags, setAddTags] = useState<string[]>([]);
  const [removeTagInput, setRemoveTagInput] = useState('');
  const [removeTags, setRemoveTags] = useState<string[]>([]);

  const [setAuthor, setSetAuthor] = useState('');
  const [setPublisher, setSetPublisher] = useState('');
  const [rating, setRating] = useState<number>(0);

  const [seriesName, setSeriesName] = useState('');
  const [autoIncrementSeries, setAutoIncrementSeries] = useState(true);
  const [seriesStartIndex, setSeriesStartIndex] = useState<number>(1.0);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        handleApply();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedBookIds, addTags, removeTags, setAuthor, setPublisher, rating, seriesName, autoIncrementSeries, seriesStartIndex]);

  if (!isOpen) return null;

  const handleAddTag = () => {
    if (addTagInput.trim() && !addTags.includes(addTagInput.trim())) {
      setAddTags([...addTags, addTagInput.trim()]);
      setAddTagInput('');
    }
  };

  const handleAddRemoveTag = () => {
    if (removeTagInput.trim() && !removeTags.includes(removeTagInput.trim())) {
      setRemoveTags([...removeTags, removeTagInput.trim()]);
      setRemoveTagInput('');
    }
  };

  const handleApply = async () => {
    if (selectedBookIds.length === 0) return;
    setIsSubmitting(true);
    setError(null);

    try {
      const res = await api.bulkUpdateBooks({
        book_ids: selectedBookIds,
        add_tags: addTags.length > 0 ? addTags : undefined,
        remove_tags: removeTags.length > 0 ? removeTags : undefined,
        set_author: setAuthor.trim() || undefined,
        set_publisher: setPublisher.trim() || undefined,
        set_rating: rating > 0 ? rating : undefined,
        set_series: seriesName.trim() || undefined,
        auto_increment_series: seriesName.trim() ? autoIncrementSeries : undefined,
        series_start_index: seriesName.trim() ? seriesStartIndex : undefined,
      });

      setToastMessage(`Successfully updated ${res.updated_count} books`);
      clearSelectedBooks();
      await loadBooks();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to apply bulk update');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 70,
        background: 'var(--bg-modal, rgba(0, 0, 0, 0.75))',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-default)',
          boxShadow: 'var(--shadow-glass)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '14px 20px',
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
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-surface)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Layers size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  Bulk Edit Books
                </h2>
                <span
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: 'var(--accent-primary)',
                    color: '#fff',
                    fontWeight: 600,
                  }}
                >
                  {selectedBookIds.length} Selected
                </span>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
                Modify shared tags, authors, series, and ratings across multiple titles
              </p>
            </div>
          </div>
          <button onClick={onClose} className="btn-icon">
            <X size={16} />
          </button>
        </div>

        {/* Modal Form */}
        <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
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

          {/* Tags Add / Remove */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <Tag size={13} />
                <span>Add Tags</span>
              </label>
              <div style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
                <input
                  type="text"
                  value={addTagInput}
                  onChange={(e) => setAddTagInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  placeholder="Tag to add..."
                  className="input-text"
                  style={{ flex: 1, fontSize: '12px' }}
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="btn btn-secondary"
                  style={{ padding: '0 10px' }}
                >
                  <Plus size={14} />
                </button>
              </div>
              {addTags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {addTags.map((t) => (
                    <span
                      key={t}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-full)',
                        background: 'rgba(16, 185, 129, 0.15)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        fontSize: '11px',
                        color: '#10b981',
                      }}
                    >
                      <span>+{t}</span>
                      <button
                        type="button"
                        onClick={() => setAddTags(addTags.filter((item) => item !== t))}
                        style={{ background: 'none', border: 'none', color: '#10b981', cursor: 'pointer', padding: 0 }}
                      >
                        <X size={10} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <Tag size={13} />
                <span>Remove Tags</span>
              </label>
              <div style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
                <input
                  type="text"
                  value={removeTagInput}
                  onChange={(e) => setRemoveTagInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddRemoveTag())}
                  placeholder="Tag to remove..."
                  className="input-text"
                  style={{ flex: 1, fontSize: '12px' }}
                />
                <button
                  type="button"
                  onClick={handleAddRemoveTag}
                  className="btn btn-secondary"
                  style={{ padding: '0 10px' }}
                >
                  <Plus size={14} />
                </button>
              </div>
              {removeTags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {removeTags.map((t) => (
                    <span
                      key={t}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-full)',
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        fontSize: '11px',
                        color: '#ef4444',
                      }}
                    >
                      <span>-{t}</span>
                      <button
                        type="button"
                        onClick={() => setRemoveTags(removeTags.filter((item) => item !== t))}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: 0 }}
                      >
                        <X size={10} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Author & Publisher */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Set Author (leaves unchanged if empty)
              </label>
              <input
                type="text"
                value={setAuthor}
                onChange={(e) => setSetAuthor(e.target.value)}
                placeholder="New author name..."
                className="input-text"
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Set Publisher (leaves unchanged if empty)
              </label>
              <input
                type="text"
                value={setPublisher}
                onChange={(e) => setSetPublisher(e.target.value)}
                placeholder="Publisher name..."
                className="input-text"
              />
            </div>
          </div>

          {/* Series & Auto-Numbering */}
          <div
            style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-default)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <h4 style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
              Series Configuration
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 0.6fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '3px' }}>
                  Series Name
                </label>
                <input
                  type="text"
                  value={seriesName}
                  onChange={(e) => setSeriesName(e.target.value)}
                  placeholder="e.g. The Expanse"
                  className="input-text"
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '3px' }}>
                  Start Index
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={seriesStartIndex}
                  onChange={(e) => setSeriesStartIndex(parseFloat(e.target.value) || 1.0)}
                  className="input-text"
                  style={{ fontFamily: 'monospace' }}
                />
              </div>
            </div>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <input
                type="checkbox"
                checked={autoIncrementSeries}
                onChange={(e) => setAutoIncrementSeries(e.target.checked)}
              />
              <span>
                Auto-increment series index sequentially (e.g. 1.0, 2.0, 3.0...) across selected books
              </span>
            </label>
          </div>

          {/* Rating */}
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              Set Rating (leaves unchanged if 0)
            </label>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                height: '36px',
                padding: '0 8px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                width: 'fit-content',
              }}
            >
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(rating === star ? 0 : star)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '2px',
                    color: star <= rating ? '#eab308' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <Star size={18} fill={star <= rating ? '#eab308' : 'none'} />
                </button>
              ))}
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '8px' }}>
                {rating > 0 ? `${rating} stars` : 'Do not change'}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid var(--border-default)',
            background: 'var(--bg-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Applying to {selectedBookIds.length} books
          </span>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              onClick={handleApply}
              disabled={isSubmitting}
              className="btn btn-primary"
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Applying...</span>
                </>
              ) : (
                <>
                  <Save size={14} />
                  <span>Apply Bulk Changes</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
