import React, { useEffect, useRef, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';
import type { ComicManifest } from '../../types';

interface ComicReaderProps {
  bookId: number;
}

export const ComicReader: React.FC<ComicReaderProps> = ({ bookId }) => {
  const {
    activeLibraryId,
    readerComicMode,
    setReaderComicMode,
    readerProgress,
    saveProgress,
  } = useStore();

  const [manifest, setManifest] = useState<ComicManifest | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load manifest
  useEffect(() => {
    if (!activeLibraryId) return;
    setIsLoading(true);
    api
      .getComicManifest(activeLibraryId, bookId)
      .then((m) => {
        setManifest(m);
        // Resume from saved location if available
        if (readerProgress && readerProgress.location) {
          const savedIndex = parseInt(readerProgress.location, 10);
          if (!isNaN(savedIndex) && savedIndex >= 0 && savedIndex < m.total_pages) {
            setCurrentPage(savedIndex);
          }
        }
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load comic manifest:', err);
        setIsLoading(false);
      });
  }, [activeLibraryId, bookId]);

  // Sync progress on page change (debounced)
  useEffect(() => {
    if (!manifest || manifest.total_pages === 0) return;
    const timer = setTimeout(() => {
      const pct = Math.min(100, Math.round(((currentPage + 1) / manifest.total_pages) * 100));
      saveProgress(currentPage.toString(), pct, 5);
    }, 1000);
    return () => clearTimeout(timer);
  }, [currentPage, manifest]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (readerComicMode === 'webtoon') return;

      if (e.key === 'ArrowRight') {
        if (readerComicMode === 'rtl') {
          handlePrev();
        } else {
          handleNext();
        }
      } else if (e.key === 'ArrowLeft') {
        if (readerComicMode === 'rtl') {
          handleNext();
        } else {
          handlePrev();
        }
      } else if (e.key === 'f' || e.key === 'F') {
        toggleFullscreen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPage, manifest, readerComicMode]);

  const handleNext = () => {
    if (!manifest) return;
    if (currentPage < manifest.total_pages - 1) {
      setCurrentPage((p) => p + 1);
    }
  };

  const handlePrev = () => {
    if (currentPage > 0) {
      setCurrentPage((p) => p - 1);
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true));
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false));
    }
  };

  if (isLoading) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#94a3b8',
          fontSize: '15px',
        }}
      >
        Unpacking comic pages...
      </div>
    );
  }

  if (!manifest || manifest.total_pages === 0) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ef4444',
          fontSize: '15px',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <span>No image pages found in this comic archive.</span>
        <span style={{ fontSize: '13px', color: '#94a3b8' }}>
          Please verify the file contains standard JPEG, PNG, or WebP images.
        </span>
      </div>
    );
  }

  const currentImageUrl = activeLibraryId
    ? api.getComicPageUrl(activeLibraryId, bookId, currentPage)
    : '';

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        background: '#0a0d14',
        overflow: 'hidden',
        userSelect: 'none',
      }}
    >
      {/* Comic Mode Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 16px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
            {manifest.series_name ? `${manifest.series_name} ` : ''}
            {manifest.issue_number ? `#${manifest.issue_number}` : ''}
          </span>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>
            Page {currentPage + 1} of {manifest.total_pages}
          </span>
        </div>

        {/* Reading Mode Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            className={`btn-secondary ${readerComicMode === 'ltr' ? 'active' : ''}`}
            onClick={() => setReaderComicMode('ltr')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              background: readerComicMode === 'ltr' ? '#4f46e5' : 'rgba(255,255,255,0.06)',
              color: '#fff',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Left-to-Right
          </button>
          <button
            className={`btn-secondary ${readerComicMode === 'rtl' ? 'active' : ''}`}
            onClick={() => setReaderComicMode('rtl')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              background: readerComicMode === 'rtl' ? '#4f46e5' : 'rgba(255,255,255,0.06)',
              color: '#fff',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Manga (RTL)
          </button>
          <button
            className={`btn-secondary ${readerComicMode === 'webtoon' ? 'active' : ''}`}
            onClick={() => setReaderComicMode('webtoon')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              background: readerComicMode === 'webtoon' ? '#4f46e5' : 'rgba(255,255,255,0.06)',
              color: '#fff',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Webtoon
          </button>
          <button
            onClick={toggleFullscreen}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px',
              marginLeft: '8px',
            }}
            title="Toggle Fullscreen (F)"
          >
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>
      </div>

      {/* Main View Area */}
      {readerComicMode === 'webtoon' ? (
        // Webtoon continuous vertical scroll
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            background: '#090d16',
            padding: '16px 0',
          }}
        >
          {manifest.pages.map((p, idx) => (
            <img
              key={p.index}
              src={activeLibraryId ? api.getComicPageUrl(activeLibraryId, bookId, p.index) : ''}
              alt={`Page ${idx + 1}`}
              loading={idx < 4 ? 'eager' : 'lazy'}
              style={{
                maxWidth: '900px',
                width: '100%',
                height: 'auto',
                display: 'block',
                marginBottom: '4px',
              }}
            />
          ))}
        </div>
      ) : (
        // Paged Single/Manga View
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            padding: '12px',
            overflow: 'hidden',
          }}
        >
          <img
            src={currentImageUrl}
            alt={`Page ${currentPage + 1}`}
            style={{
              maxHeight: '100%',
              maxWidth: '100%',
              objectFit: 'contain',
              boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
              borderRadius: '4px',
            }}
          />

          {/* Navigation Overlay Buttons */}
          <button
            onClick={readerComicMode === 'rtl' ? handleNext : handlePrev}
            disabled={currentPage === 0}
            style={{
              position: 'absolute',
              left: '16px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              background: 'rgba(0,0,0,0.4)',
              color: '#fff',
              border: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: currentPage === 0 ? 'not-allowed' : 'pointer',
              opacity: currentPage === 0 ? 0.3 : 0.8,
            }}
            title={readerComicMode === 'rtl' ? 'Next Page' : 'Previous Page'}
          >
            <ChevronLeft size={24} />
          </button>

          <button
            onClick={readerComicMode === 'rtl' ? handlePrev : handleNext}
            disabled={currentPage === manifest.total_pages - 1}
            style={{
              position: 'absolute',
              right: '16px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              background: 'rgba(0,0,0,0.4)',
              color: '#fff',
              border: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: currentPage === manifest.total_pages - 1 ? 'not-allowed' : 'pointer',
              opacity: currentPage === manifest.total_pages - 1 ? 0.3 : 0.8,
            }}
            title={readerComicMode === 'rtl' ? 'Previous Page' : 'Next Page'}
          >
            <ChevronRight size={24} />
          </button>
        </div>
      )}

      {/* Scrubber Bottom Bar */}
      {readerComicMode !== 'webtoon' && (
        <div
          style={{
            padding: '10px 24px',
            background: 'rgba(15, 23, 42, 0.9)',
            backdropFilter: 'blur(8px)',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
          }}
        >
          <span style={{ fontSize: '12px', color: '#94a3b8', minWidth: '40px' }}>
            {currentPage + 1}
          </span>
          <input
            type="range"
            min={0}
            max={manifest.total_pages - 1}
            value={currentPage}
            onChange={(e) => setCurrentPage(parseInt(e.target.value, 10))}
            style={{
              flex: 1,
              accentColor: '#6366f1',
              cursor: 'pointer',
            }}
          />
          <span style={{ fontSize: '12px', color: '#94a3b8', minWidth: '40px', textAlign: 'right' }}>
            {manifest.total_pages}
          </span>
        </div>
      )}
    </div>
  );
};
