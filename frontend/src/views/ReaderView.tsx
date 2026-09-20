import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  BookOpen,
  Minus,
  Plus,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
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
    closeReader,
    toggleReaderAI,
    isReaderAIOpen,
  } = useStore();

  const [book, setBook] = useState<Book | null>(null);
  const [progressPercent, setProgressPercent] = useState(0);

  useEffect(() => {
    if (!readerBookId) return;
    api.getBook(readerBookId)
      .then(setBook)
      .catch((err) => console.error('Failed to load reader book:', err));
  }, [readerBookId]);

  if (!readerBookId || !book) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-app)',
        color: 'var(--text-secondary)',
      }}>
        Loading reader...
      </div>
    );
  }

  const isEpub = readerFormat?.toUpperCase() === 'EPUB';
  const isPdf = readerFormat?.toUpperCase() === 'PDF';

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
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
              {book.authors.join(', ')} &bull; {readerFormat}
            </div>
          </div>
        </div>

        {/* Center: Reading Progress */}
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

        {/* Right Controls: Theme, Font Size & AI Assistant */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Themes */}
          {isEpub && (
            <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-surface-elevated)', padding: '2px', borderRadius: 'var(--radius-sm)' }}>
              {(['light', 'sepia', 'dark', 'black'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setReaderTheme(t)}
                  style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: 'var(--radius-xs)',
                    border: readerTheme === t ? '2px solid var(--accent-primary)' : '1px solid transparent',
                    background: t === 'light' ? '#ffffff' : t === 'sepia' ? '#fbf0d9' : t === 'dark' ? '#1e293b' : '#000000',
                    cursor: 'pointer',
                  }}
                  title={`${t.charAt(0).toUpperCase() + t.slice(1)} reading theme`}
                />
              ))}
            </div>
          )}

          {/* Font Size Steppers */}
          {isEpub && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                className="btn-icon"
                onClick={() => setReaderFontSize(Math.max(12, readerFontSize - 2))}
                title="Decrease font size"
                style={{ width: '28px', height: '28px' }}
              >
                <Minus size={13} />
              </button>
              <span style={{ fontSize: '11px', fontWeight: 600, minWidth: '24px', textAlign: 'center' }}>
                {readerFontSize}
              </span>
              <button
                className="btn-icon"
                onClick={() => setReaderFontSize(Math.min(36, readerFontSize + 2))}
                title="Increase font size"
                style={{ width: '28px', height: '28px' }}
              >
                <Plus size={13} />
              </button>
            </div>
          )}

          {/* In-Reader AI Assistant Launcher */}
          <button
            className="btn btn-secondary"
            onClick={toggleReaderAI}
            style={{
              borderColor: isReaderAIOpen ? 'var(--accent-primary)' : undefined,
              background: isReaderAIOpen ? 'var(--accent-surface)' : undefined,
              color: isReaderAIOpen ? 'var(--accent-primary)' : undefined,
            }}
          >
            <Sparkles size={14} color="var(--accent-primary)" />
            <span>AI Assistant</span>
          </button>
        </div>
      </header>

      {/* Main Reading Canvas */}
      <main style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {isEpub && (
          <EpubReader
            bookId={book.id}
            onProgressUpdate={setProgressPercent}
          />
        )}

        {isPdf && (
          <PdfReader bookId={book.id} />
        )}

        {!isEpub && !isPdf && (
          <div style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
          }}>
            <BookOpen size={48} color="var(--text-muted)" />
            <h3>Direct preview is available for EPUB and PDF formats</h3>
            <a
              href={api.getBookDownloadUrl(book.id, readerFormat || 'EPUB')}
              download
              className="btn btn-primary"
            >
              Download {readerFormat} File
            </a>
          </div>
        )}

        {/* Collapsible Book AI Assistant Sidebar */}
        <ReaderAIAssistant bookId={book.id} bookTitle={book.title} />
      </main>
    </div>
  );
};
