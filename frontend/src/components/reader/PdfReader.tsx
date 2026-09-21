import React, { useEffect, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';

interface PdfReaderProps {
  bookId: number;
  targetLocation?: string | null;
}

export const PdfReader: React.FC<PdfReaderProps> = ({ bookId, targetLocation }) => {
  const { readerProgress, saveProgress } = useStore();
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [inputPage, setInputPage] = useState<string>('1');

  // Resume from saved location if available
  useEffect(() => {
    const loc = targetLocation || readerProgress?.location;
    if (loc) {
      const pageNum = parseInt(loc.replace(/\D/g, ''), 10);
      if (!isNaN(pageNum) && pageNum > 0) {
        setCurrentPage(pageNum);
        setInputPage(pageNum.toString());
      }
    }
  }, [targetLocation, readerProgress]);

  const handlePageChange = (newPage: number) => {
    if (newPage < 1) return;
    setCurrentPage(newPage);
    setInputPage(newPage.toString());
    // Estimate progress: default rough calculation if total pages unknown
    saveProgress(`page-${newPage}`, Math.min(100, Math.round((newPage / 100) * 100)), 10);
  };

  const handlePageInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const p = parseInt(inputPage, 10);
    if (!isNaN(p) && p > 0) {
      handlePageChange(p);
    }
  };

  const handleZoomIn = () => setZoomLevel((z) => Math.min(250, z + 25));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(50, z - 25));

  const pdfUrl = `${api.getBookDownloadUrl(bookId, 'PDF')}#page=${currentPage}&zoom=${zoomLevel}&toolbar=1&navpanes=1`;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: '#0f172a',
        position: 'relative',
      }}
    >
      {/* PDF Quick Controls Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 16px',
          background: 'rgba(15, 23, 42, 0.95)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          zIndex: 10,
        }}
      >
        {/* Page Nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            style={{
              background: 'none',
              border: 'none',
              color: currentPage <= 1 ? '#475569' : '#94a3b8',
              cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
              padding: '4px',
            }}
            title="Previous Page"
          >
            <ChevronLeft size={18} />
          </button>

          <form onSubmit={handlePageInputSubmit} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Page</span>
            <input
              type="text"
              value={inputPage}
              onChange={(e) => setInputPage(e.target.value)}
              onBlur={handlePageInputSubmit}
              style={{
                width: '44px',
                textAlign: 'center',
                padding: '2px 4px',
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '4px',
                color: '#fff',
                fontSize: '12px',
                outline: 'none',
              }}
            />
          </form>

          <button
            onClick={() => handlePageChange(currentPage + 1)}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px',
            }}
            title="Next Page"
          >
            <ChevronRight size={18} />
          </button>
        </div>

        {/* Zoom Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleZoomOut}
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <span style={{ fontSize: '12px', color: '#cbd5e1', minWidth: '40px', textAlign: 'center' }}>
            {zoomLevel}%
          </span>
          <button
            onClick={handleZoomIn}
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
        </div>
      </div>

      {/* PDF Frame */}
      <iframe
        key={`${currentPage}-${zoomLevel}`}
        src={pdfUrl}
        title="PDF Book Reader"
        style={{
          flex: 1,
          width: '100%',
          height: '100%',
          border: 'none',
          background: '#1e293b',
        }}
      />
    </div>
  );
};
