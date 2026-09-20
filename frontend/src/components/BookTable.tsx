import React, { useMemo, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Star } from 'lucide-react';
import { useStore } from '../store/useStore';

export const BookTable: React.FC = () => {
  const {
    books,
    searchQuery,
    selectedTaxonomyPath,
    selectedAuthor,
    selectedFormat,
    selectedSeries,
    activeVirtualLibrary,
    virtualLibraries,
    selectedBookId,
    selectBook,
    openReader,
  } = useStore();

  const parentRef = useRef<HTMLDivElement>(null);

  // Filter books matching search & filters
  const filteredBooks = useMemo(() => {
    return books.filter((b) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = b.title.toLowerCase().includes(q);
        const matchesAuthor = b.authors.some((a) => a.toLowerCase().includes(q));
        const matchesBisac = b.classification?.bisac_heading.toLowerCase().includes(q);
        if (!matchesTitle && !matchesAuthor && !matchesBisac) return false;
      }
      if (selectedAuthor && !b.authors.includes(selectedAuthor)) return false;
      if (selectedFormat && !b.formats.some((f) => f.format === selectedFormat)) return false;
      if (selectedTaxonomyPath) {
        const matchesHeading = b.classification?.bisac_heading
          .toLowerCase()
          .includes(selectedTaxonomyPath.toLowerCase());
        if (!matchesHeading) return false;
      }

      // Series filter
      if (selectedSeries && b.series !== selectedSeries) return false;

      // Virtual library query filter
      if (activeVirtualLibrary) {
        const vl = virtualLibraries.find((v) => v.name === activeVirtualLibrary);
        if (vl && vl.query.trim()) {
          const q = vl.query.toLowerCase();
          if (q.includes('#read_status:')) {
            const expected = q.split('#read_status:')[1]?.split(' ')[0]?.replace(/["']/g, '');
            const current = (b.custom_values?.read_status || '').toLowerCase();
            if (expected && !current.includes(expected.toLowerCase())) return false;
          }
          if (q.includes('series:')) {
            const expected = q.split('series:')[1]?.split(' ')[0]?.replace(/["']/g, '');
            const current = (b.series || '').toLowerCase();
            if (expected && !current.includes(expected.toLowerCase())) return false;
          }
          if (q.includes('tag:') || q.includes('tags:')) {
            const match = q.match(/tags?:"?([^"\s]+)"?/);
            const expected = match ? match[1].toLowerCase() : '';
            if (expected && !b.tags.some((t) => t.toLowerCase().includes(expected))) return false;
          }
        }
      }

      return true;
    });
  }, [
    books,
    searchQuery,
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
    estimateSize: () => 40,
    overscan: 10,
  });

  return (
    <div
      ref={parentRef}
      style={{
        flex: 1,
        height: 'calc(100vh - var(--header-height) - var(--status-bar-height) - 40px)',
        overflowY: 'auto',
        background: 'var(--bg-surface)',
      }}
    >
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
        <thead
          style={{
            position: 'sticky',
            top: 0,
            background: 'var(--bg-surface-elevated)',
            zIndex: 10,
            borderBottom: '2px solid var(--border-default)',
            userSelect: 'none',
          }}
        >
          <tr>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '30%' }}>Title</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '20%' }}>Authors</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '15%' }}>Series</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '15%' }}>Classification</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '10%' }}>Formats</th>
            <th style={{ padding: '8px 16px', fontWeight: 600, width: '10%' }}>Rating</th>
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

            return (
              <tr
                key={b.id}
                onClick={() => selectBook(b.id)}
                onDoubleClick={() => openReader(b.id)}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                  display: 'flex',
                  alignItems: 'center',
                  background: isSelected ? 'var(--accent-surface)' : undefined,
                  borderBottom: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  transition: 'background var(--transition-fast)',
                }}
              >
                <td
                  style={{
                    padding: '0 16px',
                    width: '30%',
                    fontWeight: 500,
                    color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={b.title}
                >
                  {b.title}
                </td>
                <td
                  style={{
                    padding: '0 16px',
                    width: '20%',
                    color: 'var(--text-secondary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={b.authors.join(', ')}
                >
                  {b.authors.join(', ')}
                </td>
                <td
                  style={{
                    padding: '0 16px',
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
                  {b.series ? `${b.series} #${b.series_index || 1}` : '-'}
                </td>
                <td
                  style={{
                    padding: '0 16px',
                    width: '15%',
                    color: 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    fontSize: '12px',
                  }}
                >
                  {b.classification?.bisac_heading || '-'}
                </td>
                <td style={{ padding: '0 16px', width: '10%', display: 'flex', gap: '4px' }}>
                  {b.formats.map((f) => (
                    <span
                      key={f.format}
                      style={{
                        fontSize: '10px',
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
                <td style={{ padding: '0 16px', width: '10%' }}>
                  {b.rating && b.rating > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#eab308' }}>
                      <Star size={12} fill="#eab308" />
                      <span style={{ fontSize: '11px', fontWeight: 600 }}>{b.rating / 2}</span>
                    </div>
                  ) : (
                    '-'
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
