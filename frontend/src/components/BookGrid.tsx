import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { SearchX } from 'lucide-react';
import { useStore } from '../store/useStore';
import { BookCard } from './BookCard';

export const BookGrid: React.FC = () => {
  const {
    books,
    searchQuery,
    selectedTaxonomyPath,
    selectedAuthor,
    selectedFormat,
    selectedSeries,
    selectedBookId,
    selectBook,
    openReader,
    isLoadingBooks,
    activeVirtualLibrary,
    virtualLibraries,
  } = useStore();

  const parentRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(800);

  // ResizeObserver to calculate column count dynamically
  useEffect(() => {
    if (!parentRef.current) return;
    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        setContainerWidth(entries[0].contentRect.width);
      }
    });
    observer.observe(parentRef.current);
    return () => observer.disconnect();
  }, []);

  // Filter books based on active criteria
  const filteredBooks = useMemo(() => {
    return books.filter((b) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = b.title.toLowerCase().includes(q);
        const matchesAuthor = b.authors.some((a) => a.toLowerCase().includes(q));
        const matchesTag = b.tags.some((t) => t.toLowerCase().includes(q));
        const matchesBisac = b.classification?.bisac_heading.toLowerCase().includes(q);
        if (!matchesTitle && !matchesAuthor && !matchesTag && !matchesBisac) {
          return false;
        }
      }

      // 2. Author Filter
      if (selectedAuthor && !b.authors.includes(selectedAuthor)) {
        return false;
      }

      // 3. Format Filter
      if (selectedFormat && !b.formats.some((f) => f.format === selectedFormat)) {
        return false;
      }

      // 4. Taxonomy Path Filter
      if (selectedTaxonomyPath) {
        const matchesHeading = b.classification?.bisac_heading
          .toLowerCase()
          .includes(selectedTaxonomyPath.toLowerCase());
        if (!matchesHeading) return false;
      }

      // 5. Series Filter
      if (selectedSeries && b.series !== selectedSeries) {
        return false;
      }

      // 6. Virtual Library Filter
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

  // Compute column count based on width: min 160px card width + gaps
  const columnCount = Math.max(1, Math.floor(containerWidth / 180));
  const rowCount = Math.ceil(filteredBooks.length / columnCount);

  // Virtualize rows
  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 320, // estimated card row height
    overscan: 3,
  });

  if (isLoadingBooks) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        gap: '8px',
      }}>
        <div style={{
          width: '24px',
          height: '24px',
          border: '3px solid var(--border-default)',
          borderTopColor: 'var(--accent-primary)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <span>Loading library catalog...</span>
      </div>
    );
  }

  if (filteredBooks.length === 0) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        gap: '12px',
        padding: '2rem',
      }}>
        <SearchX size={48} strokeWidth={1.5} />
        <h3 style={{ color: 'var(--text-primary)', fontWeight: 600 }}>No Books Match Your Filter</h3>
        <p style={{ fontSize: '13px', maxWidth: '360px', textAlign: 'center' }}>
          Try clearing your search terms, selecting a different taxonomy category, or importing new books.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      style={{
        flex: 1,
        height: 'calc(100vh - var(--header-height) - var(--status-bar-height))',
        overflowY: 'auto',
        padding: '1.25rem',
        position: 'relative',
      }}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const startIndex = virtualRow.index * columnCount;
          const rowBooks = filteredBooks.slice(startIndex, startIndex + columnCount);

          return (
            <div
              key={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
                display: 'grid',
                gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))`,
                gap: '16px',
                paddingBottom: '16px',
              }}
            >
              {rowBooks.map((b) => (
                <BookCard
                  key={b.id}
                  book={b}
                  isSelected={b.id === selectedBookId}
                  onSelect={() => selectBook(b.id)}
                  onDoubleClick={() => openReader(b.id)}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};
