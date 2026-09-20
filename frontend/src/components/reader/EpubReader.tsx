import React, { useEffect, useRef, useState } from 'react';
import ePub from 'epubjs';
import type { Book as EpubBookInstance, Rendition } from 'epubjs';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';

interface EpubReaderProps {
  bookId: number;
  onProgressUpdate?: (percent: number) => void;
}

export const EpubReader: React.FC<EpubReaderProps> = ({
  bookId,
  onProgressUpdate,
}) => {
  const { readerTheme, readerFontSize } = useStore();
  const viewerRef = useRef<HTMLDivElement>(null);
  const bookRef = useRef<EpubBookInstance | null>(null);
  const renditionRef = useRef<Rendition | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Theme color maps
  const themeColors = {
    light: { bg: '#ffffff', text: '#1f2937' },
    sepia: { bg: '#fbf0d9', text: '#5f4b32' },
    dark: { bg: '#182030', text: '#cbd5e1' },
    black: { bg: '#000000', text: '#e2e8f0' },
  }[readerTheme];

  useEffect(() => {
    if (!viewerRef.current) return;

    const downloadUrl = api.getBookDownloadUrl(bookId, 'EPUB');
    const book = ePub(downloadUrl);
    bookRef.current = book;

    const rendition = book.renderTo(viewerRef.current, {
      width: '100%',
      height: '100%',
      flow: 'paginated',
      spread: 'auto',
    });
    renditionRef.current = rendition;

    // Apply styles
    rendition.themes.default({
      body: {
        background: `${themeColors.bg} !important`,
        color: `${themeColors.text} !important`,
        'font-size': `${readerFontSize}px !important`,
        'line-height': '1.7 !important',
        'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Georgia, serif !important',
      },
      p: {
        'margin-bottom': '1.2em !important',
      },
    });

    const savedCfi = localStorage.getItem(`xbook_progress_${bookId}`);
    rendition.display(savedCfi || undefined).then(() => {
      setIsLoaded(true);
    });

    book.ready.then(() => {
      book.locations.generate(1024).then(() => {
        rendition.on('relocated', (location: any) => {
          if (location && location.start) {
            const percent = book.locations.percentageFromCfi(location.start.cfi);
            localStorage.setItem(`xbook_progress_${bookId}`, location.start.cfi);
            if (onProgressUpdate) {
              onProgressUpdate(Math.round(percent * 100));
            }
          }
        });
      });
    });

    return () => {
      book.destroy();
    };
  }, [bookId]);

  // Update theme & font size when store changes
  useEffect(() => {
    if (!renditionRef.current) return;
    renditionRef.current.themes.default({
      body: {
        background: `${themeColors.bg} !important`,
        color: `${themeColors.text} !important`,
        'font-size': `${readerFontSize}px !important`,
      },
    });
  }, [readerTheme, readerFontSize, themeColors]);

  const handlePrev = () => renditionRef.current?.prev();
  const handleNext = () => renditionRef.current?.next();

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        background: themeColors.bg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Viewer Mount Point */}
      <div
        ref={viewerRef}
        style={{
          width: '100%',
          maxWidth: '900px',
          height: '100%',
          margin: '0 auto',
        }}
      />

      {!isLoaded && (
        <div style={{ position: 'absolute', color: themeColors.text, fontSize: '13px' }}>
          Loading EPUB renderer...
        </div>
      )}

      {/* Navigation Floating Buttons */}
      <button
        className="btn-icon"
        onClick={handlePrev}
        style={{
          position: 'absolute',
          left: '16px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: 'rgba(0,0,0,0.2)',
          color: themeColors.text,
          border: '1px solid rgba(255,255,255,0.1)',
          backdropFilter: 'blur(8px)',
        }}
        title="Previous Page"
      >
        <ChevronLeft size={20} />
      </button>

      <button
        className="btn-icon"
        onClick={handleNext}
        style={{
          position: 'absolute',
          right: '16px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: 'rgba(0,0,0,0.2)',
          color: themeColors.text,
          border: '1px solid rgba(255,255,255,0.1)',
          backdropFilter: 'blur(8px)',
        }}
        title="Next Page"
      >
        <ChevronRight size={20} />
      </button>
    </div>
  );
};
