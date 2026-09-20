import React, { useState } from 'react';
import { Book as BookIcon, Sparkles, Star } from 'lucide-react';
import { api } from '../api/client';
import type { Book } from '../types';

interface BookCardProps {
  book: Book;
  isSelected: boolean;
  onSelect: () => void;
  onDoubleClick?: () => void;
}

export const BookCard: React.FC<BookCardProps> = ({
  book,
  isSelected,
  onSelect,
  onDoubleClick,
}) => {
  const [coverError, setCoverError] = useState(false);
  const coverUrl = api.getBookCoverUrl(book.id);

  return (
    <div
      className="glass-card"
      onClick={onSelect}
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
