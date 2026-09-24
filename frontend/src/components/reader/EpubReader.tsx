import React, { useEffect, useRef, useState } from 'react';
import ePub from 'epubjs';
import type { Book as EpubBookInstance, Rendition } from 'epubjs';
import {
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Sparkles,
  X,
} from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';

interface EpubReaderProps {
  bookId: number;
  targetLocation?: string | null;
  onProgressUpdate?: (percent: number) => void;
}

interface SelectionPopover {
  cfiRange: string;
  text: string;
  x: number;
  y: number;
}

export const EpubReader: React.FC<EpubReaderProps> = ({
  bookId,
  targetLocation,
  onProgressUpdate,
}) => {
  const {
    readerTheme,
    readerFontSize,
    readerLayout,
    readerProgress,
    readerAnnotations,
    saveProgress,
    addAnnotation,
    toggleReaderAI,
    closeReader,
  } = useStore();

  const viewerRef = useRef<HTMLDivElement>(null);
  const bookRef = useRef<EpubBookInstance | null>(null);
  const renditionRef = useRef<Rendition | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [popover, setPopover] = useState<SelectionPopover | null>(null);
  const [noteInput, setNoteInput] = useState<string>('');
  const [showNoteInput, setShowNoteInput] = useState<boolean>(false);
  const [chosenColor, setChosenColor] = useState<string>('yellow');

  const highlightColors = [
    { name: 'yellow', hex: '#fde047' },
    { name: 'green', hex: '#86efac' },
    { name: 'blue', hex: '#93c5fd' },
    { name: 'pink', hex: '#f472b6' },
    { name: 'purple', hex: '#c084fc' },
  ];

  // Theme color maps
  const themeColors = {
    light: { bg: '#ffffff', text: '#1f2937' },
    sepia: { bg: '#fbf0d9', text: '#5f4b32' },
    dark: { bg: '#182030', text: '#cbd5e1' },
    black: { bg: '#000000', text: '#e2e8f0' },
  }[readerTheme];

  // Listen for Escape key on window
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeReader();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeReader]);

  useEffect(() => {
    if (!viewerRef.current) return;

    let isCancelled = false;
    setIsLoaded(false);
    setError(null);

    // Destroy previous book instance if any
    try {
      bookRef.current?.destroy();
    } catch (e) {}

    const downloadUrl = api.getBookDownloadUrl(bookId, 'EPUB');

    // Fetch EPUB as ArrayBuffer so epubjs unpacks the zip binary in-memory
    fetch(downloadUrl)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: Failed to download book`);
        }
        return res.arrayBuffer();
      })
      .then((buffer) => {
        if (isCancelled || !viewerRef.current) return;

        viewerRef.current.innerHTML = '';

        const ePubFn = typeof ePub === 'function' ? ePub : (ePub as any).default || ePub;
        const book = ePubFn(buffer);
        bookRef.current = book;

        const rendition = book.renderTo(viewerRef.current, {
          width: '100%',
          height: '100%',
          flow: readerLayout === 'scrolled' ? 'scrolled-doc' : 'paginated',
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
          '::selection': {
            background: 'rgba(99, 102, 241, 0.3) !important',
          },
        });

        // Determine initial location (backend progress takes precedence over localStorage)
        const initialLocation =
          targetLocation ||
          readerProgress?.location ||
          localStorage.getItem(`xbook_progress_${bookId}`) ||
          undefined;

        rendition.display(initialLocation).then(() => {
          if (!isCancelled) {
            setIsLoaded(true);
          }
        }).catch(() => {
          // If CFI was invalid or mismatch, fallback to first chapter
          rendition.display().then(() => {
            if (!isCancelled) {
              setIsLoaded(true);
            }
          });
        });

        // Locations generation for percentage calculation
        book.ready.then(() => {
          book.locations.generate(1024).then(() => {
            rendition.on('relocated', (location: any) => {
              if (location && location.start) {
                const percent = Math.round(book.locations.percentageFromCfi(location.start.cfi) * 100);
                localStorage.setItem(`xbook_progress_${bookId}`, location.start.cfi);
                if (onProgressUpdate) {
                  onProgressUpdate(percent);
                }
                saveProgress(location.start.cfi, percent, 5);
              }
            });
          }).catch((err: any) => console.warn('Location generation skipped:', err));
        });

        // Selection listener for highlights
        rendition.on('selected', (cfiRange: string, _contents: any) => {
          book.getRange(cfiRange).then((range: Range) => {
            const text = range.toString().trim();
            if (!text) return;
            const rect = range.getBoundingClientRect();
            setPopover({
              cfiRange,
              text,
              x: Math.min(window.innerWidth - 260, Math.max(20, rect.left)),
              y: Math.max(60, rect.top - 50),
            });
            setShowNoteInput(false);
          });
        });

        // Keyboard navigation inside iframe: handles Arrow keys AND Escape key
        rendition.on('keydown', (e: KeyboardEvent) => {
          if (e.key === 'Escape') {
            closeReader();
            return;
          }
          if (e.key === 'ArrowRight') rendition.next();
          if (e.key === 'ArrowLeft') rendition.prev();
        });
      })
      .catch((err: any) => {
        if (!isCancelled) {
          console.error('Failed to load EPUB:', err);
          setError(err.message || 'Failed to open book');
        }
      });

    return () => {
      isCancelled = true;
      try {
        bookRef.current?.destroy();
      } catch (e) {}
    };
  }, [bookId, readerLayout]);

  // Jump to targetLocation when changed externally
  useEffect(() => {
    if (targetLocation && renditionRef.current) {
      renditionRef.current.display(targetLocation);
    }
  }, [targetLocation]);

  // Render highlights onto the text
  useEffect(() => {
    if (!renditionRef.current || !isLoaded) return;
    readerAnnotations.forEach((ann) => {
      try {
        renditionRef.current?.annotations.add(
          'highlight',
          ann.location,
          {},
          () => {},
          'xbook-highlight',
          {
            fill: ann.color === 'yellow' ? '#fde047' : ann.color,
            'fill-opacity': '0.35',
            'mix-blend-mode': 'multiply',
          }
        );
      } catch (err) {}
    });
  }, [readerAnnotations, isLoaded]);

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

  const handleApplyHighlight = (color: string) => {
    if (!popover) return;
    setChosenColor(color);
    addAnnotation({
      format: 'EPUB',
      location: popover.cfiRange,
      selected_text: popover.text,
      color,
      note_text: noteInput.trim() || undefined,
    });
    setPopover(null);
    setNoteInput('');
    setShowNoteInput(false);
  };

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

      {!isLoaded && !error && (
        <div style={{ position: 'absolute', color: themeColors.text, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '16px', height: '16px', border: '2px solid rgba(125,125,125,0.3)', borderTopColor: 'var(--accent-primary, #6366f1)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
          <span>Loading book text...</span>
        </div>
      )}

      {error && (
        <div
          style={{
            position: 'absolute',
            color: '#ef4444',
            fontSize: '13.5px',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            padding: '16px 24px',
            borderRadius: '10px',
            textAlign: 'center',
            boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
            maxWidth: '420px',
            zIndex: 10,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '6px' }}>Unable to load EPUB</div>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '12px' }}>{error}</div>
          <button
            className="btn btn-secondary"
            onClick={closeReader}
            style={{ fontSize: '12px', padding: '4px 12px' }}
          >
            Return to Library (Esc)
          </button>
        </div>
      )}

      {/* Text Selection Popover */}
      {popover && (
        <div
          style={{
            position: 'fixed',
            left: `${popover.x}px`,
            top: `${popover.y}px`,
            background: '#0f172a',
            borderRadius: '8px',
            padding: '8px 12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
            border: '1px solid rgba(255,255,255,0.15)',
            zIndex: 1000,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Highlight:</span>
            {highlightColors.map((c) => (
              <button
                key={c.name}
                onClick={() => handleApplyHighlight(c.name)}
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: c.hex,
                  border: 'none',
                  cursor: 'pointer',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                }}
                title={`Highlight with ${c.name}`}
              />
            ))}
            <div style={{ width: '1px', height: '18px', background: 'rgba(255,255,255,0.15)' }} />
            <button
              onClick={() => setShowNoteInput(!showNoteInput)}
              style={{
                background: 'none',
                border: 'none',
                color: '#818cf8',
                cursor: 'pointer',
                padding: '2px',
              }}
              title="Add Note"
            >
              <MessageSquare size={16} />
            </button>
            <button
              onClick={() => {
                toggleReaderAI();
                setPopover(null);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: '#38bdf8',
                cursor: 'pointer',
                padding: '2px',
              }}
              title="Ask AI Context"
            >
              <Sparkles size={16} />
            </button>
            <button
              onClick={() => setPopover(null)}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                padding: '2px',
              }}
            >
              <X size={14} />
            </button>
          </div>

          {showNoteInput && (
            <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
              <input
                type="text"
                placeholder="Attach a note..."
                value={noteInput}
                onChange={(e) => setNoteInput(e.target.value)}
                autoFocus
                style={{
                  background: 'rgba(255,255,255,0.08)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '12px',
                  padding: '4px 8px',
                  outline: 'none',
                  width: '180px',
                }}
              />
              <button
                onClick={() => handleApplyHighlight(chosenColor)}
                style={{
                  background: '#4f46e5',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '11px',
                  padding: '4px 8px',
                  cursor: 'pointer',
                }}
              >
                Save
              </button>
            </div>
          )}
        </div>
      )}

      {/* Navigation Floating Buttons */}
      {readerLayout !== 'scrolled' && (
        <>
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
              background: 'rgba(0,0,0,0.25)',
              color: themeColors.text,
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(8px)',
              cursor: 'pointer',
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
              background: 'rgba(0,0,0,0.25)',
              color: themeColors.text,
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(8px)',
              cursor: 'pointer',
            }}
            title="Next Page"
          >
            <ChevronRight size={20} />
          </button>
        </>
      )}
    </div>
  );
};
