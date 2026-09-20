import React, { useState } from 'react';
import {
  BookOpen,
  CheckCircle,
  Download,
  RefreshCw,
  Sparkles,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import { SummaryTabs } from './SummaryTabs';

export const DetailInspector: React.FC = () => {
  const {
    selectedBook,
    selectBook,
    openReader,
    refreshSelectedBook,
  } = useStore();

  const [isEnriching, setIsEnriching] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [enrichSuccess, setEnrichSuccess] = useState<string | null>(null);

  if (!selectedBook) {
    return (
      <aside
        style={{
          width: 'var(--inspector-width)',
          height: 'calc(100vh - var(--header-height) - var(--status-bar-height))',
          background: 'var(--bg-surface)',
          borderLeft: '1px solid var(--border-default)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          color: 'var(--text-muted)',
          textAlign: 'center',
          gap: '8px',
        }}
      >
        <BookOpen size={40} strokeWidth={1.5} />
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          No Book Selected
        </h3>
        <p style={{ fontSize: '12px' }}>
          Select a book from the catalog grid or table to inspect metadata, read summaries, and launch the reader.
        </p>
      </aside>
    );
  }

  const handleEnrich = async () => {
    setIsEnriching(true);
    setEnrichSuccess(null);
    try {
      const res = await api.enrichBook(selectedBook.id);
      setEnrichSuccess(res.message);
      await refreshSelectedBook();
    } catch (err) {
      console.error('Enrichment failed:', err);
    } finally {
      setIsEnriching(false);
    }
  };

  const handleIndex = async () => {
    setIsIndexing(true);
    try {
      await api.indexBook(selectedBook.id);
      await refreshSelectedBook();
    } catch (err) {
      console.error('Vector indexing failed:', err);
    } finally {
      setIsIndexing(false);
    }
  };

  const primaryFormat = selectedBook.formats.find(
    (f) => f.format === 'EPUB' || f.format === 'PDF'
  ) || selectedBook.formats[0];

  return (
    <aside
      style={{
        width: 'var(--inspector-width)',
        height: 'calc(100vh - var(--header-height) - var(--status-bar-height))',
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border-default)',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        padding: '1.25rem',
        gap: '1.25rem',
      }}
    >
      {/* Header with Close */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, lineHeight: 1.3, color: 'var(--text-primary)' }}>
            {selectedBook.title}
          </h2>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '3px' }}>
            by {selectedBook.authors.join(', ')}
          </div>
        </div>
        <button
          className="btn-icon"
          onClick={() => selectBook(null)}
          title="Close Inspector"
          style={{ width: '28px', height: '28px' }}
        >
          <X size={14} />
        </button>
      </div>

      {/* Cover & Quick Actions */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        <div
          style={{
            width: '120px',
            aspectRatio: '2 / 3',
            borderRadius: 'var(--radius-sm)',
            overflow: 'hidden',
            background: 'var(--bg-surface-elevated)',
            boxShadow: 'var(--shadow-md)',
            flexShrink: 0,
          }}
        >
          <img
            src={api.getBookCoverUrl(selectedBook.id)}
            alt={selectedBook.title}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          {/* Read Now Button */}
          {primaryFormat && (
            <button
              className="btn btn-primary"
              onClick={() => openReader(selectedBook.id, primaryFormat.format)}
              style={{ width: '100%', padding: '8px 12px' }}
            >
              <BookOpen size={15} />
              <span>Read {primaryFormat.format}</span>
            </button>
          )}

          {/* RAG Indexing Action */}
          <button
            className="btn btn-secondary"
            onClick={handleIndex}
            disabled={isIndexing || selectedBook.is_indexed}
            style={{ width: '100%' }}
          >
            {selectedBook.is_indexed ? (
              <>
                <CheckCircle size={14} color="#10b981" />
                <span>RAG Vector Indexed</span>
              </>
            ) : (
              <>
                <Sparkles size={14} color="var(--accent-primary)" />
                <span>{isIndexing ? 'Indexing...' : 'Index for RAG'}</span>
              </>
            )}
          </button>

          {/* Agentic Metadata Enrichment Action */}
          <button
            className="btn btn-secondary"
            onClick={handleEnrich}
            disabled={isEnriching}
            style={{ width: '100%' }}
          >
            <RefreshCw size={14} className={isEnriching ? 'animate-spin' : ''} />
            <span>{isEnriching ? 'Searching Providers...' : 'Enrich Metadata'}</span>
          </button>

          {enrichSuccess && (
            <div style={{ fontSize: '11.5px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle size={12} />
              <span>{enrichSuccess}</span>
            </div>
          )}
        </div>
      </div>

      {/* Formats Section */}
      <div>
        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
          Available Formats
        </div>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {selectedBook.formats.map((fmt) => (
            <a
              key={fmt.format}
              href={api.getBookDownloadUrl(selectedBook.id, fmt.format)}
              download
              className="btn btn-secondary"
              style={{ fontSize: '11.5px', padding: '4px 8px' }}
            >
              <Download size={12} />
              <span>{fmt.format} ({Math.round(fmt.uncompressed_size / 1024)} KB)</span>
            </a>
          ))}
        </div>
      </div>

      {/* AI Classification & Categorization */}
      {selectedBook.classification && (
        <div
          style={{
            padding: '10px 12px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
              AI Taxonomy Classification
            </span>
            <span className="badge badge-emerald">
              {Math.round(selectedBook.classification.confidence * 100)}% Match
            </span>
          </div>

          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {selectedBook.classification.bisac_heading}
          </div>

          <div style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
            BISAC: <strong>{selectedBook.classification.bisac_code}</strong> &bull; DDC: <strong>{selectedBook.classification.ddc_code}</strong>
          </div>

          {selectedBook.classification.reasoning && (
            <div style={{ fontSize: '11.5px', fontStyle: 'italic', color: 'var(--text-secondary)' }}>
              "{selectedBook.classification.reasoning}"
            </div>
          )}
        </div>
      )}

      {/* Multi-Resolution AI Summaries (Feature 006) */}
      <div>
        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
          AI Knowledge Summaries
        </div>
        <SummaryTabs />
      </div>

      {/* Book Description / Comments */}
      {selectedBook.comments && (
        <div>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
            Description
          </div>
          <div
            style={{ fontSize: '12.5px', lineHeight: 1.6, color: 'var(--text-secondary)' }}
            dangerouslySetInnerHTML={{ __html: selectedBook.comments }}
          />
        </div>
      )}
    </aside>
  );
};
