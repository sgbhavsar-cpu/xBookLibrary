import React, { useRef, useState, useEffect } from 'react';
import { Book as BookIcon, Check, Loader2, Pencil, Sparkles, Star, X } from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import type { Book } from '../types';

interface BookCardProps {
  book: Book;
  isSelected: boolean;
  isChecked?: boolean;
  onSelect: () => void;
  onToggleCheck?: () => void;
  onDoubleClick?: () => void;
}

export const BookCard: React.FC<BookCardProps> = ({
  book,
  isSelected,
  isChecked = false,
  onSelect,
  onToggleCheck,
  onDoubleClick,
}) => {
  const { loadBooks, selectBook, setToastMessage } = useStore();
  const [coverError, setCoverError] = useState(false);
  const coverUrl = api.getBookCoverUrl(book.id);
  const lastClickTimeRef = useRef<number>(0);

  // In-place editing state
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(book.title || '');
  const [authors, setAuthors] = useState(book.authors ? book.authors.join(', ') : '');
  const [series, setSeries] = useState(book.series || '');
  const [seriesIndex, setSeriesIndex] = useState<number>(book.series_index ?? 1.0);
  const [rating, setRating] = useState<number>(book.custom_values?.rating ?? book.rating ?? 0);
  const [tags, setTags] = useState(book.tags ? book.tags.join(', ') : '');
  const [isSaving, setIsSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Synchronize state when book prop changes
  useEffect(() => {
    if (!isEditing) {
      setTitle(book.title || '');
      setAuthors(book.authors ? book.authors.join(', ') : '');
      setSeries(book.series || '');
      setSeriesIndex(book.series_index ?? 1.0);
      setRating(book.custom_values?.rating ?? book.rating ?? 0);
      setTags(book.tags ? book.tags.join(', ') : '');
      setEditError(null);
    }
  }, [book, isEditing]);

  const handleClick = () => {
    if (isEditing) return;
    const now = Date.now();
    if (now - lastClickTimeRef.current < 400) {
      lastClickTimeRef.current = 0;
      onDoubleClick?.();
    } else {
      lastClickTimeRef.current = now;
      onSelect();
    }
  };

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setTitle(book.title || '');
    setAuthors(book.authors ? book.authors.join(', ') : '');
    setSeries(book.series || '');
    setSeriesIndex(book.series_index ?? 1.0);
    setRating(book.custom_values?.rating ?? book.rating ?? 0);
    setTags(book.tags ? book.tags.join(', ') : '');
    setEditError(null);
    setIsEditing(true);
  };

  const handleCancelEdit = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setTitle(book.title || '');
    setAuthors(book.authors ? book.authors.join(', ') : '');
    setSeries(book.series || '');
    setSeriesIndex(book.series_index ?? 1.0);
    setRating(book.custom_values?.rating ?? book.rating ?? 0);
    setTags(book.tags ? book.tags.join(', ') : '');
    setEditError(null);
    setIsEditing(false);
  };

  const handleSaveEdit = async (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (!title.trim()) {
      setEditError('Title cannot be empty');
      return;
    }
    setIsSaving(true);
    setEditError(null);

    try {
      const parsedAuthors = authors
        .split(',')
        .map((a) => a.trim())
        .filter(Boolean);
      const parsedTags = tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);

      await api.updateBookMetadata(book.id, {
        title: title.trim(),
        authors: parsedAuthors.length > 0 ? parsedAuthors : undefined,
        series_name: series.trim() || undefined,
        series_index: series.trim() ? seriesIndex : undefined,
        rating: rating > 0 ? rating : undefined,
        tags: parsedTags,
      });

      setToastMessage('Metadata updated');
      await loadBooks();
      await selectBook(book.id);
      setIsEditing(false);
    } catch (err: any) {
      setEditError(err.message || 'Failed to save metadata');
    } finally {
      setIsSaving(false);
    }
  };

  // -------------------------------------------------------------
  // Render: IN-PLACE EDIT MODE
  // -------------------------------------------------------------
  if (isEditing) {
    return (
      <div
        className="glass-card"
        onClick={(e) => e.stopPropagation()}
        onDoubleClick={(e) => e.stopPropagation()}
        style={{
          display: 'flex',
          flexDirection: 'column',
          padding: '10px',
          height: '100%',
          minHeight: '340px',
          borderColor: 'var(--accent-primary)',
          boxShadow: '0 0 0 2px var(--accent-glow), var(--shadow-lg)',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          position: 'relative',
          gap: '8px',
          userSelect: 'text',
          zIndex: 25,
        }}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.stopPropagation();
            handleCancelEdit();
          } else if (e.key === 'Enter' && !e.shiftKey) {
            e.stopPropagation();
            handleSaveEdit();
          }
        }}
      >
        {/* Header: Mini Cover & Status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: '6px',
          }}
        >
          <div
            style={{
              width: '28px',
              height: '40px',
              borderRadius: 'var(--radius-xs)',
              overflow: 'hidden',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {!coverError ? (
              <img
                src={coverUrl}
                alt={title}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={() => setCoverError(true)}
              />
            ) : (
              <BookIcon size={14} color="var(--text-muted)" />
            )}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  color: 'var(--accent-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                In-Place Edit
              </span>
              <span
                style={{
                  fontSize: '9px',
                  padding: '1px 4px',
                  borderRadius: '2px',
                  background: 'var(--bg-surface-elevated)',
                  color: 'var(--text-muted)',
                  fontFamily: 'monospace',
                }}
              >
                ID: {book.id}
              </span>
            </div>
            <p style={{ fontSize: '9.5px', color: 'var(--text-muted)', margin: 0 }}>
              Enter to save • Esc to cancel
            </p>
          </div>
          <button
            onClick={handleCancelEdit}
            data-testid="inline-header-cancel-btn"
            className="btn-icon"
            style={{ width: '22px', height: '22px' }}
            title="Cancel (Esc)"
          >
            <X size={12} />
          </button>
        </div>

        {editError && (
          <div
            style={{
              fontSize: '10.5px',
              color: '#ef4444',
              padding: '3px 6px',
              background: 'rgba(239, 68, 68, 0.12)',
              borderRadius: 'var(--radius-xs)',
            }}
          >
            {editError}
          </div>
        )}

        {/* Title Input */}
        <div>
          <label style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '2px' }}>
            Title <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            autoFocus
            className="input-text"
            style={{ fontSize: '11.5px', padding: '4px 6px', fontWeight: 600 }}
            placeholder="Book title..."
          />
        </div>

        {/* Authors Input */}
        <div>
          <label style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '2px' }}>
            Author(s)
          </label>
          <input
            type="text"
            value={authors}
            onChange={(e) => setAuthors(e.target.value)}
            className="input-text"
            style={{ fontSize: '11px', padding: '4px 6px' }}
            placeholder="Author 1, Author 2..."
          />
        </div>

        {/* Series & Series Index */}
        <div>
          <label style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '2px' }}>
            Series & #
          </label>
          <div style={{ display: 'flex', gap: '4px' }}>
            <input
              type="text"
              value={series}
              onChange={(e) => setSeries(e.target.value)}
              className="input-text"
              style={{ fontSize: '11px', padding: '4px 6px', flex: 1 }}
              placeholder="Series name..."
            />
            <input
              type="number"
              step="0.5"
              min="0"
              value={seriesIndex}
              onChange={(e) => setSeriesIndex(parseFloat(e.target.value) || 1.0)}
              className="input-text"
              style={{ fontSize: '11px', padding: '4px 4px', width: '46px', fontFamily: 'monospace', textAlign: 'center' }}
              title="Series Index"
            />
          </div>
        </div>

        {/* Rating Clicker */}
        <div>
          <label style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '2px' }}>
            Rating
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(rating === star ? 0 : star)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '1px',
                  color: star <= rating ? '#eab308' : 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                }}
                title={`${star} star${star > 1 ? 's' : ''}`}
              >
                <Star size={14} fill={star <= rating ? '#eab308' : 'none'} />
              </button>
            ))}
            {rating > 0 && (
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '3px' }}>
                ({rating}/5)
              </span>
            )}
          </div>
        </div>

        {/* Tags Input */}
        <div>
          <label style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '2px' }}>
            Tags
          </label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="input-text"
            style={{ fontSize: '11px', padding: '4px 6px' }}
            placeholder="Sci-Fi, Classics..."
          />
        </div>

        {/* Actions Footer */}
        <div
          style={{
            marginTop: 'auto',
            paddingTop: '6px',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            gap: '6px',
          }}
        >
          <button
            type="button"
            data-testid="inline-cancel-btn"
            onClick={handleCancelEdit}
            className="btn btn-secondary"
            style={{ flex: 1, height: '26px', fontSize: '11px', padding: '0 6px' }}
          >
            Cancel
          </button>
          <button
            type="button"
            data-testid="inline-save-btn"
            onClick={handleSaveEdit}
            disabled={isSaving}
            className="btn btn-primary"
            style={{ flex: 1.2, height: '26px', fontSize: '11px', padding: '0 8px', gap: '4px' }}
          >
            {isSaving ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
            <span>Save</span>
          </button>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Render: NORMAL CARD VIEW
  // -------------------------------------------------------------
  return (
    <div
      className="glass-card"
      onClick={handleClick}
      onDoubleClick={onDoubleClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: '10px',
        cursor: 'pointer',
        height: '100%',
        borderColor: isSelected ? 'var(--accent-primary)' : undefined,
        boxShadow: isSelected ? '0 0 0 2px var(--accent-glow), var(--shadow-md)' : undefined,
        background: isSelected ? 'var(--accent-surface)' : undefined,
        userSelect: 'none',
        position: 'relative',
      }}
    >
      {/* Cover Image Container */}
      <div
        style={{
          width: '100%',
          aspectRatio: '2 / 3',
          borderRadius: 'var(--radius-sm)',
          overflow: 'hidden',
          background: 'var(--bg-surface-elevated)',
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '8px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        {!coverError ? (
          <img
            src={coverUrl}
            alt={book.title}
            onError={() => setCoverError(true)}
            loading="lazy"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transition: 'transform var(--transition-fast)',
            }}
          />
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '1rem',
              textAlign: 'center',
              color: 'var(--text-muted)',
              gap: '6px',
            }}
          >
            <BookIcon size={32} />
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              {book.title}
            </span>
          </div>
        )}

        {/* Selection Checkbox */}
        <div
          onClick={(e) => {
            e.stopPropagation();
            onToggleCheck?.();
          }}
          style={{
            position: 'absolute',
            top: '6px',
            left: '6px',
            zIndex: 10,
            background: isChecked ? 'var(--accent-primary)' : 'rgba(0,0,0,0.55)',
            borderRadius: '4px',
            padding: '3px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'background var(--transition-fast)',
          }}
          title="Select book for bulk editing"
        >
          <input
            type="checkbox"
            checked={isChecked}
            onChange={() => onToggleCheck?.()}
            style={{ margin: 0, cursor: 'pointer', display: 'block' }}
          />
        </div>

        {/* Quick Edit Pencil Button */}
        <button
          onClick={handleStartEdit}
          style={{
            position: 'absolute',
            top: '6px',
            right: book.is_indexed ? '64px' : '6px',
            zIndex: 10,
            background: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
            borderRadius: '4px',
            padding: '4px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
          title="Edit metadata in place"
        >
          <Pencil size={11} />
        </button>

        {/* AI Indexed Badge */}
        {book.is_indexed && (
          <div
            style={{
              position: 'absolute',
              top: '6px',
              right: '6px',
              background: 'rgba(37, 99, 235, 0.9)',
              backdropFilter: 'blur(4px)',
              borderRadius: 'var(--radius-full)',
              padding: '3px 6px',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              fontSize: '10px',
              fontWeight: 700,
              boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
            }}
            title="Indexed for RAG semantic search"
          >
            <Sparkles size={10} />
            <span>RAG</span>
          </div>
        )}
      </div>

      {/* Book Metadata */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', flex: 1 }}>
        <h4
          style={{
            fontSize: '13px',
            fontWeight: 600,
            lineHeight: 1.3,
            color: 'var(--text-primary)',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
          title={book.title}
        >
          {book.title}
        </h4>

        <div
          style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
          title={book.authors.join(', ')}
        >
          {book.authors.join(', ')}
        </div>

        {/* Series Badge */}
        {book.series && (
          <div
            style={{
              fontSize: '11px',
              color: 'var(--accent-primary)',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            title={`${book.series} #${book.series_index || 1}`}
          >
            {book.series} #{book.series_index || 1}
          </div>
        )}

        {/* Custom read_status Badge */}
        {book.custom_values?.read_status && (
          <div style={{ marginTop: '2px' }}>
            <span
              style={{
                fontSize: '9.5px',
                fontWeight: 600,
                padding: '1px 5px',
                borderRadius: '3px',
                background:
                  book.custom_values.read_status === 'Reading'
                    ? 'rgba(59, 130, 246, 0.15)'
                    : book.custom_values.read_status === 'Completed'
                    ? 'rgba(16, 185, 129, 0.15)'
                    : 'var(--bg-surface-elevated)',
                color:
                  book.custom_values.read_status === 'Reading'
                    ? '#3b82f6'
                    : book.custom_values.read_status === 'Completed'
                    ? '#10b981'
                    : 'var(--text-muted)',
              }}
            >
              {book.custom_values.read_status}
            </span>
          </div>
        )}

        {/* Formats and Rating Footer */}
        <div
          style={{
            marginTop: 'auto',
            paddingTop: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Format Chips */}
          <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
            {book.formats.map((f) => (
              <span
                key={f.format}
                style={{
                  fontSize: '9.5px',
                  fontWeight: 700,
                  padding: '1px 5px',
                  borderRadius: '3px',
                  background: 'var(--bg-surface-elevated)',
                  color: 'var(--text-muted)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                {f.format}
              </span>
            ))}
          </div>

          {/* Star Rating */}
          {book.rating && book.rating > 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '2px', color: '#eab308' }}>
              <Star size={11} fill="#eab308" />
              <span style={{ fontSize: '11px', fontWeight: 600 }}>{book.rating / 2}</span>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
