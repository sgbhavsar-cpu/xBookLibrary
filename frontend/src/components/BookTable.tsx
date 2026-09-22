import React, { useMemo, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Check, Loader2, Pencil, Star, X } from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import type { Book } from '../types';
import { filterBooks } from '../utils/filterBooks';

export const BookTable: React.FC = () => {
  const {
    books,
    searchQuery,
    tagTreeFilter,
    selectedTaxonomyPath,
    selectedAuthor,
    selectedFormat,
    selectedSeries,
    activeVirtualLibrary,
    virtualLibraries,
    selectedBookId,
    selectBook,
    openReader,
    selectedBookIds,
    toggleSelectBookId,
    selectAllBooks,
    clearSelectedBooks,
    loadBooks,
    setToastMessage,
  } = useStore();

  const parentRef = useRef<HTMLDivElement>(null);

  // In-place editing state
  const [editingBookId, setEditingBookId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editAuthors, setEditAuthors] = useState('');
  const [editSeries, setEditSeries] = useState('');
  const [editSeriesIndex, setEditSeriesIndex] = useState<number>(1.0);
  const [editRating, setEditRating] = useState<number>(0);
  const [isSaving, setIsSaving] = useState(false);

  // Filter books matching search & filters
  const filteredBooks = useMemo(() => {
    return filterBooks(books, {
      searchQuery,
      tagTreeFilter,
      activeVirtualLibrary,
      virtualLibraries,
      selectedAuthor,
      selectedFormat,
      selectedSeries,
      selectedTaxonomyPath,
    });
  }, [
    books,
    searchQuery,
    tagTreeFilter,
    selectedAuthor,
    selectedFormat,
    selectedTaxonomyPath,
    selectedSeries,
    activeVirtualLibrary,
    virtualLibraries,
  ]);

  const rowVirtualizer = useVirtualizer({
    count: filteredBooks.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48,
    overscan: 5,
  });

  const handleStartEdit = (b: Book, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setEditingBookId(b.id);
    setEditTitle(b.title || '');
    setEditAuthors(b.authors ? b.authors.join(', ') : '');
    setEditSeries(b.series || '');
    setEditSeriesIndex(b.series_index ?? 1.0);
    setEditRating(b.custom_values?.rating ?? b.rating ?? 0);
  };

  const handleCancelEdit = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setEditingBookId(null);
  };

  const handleSaveEdit = async (bookId: number, e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (!editTitle.trim()) return;
    setIsSaving(true);

    try {
      const parsedAuthors = editAuthors
        .split(',')
        .map((a) => a.trim())
        .filter(Boolean);

      await api.updateBookMetadata(bookId, {
        title: editTitle.trim(),
        authors: parsedAuthors.length > 0 ? parsedAuthors : undefined,
        series_name: editSeries.trim() || undefined,
        series_index: editSeries.trim() ? editSeriesIndex : undefined,
        rating: editRating > 0 ? editRating : undefined,
      });

      setToastMessage('Row metadata updated in place');
      await loadBooks();
      setEditingBookId(null);
    } catch (err: any) {
      alert(err.message || 'Failed to update metadata');
    } finally {
      setIsSaving(false);
    }
  };

  const allSelected =
    filteredBooks.length > 0 &&
    filteredBooks.every((b) => selectedBookIds.includes(b.id));

  return (
    <div
      ref={parentRef}
      style={{
        flex: 1,
        height: 'calc(100vh - var(--header-height) - var(--status-bar-height))',
        overflowY: 'auto',
        position: 'relative',
      }}
    >
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '13px',
          textAlign: 'left',
        }}
      >
        <thead
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 10,
            background: 'var(--bg-surface-elevated)',
            borderBottom: '1px solid var(--border-default)',
            color: 'var(--text-secondary)',
            fontSize: '11px',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          <tr style={{ display: 'flex', alignItems: 'center' }}>
            <th
              style={{
                width: '40px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '8px 12px',
              }}
            >
              <input
                type="checkbox"
                checked={allSelected}
                onChange={() => {
                  if (allSelected) {
                    clearSelectedBooks();
                  } else {
                    selectAllBooks();
                  }
                }}
                className="cursor-pointer rounded"
                title="Select all books"
              />
            </th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '28%' }}>Title</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '18%' }}>Authors</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '15%' }}>Series</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '14%' }}>Classification</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '9%' }}>Formats</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '9%' }}>Rating</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '70px', textAlign: 'center' }}>Actions</th>
          </tr>
        </thead>
        <tbody
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            position: 'relative',
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const b = filteredBooks[virtualRow.index];
            const isSelected = b.id === selectedBookId;
            const isChecked = selectedBookIds.includes(b.id);
            const isRowEditing = editingBookId === b.id;

            return (
              <tr
                key={b.id}
                onClick={(e) => {
                  if (isRowEditing) return;
                  if (e.shiftKey || e.ctrlKey || e.metaKey) {
                    toggleSelectBookId(b.id);
                  }
                  selectBook(b.id);
                }}
                onDoubleClick={() => {
                  if (isRowEditing) return;
                  const primary =
                    b.formats.find((f) =>
                      ['EPUB', 'PDF', 'CBZ', 'CBR', 'MP3', 'M4B'].includes(f.format.toUpperCase())
                    ) || b.formats[0];
                  openReader(b.id, primary?.format);
                }}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                  display: 'flex',
                  alignItems: 'center',
                  background: isRowEditing
                    ? 'var(--bg-card)'
                    : isChecked
                    ? 'rgba(99, 102, 241, 0.15)'
                    : isSelected
                    ? 'var(--accent-surface)'
                    : undefined,
                  borderBottom: '1px solid var(--border-subtle)',
                  boxShadow: isRowEditing ? '0 0 0 1px var(--accent-primary) inset' : undefined,
                  cursor: isRowEditing ? 'default' : 'pointer',
                  transition: 'background var(--transition-fast)',
                }}
              >
                {/* Checkbox */}
                <td
                  style={{
                    width: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0 12px',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleSelectBookId(b.id)}
                    className="cursor-pointer rounded"
                  />
                </td>

                {/* Title */}
                <td
                  style={{
                    padding: '0 12px',
                    width: '28%',
                    fontWeight: 500,
                    color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={b.title}
                >
                  {isRowEditing ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      autoFocus
                      className="input-text"
                      style={{ fontSize: '12px', padding: '3px 6px' }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveEdit(b.id);
                        if (e.key === 'Escape') handleCancelEdit();
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    b.title
                  )}
                </td>

                {/* Authors */}
                <td
                  style={{
                    padding: '0 12px',
                    width: '18%',
                    color: 'var(--text-secondary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={b.authors.join(', ')}
                >
                  {isRowEditing ? (
                    <input
                      type="text"
                      value={editAuthors}
                      onChange={(e) => setEditAuthors(e.target.value)}
                      className="input-text"
                      style={{ fontSize: '11px', padding: '3px 6px' }}
                      placeholder="Author(s)..."
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveEdit(b.id);
                        if (e.key === 'Escape') handleCancelEdit();
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    b.authors.join(', ')
                  )}
                </td>

                {/* Series */}
                <td
                  style={{
                    padding: '0 12px',
                    width: '15%',
                    color: 'var(--accent-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    fontSize: '12px',
                    fontWeight: 500,
                  }}
                  title={b.series ? `${b.series} #${b.series_index || 1}` : ''}
                >
                  {isRowEditing ? (
                    <div style={{ display: 'flex', gap: '3px' }} onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editSeries}
                        onChange={(e) => setEditSeries(e.target.value)}
                        className="input-text"
                        style={{ fontSize: '11px', padding: '3px 4px', flex: 1 }}
                        placeholder="Series..."
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(b.id);
                          if (e.key === 'Escape') handleCancelEdit();
                        }}
                      />
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        value={editSeriesIndex}
                        onChange={(e) => setEditSeriesIndex(parseFloat(e.target.value) || 1.0)}
                        className="input-text"
                        style={{ fontSize: '11px', padding: '3px 2px', width: '36px', textAlign: 'center' }}
                      />
                    </div>
                  ) : b.series ? (
                    `${b.series} #${b.series_index || 1}`
                  ) : (
                    '-'
                  )}
                </td>

                {/* Classification */}
                <td
                  style={{
                    padding: '0 12px',
                    width: '14%',
                    color: 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    fontSize: '12px',
                  }}
                >
                  {b.classification?.bisac_heading || '-'}
                </td>

                {/* Formats */}
                <td style={{ padding: '0 12px', width: '9%', display: 'flex', gap: '3px' }}>
                  {b.formats.map((f) => (
                    <span
                      key={f.format}
                      style={{
                        fontSize: '9.5px',
                        fontWeight: 700,
                        padding: '1px 4px',
                        borderRadius: '3px',
                        background: 'var(--bg-surface-elevated)',
                        color: 'var(--text-muted)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      {f.format}
                    </span>
                  ))}
                </td>

                {/* Rating */}
                <td style={{ padding: '0 12px', width: '9%' }} onClick={(e) => isRowEditing && e.stopPropagation()}>
                  {isRowEditing ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setEditRating(editRating === star ? 0 : star)}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '1px',
                            color: star <= editRating ? '#eab308' : 'var(--text-muted)',
                          }}
                        >
                          <Star size={13} fill={star <= editRating ? '#eab308' : 'none'} />
                        </button>
                      ))}
                    </div>
                  ) : b.rating && b.rating > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#eab308' }}>
                      <Star size={12} fill="#eab308" />
                      <span style={{ fontSize: '11px', fontWeight: 600 }}>{b.rating / 2}</span>
                    </div>
                  ) : (
                    '-'
                  )}
                </td>

                {/* Actions */}
                <td
                  style={{
                    padding: '0 8px',
                    width: '70px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {isRowEditing ? (
                    <>
                      <button
                        onClick={(e) => handleSaveEdit(b.id, e)}
                        disabled={isSaving}
                        className="btn-icon"
                        style={{ width: '24px', height: '24px', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.4)' }}
                        title="Save Changes"
                      >
                        {isSaving ? <Loader2 size={12} className="animate-spin" /> : <Check size={13} />}
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="btn-icon"
                        style={{ width: '24px', height: '24px', color: '#ef4444' }}
                        title="Cancel"
                      >
                        <X size={13} />
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={(e) => handleStartEdit(b, e)}
                      className="btn-icon"
                      style={{ width: '24px', height: '24px' }}
                      title="Edit row in place"
                    >
                      <Pencil size={12} />
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
