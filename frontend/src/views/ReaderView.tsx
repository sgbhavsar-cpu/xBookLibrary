import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  BookOpen,
  Highlighter,
  Minus,
  Plus,
  Scroll,
  Sparkles,
  SplitSquareVertical,
} from 'lucide-react';
import { api } from '../api/client';
import { AnnotationsDrawer } from '../components/reader/AnnotationsDrawer';
import { ComicReader } from '../components/reader/ComicReader';
import { EpubReader } from '../components/reader/EpubReader';
import { PdfReader } from '../components/reader/PdfReader';
import { ReaderAIAssistant } from '../components/reader/ReaderAIAssistant';
import { useStore } from '../store/useStore';
import type { Book } from '../types';

export const ReaderView: React.FC = () => {
  const {
    readerBookId,
    readerFormat,
    readerTheme,
    setReaderTheme,
    readerFontSize,
    setReaderFontSize,
    readerLayout,
    setReaderLayout,
    readerProgress,
    readerAnnotations,
    isAnnotationsDrawerOpen,
    toggleAnnotationsDrawer,
    closeReader,
    toggleReaderAI,
    isReaderAIOpen,
  } = useStore();

  const [book, setBook] = useState<Book | null>(null);
  const [targetLocation, setTargetLocation] = useState<string | null>(null);

  useEffect(() => {
    if (!readerBookId) return;
    api
      .getBook(readerBookId)
      .then(setBook)
      .catch((err) => console.error('Failed to load reader book:', err));
  }, [readerBookId]);

  if (!readerBookId || !book) {
    return (
      <div
        style={{
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-app)',
          color: 'var(--text-secondary)',
        }}
      >
        Loading reader...
      </div>
    );
  }

  const fmt = (readerFormat || 'EPUB').toUpperCase();
  const isEpub = fmt === 'EPUB';
  const isPdf = fmt === 'PDF';
  const isComic = fmt === 'CBZ' || fmt === 'CBR';

  const progressPercent = Math.round(readerProgress?.progress_percent || 0);

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
        background: 'var(--bg-app)',
      }}
    >
      {/* Reader Top Header Bar */}
      <header
        className="glass-panel"
        style={{
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 1rem',
          zIndex: 40,
          borderBottom: '1px solid var(--border-default)',
        }}
      >
        {/* Left: Return & Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            className="btn-icon"
            onClick={closeReader}
            title="Back to Library"
          >
            <ArrowLeft size={16} />
          </button>

          <div>
            <div style={{ fontWeight: 600, fontSize: '13.5px', color: 'var(--text-primary)' }}>
              {book.title}
            </div>
            <div style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
              {book.authors.join(', ')} &bull; {fmt}
            </div>
          </div>
        </div>

        {/* Center: Reading Progress Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '160px' }}>
          <div
            style={{
              flex: 1,
              height: '6px',
              borderRadius: 'var(--radius-full)',
              background: 'var(--border-default)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${progressPercent}%`,
                height: '100%',
                background: 'var(--accent-primary)',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
          <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text-muted)' }}>
            {progressPercent}%
          </span>
        </div>

        {/* Right Controls: Themes, Font Size, Notes, AI Assistant */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Layout Mode (EPUB only) */}
          {isEpub && (
            <button
              className="btn-icon"
              onClick={() => setReaderLayout(readerLayout === 'paginated' ? 'scrolled' : 'paginated')}
              title={`Switch to ${readerLayout === 'paginated' ? 'Continuous Scroll' : 'Paginated'} mode`}
              style={{
                background: readerLayout === 'scrolled' ? 'var(--accent-surface)' : undefined,
                color: readerLayout === 'scrolled' ? 'var(--accent-primary)' : undefined,
              }}
            >
              {readerLayout === 'paginated' ? <SplitSquareVertical size={15} /> : <Scroll size={15} />}
            </button>
          )}

          {/* Themes (EPUB only) */}
          {isEpub && (
            <div
              style={{
                display: 'flex',
                gap: '4px',
                background: 'var(--bg-surface-elevated)',
                padding: '2px',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              {(['light', 'sepia', 'dark', 'black'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setReaderTheme(t)}
                  style={{
                    width: '22px',
                    height: '22px',
                    borderRadius: 'var(--radius-xs)',
                    border:
                      readerTheme === t
                        ? '2px solid var(--accent-primary)'
                        : '1px solid transparent',
                    background:
                      t === 'light'
                        ? '#ffffff'
                        : t === 'sepia'
                        ? '#fbf0d9'
                        : t === 'dark'
                        ? '#1e293b'
                        : '#000000',
                    cursor: 'pointer',
                  }}
                  title={`${t.charAt(0).toUpperCase() + t.slice(1)} theme`}
                />
              ))}
            </div>
          )}

          {/* Font Size Steppers (EPUB only) */}
          {isEpub && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
              <button
                className="btn-icon"
                onClick={() => setReaderFontSize(Math.max(12, readerFontSize - 2))}
                title="Decrease font size"
                style={{ width: '26px', height: '26px' }}
              >
                <Minus size={12} />
              </button>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  minWidth: '22px',
                  textAlign: 'center',
                }}
              >
                {readerFontSize}
              </span>
              <button
                className="btn-icon"
                onClick={() => setReaderFontSize(Math.min(36, readerFontSize + 2))}
                title="Increase font size"
                style={{ width: '26px', height: '26px' }}
              >
                <Plus size={12} />
              </button>
            </div>
          )}

          {/* Highlights & Notes Drawer Toggle */}
          <button
            className="btn btn-secondary"
            onClick={toggleAnnotationsDrawer}
            style={{
              borderColor: isAnnotationsDrawerOpen ? 'var(--accent-primary)' : undefined,
              background: isAnnotationsDrawerOpen ? 'var(--accent-surface)' : undefined,
              color: isAnnotationsDrawerOpen ? 'var(--accent-primary)' : undefined,
              padding: '6px 10px',
              fontSize: '12px',
              gap: '6px',
            }}
            title="Toggle Notes & Bookmarks Drawer"
          >
            <Highlighter size={13} />
            <span>Notes</span>
            {readerAnnotations.length > 0 && (
              <span
                style={{
                  fontSize: '10px',
                  background: 'var(--accent-primary)',
                  color: '#fff',
                  borderRadius: '10px',
                  padding: '1px 5px',
                  fontWeight: 600,
                }}
              >
                {readerAnnotations.length}
              </span>
            )}
          </button>

          {/* In-Reader AI Assistant Launcher */}
          <button
            className="btn btn-secondary"
            onClick={toggleReaderAI}
            style={{
              borderColor: isReaderAIOpen ? 'var(--accent-primary)' : undefined,
              background: isReaderAIOpen ? 'var(--accent-surface)' : undefined,
              color: isReaderAIOpen ? 'var(--accent-primary)' : undefined,
              padding: '6px 10px',
              fontSize: '12px',
            }}
          >
            <Sparkles size={13} color="var(--accent-primary)" />
            <span>AI Lookup</span>
          </button>
        </div>
      </header>

      {/* Main Reading Canvas */}
      <main style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        <div style={{ flex: 1, position: 'relative', height: '100%', overflow: 'hidden' }}>
          {isEpub && (
            <EpubReader
              bookId={book.id}
              targetLocation={targetLocation}
            />
          )}

          {isPdf && (
            <PdfReader
              bookId={book.id}
              targetLocation={targetLocation}
            />
          )}

          {isComic && (
            <ComicReader bookId={book.id} />
          )}

          {!isEpub && !isPdf && !isComic && (
            <div
              style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
              }}
            >
              <BookOpen size={48} color="var(--text-muted)" />
              <h3>Direct web preview is supported for EPUB, PDF, and CBZ/CBR comic books</h3>
              <a
                href={api.getBookDownloadUrl(book.id, fmt)}
                download
                className="btn btn-primary"
              >
                Download {fmt} File
              </a>
            </div>
          )}
        </div>

        {/* Collapsible Highlights & Notes Drawer */}
        {isAnnotationsDrawerOpen && (
          <AnnotationsDrawer
            bookId={book.id}
            onNavigateToLocation={(loc) => setTargetLocation(loc)}
          />
        )}

        {/* Collapsible Book AI Assistant Sidebar */}
        <ReaderAIAssistant bookId={book.id} bookTitle={book.title} />
      </main>
    </div>
  );
};

export default ReaderView;
