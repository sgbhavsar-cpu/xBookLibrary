import React, { useEffect, useState } from 'react';
import {
  Bookmark,
  BookOpen,
  Check,
  CheckCircle,
  Download,
  Layers,
  RefreshCw,
  Repeat,
  Send,
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
    activeLibraryId,
    loadBooks,
    loadSeriesList,
    setSendToDeviceOpen,
  } = useStore();

  const [isEnriching, setIsEnriching] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [enrichSuccess, setEnrichSuccess] = useState<string | null>(null);
  const [convertMessage, setConvertMessage] = useState<string | null>(null);

  // Series & Custom Columns local state
  const [seriesName, setSeriesName] = useState('');
  const [seriesIndex, setSeriesIndex] = useState(1.0);
  const [isSavingSeries, setIsSavingSeries] = useState(false);
  const [seriesSuccess, setSeriesSuccess] = useState(false);

  const [customVals, setCustomVals] = useState<Record<string, any>>({});
  const [isSavingCustom, setIsSavingCustom] = useState(false);
  const [customSuccess, setCustomSuccess] = useState(false);

  useEffect(() => {
    if (!selectedBook || !activeLibraryId) return;
    setSeriesName(selectedBook.series || '');
    setSeriesIndex(selectedBook.series_index || 1.0);
    setEnrichSuccess(null);
    setConvertMessage(null);
    setSeriesSuccess(false);
    setCustomSuccess(false);

    api.getBookCustomValues(selectedBook.id, activeLibraryId)
      .then((res) => setCustomVals(res.values || {}))
      .catch((err) => console.error('Failed to load custom values:', err));
  }, [selectedBook?.id, activeLibraryId]);

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

  const handleSaveSeries = async () => {
    if (!selectedBook || !activeLibraryId) return;
    setIsSavingSeries(true);
    try {
      await api.updateBookSeries(
        selectedBook.id,
        { name: seriesName.trim() || undefined, series_index: Number(seriesIndex) || 1.0 },
        activeLibraryId
      );
      setSeriesSuccess(true);
      setTimeout(() => setSeriesSuccess(false), 2000);
      await loadSeriesList();
      await loadBooks();
      await refreshSelectedBook();
    } catch (err) {
      console.error('Failed to update series:', err);
    } finally {
      setIsSavingSeries(false);
    }
  };

  const handleSaveCustom = async () => {
    if (!selectedBook || !activeLibraryId) return;
    setIsSavingCustom(true);
    try {
      await api.updateBookCustomValues(selectedBook.id, customVals, activeLibraryId);
      setCustomSuccess(true);
      setTimeout(() => setCustomSuccess(false), 2000);
      await loadBooks();
      await refreshSelectedBook();
    } catch (err) {
      console.error('Failed to update custom values:', err);
    } finally {
      setIsSavingCustom(false);
    }
  };

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

  const handleConvert = async (targetFormat: string) => {
    if (!selectedBook) return;
    setIsConverting(true);
    setConvertMessage(`Converting to ${targetFormat}...`);
    try {
      const job = await api.startConversion({
        book_id: selectedBook.id,
        target_format: targetFormat,
      });
      const poll = setInterval(async () => {
        try {
          const status = await api.getConversionJob(job.id);
          if (status.status === 'completed') {
            clearInterval(poll);
            setIsConverting(false);
            setConvertMessage(`Converted to ${targetFormat}!`);
            await refreshSelectedBook();
          } else if (status.status === 'failed') {
            clearInterval(poll);
            setIsConverting(false);
            setConvertMessage(status.error_message || 'Conversion failed');
          }
        } catch {
          clearInterval(poll);
          setIsConverting(false);
        }
      }, 1200);
    } catch (err: any) {
      setIsConverting(false);
      setConvertMessage(err.message || 'Conversion failed');
    }
  };

  const primaryFormat = selectedBook.formats.find(
    (f) => ['EPUB', 'PDF', 'CBZ', 'CBR'].includes(f.format.toUpperCase())
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

          {/* Send to Device Action */}
          <button
            className="btn btn-secondary"
            onClick={() => setSendToDeviceOpen(true)}
            style={{ width: '100%' }}
            title="Send to Kindle or export to USB drive"
          >
            <Send size={14} color="var(--accent-primary)" />
            <span>Send to Device</span>
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

      {/* Series & Universe Management */}
      <div
        style={{
          padding: '10px 12px',
          borderRadius: 'var(--radius-sm)',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Bookmark size={12} /> Series & Reading Order
          </span>
          {seriesSuccess && (
            <span style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '2px' }}>
              <Check size={11} /> Saved
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          <input
            type="text"
            className="input-text"
            placeholder="Series Name (e.g. Foundation)"
            value={seriesName}
            onChange={(e) => setSeriesName(e.target.value)}
            style={{ flex: 2, fontSize: '12px', padding: '4px 8px' }}
          />
          <input
            type="number"
            step="0.1"
            className="input-text"
            placeholder="Index"
            value={seriesIndex}
            onChange={(e) => setSeriesIndex(parseFloat(e.target.value) || 1.0)}
            style={{ width: '65px', fontSize: '12px', padding: '4px 8px', textAlign: 'center' }}
            title="Series Volume Index (e.g. 1.0, 2.5)"
          />
        </div>

        <button
          className="btn btn-secondary"
          onClick={handleSaveSeries}
          disabled={isSavingSeries}
          style={{ width: '100%', fontSize: '11px', padding: '4px' }}
        >
          {isSavingSeries ? 'Saving...' : 'Update Series Info'}
        </button>
      </div>

      {/* Custom Metadata Columns */}
      <div
        style={{
          padding: '10px 12px',
          borderRadius: 'var(--radius-sm)',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Layers size={12} /> Custom Calibre Columns
          </span>
          {customSuccess && (
            <span style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '2px' }}>
              <Check size={11} /> Saved
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          {/* Read Status */}
          <div>
            <label style={{ display: 'block', fontSize: '10.5px', color: 'var(--text-muted)', marginBottom: '2px' }}>
              #read_status
            </label>
            <select
              value={customVals['read_status'] || ''}
              onChange={(e) => setCustomVals({ ...customVals, read_status: e.target.value })}
              style={{
                width: '100%',
                padding: '4px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                fontSize: '11.5px',
              }}
            >
              <option value="">(None)</option>
              <option value="Unread">Unread</option>
              <option value="Reading">Reading</option>
              <option value="Completed">Completed</option>
              <option value="Abandoned">Abandoned</option>
            </select>
          </div>

          {/* Rating */}
          <div>
            <label style={{ display: 'block', fontSize: '10.5px', color: 'var(--text-muted)', marginBottom: '2px' }}>
              #rating
            </label>
            <select
              value={customVals['rating'] || ''}
              onChange={(e) => setCustomVals({ ...customVals, rating: e.target.value ? Number(e.target.value) : null })}
              style={{
                width: '100%',
                padding: '4px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                fontSize: '11.5px',
              }}
            >
              <option value="">(None)</option>
              <option value="5">⭐⭐⭐⭐⭐ (5)</option>
              <option value="4">⭐⭐⭐⭐ (4)</option>
              <option value="3">⭐⭐⭐ (3)</option>
              <option value="2">⭐⭐ (2)</option>
              <option value="1">⭐ (1)</option>
            </select>
          </div>

          {/* Pages */}
          <div>
            <label style={{ display: 'block', fontSize: '10.5px', color: 'var(--text-muted)', marginBottom: '2px' }}>
              #pages
            </label>
            <input
              type="number"
              className="input-text"
              placeholder="Page count"
              value={customVals['pages'] || ''}
              onChange={(e) => setCustomVals({ ...customVals, pages: e.target.value ? parseInt(e.target.value, 10) : null })}
              style={{ width: '100%', fontSize: '11.5px', padding: '4px 6px' }}
            />
          </div>

          {/* Difficulty */}
          <div>
            <label style={{ display: 'block', fontSize: '10.5px', color: 'var(--text-muted)', marginBottom: '2px' }}>
              #difficulty
            </label>
            <select
              value={customVals['difficulty'] || ''}
              onChange={(e) => setCustomVals({ ...customVals, difficulty: e.target.value })}
              style={{
                width: '100%',
                padding: '4px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                fontSize: '11.5px',
              }}
            >
              <option value="">(None)</option>
              <option value="Introductory">Introductory</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>
        </div>

        <button
          className="btn btn-secondary"
          onClick={handleSaveCustom}
          disabled={isSavingCustom}
          style={{ width: '100%', fontSize: '11px', padding: '4px' }}
        >
          {isSavingCustom ? 'Saving...' : 'Save Custom Columns'}
        </button>
      </div>

      {/* Formats Section */}
      <div>
        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
          Available Formats
        </div>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {selectedBook.formats.map((fmt) => {
            const canRead = ['EPUB', 'PDF', 'CBZ', 'CBR'].includes(fmt.format.toUpperCase());
            return (
              <div key={fmt.format} style={{ display: 'flex', gap: '2px', alignItems: 'center' }}>
                {canRead && (
                  <button
                    className="btn btn-secondary"
                    onClick={() => openReader(selectedBook.id, fmt.format)}
                    style={{ fontSize: '11.5px', padding: '4px 8px', color: 'var(--accent-primary)' }}
                    title={`Read ${fmt.format}`}
                  >
                    <BookOpen size={12} />
                    <span>Read {fmt.format}</span>
                  </button>
                )}
                <a
                  href={api.getBookDownloadUrl(selectedBook.id, fmt.format)}
                  download
                  className="btn btn-secondary"
                  style={{ fontSize: '11.5px', padding: '4px 8px' }}
                  title="Download File"
                >
                  <Download size={12} />
                  <span>({Math.round(fmt.uncompressed_size / 1024)} KB)</span>
                </a>
              </div>
            );
          })}
        </div>

        {/* Format Conversion Controls */}
        <div style={{ marginTop: '8px', display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
          {!selectedBook.formats.some((f) => f.format.toUpperCase() === 'EPUB') && (
            <button
              className="btn btn-secondary"
              onClick={() => handleConvert('EPUB')}
              disabled={isConverting}
              style={{ fontSize: '11px', padding: '3px 8px' }}
              title="Convert to reflowable EPUB"
            >
              <Repeat size={11} className={isConverting ? 'animate-spin' : ''} />
              <span>Convert to EPUB</span>
            </button>
          )}
          {!selectedBook.formats.some((f) => f.format.toUpperCase() === 'PDF') && (
            <button
              className="btn btn-secondary"
              onClick={() => handleConvert('PDF')}
              disabled={isConverting}
              style={{ fontSize: '11px', padding: '3px 8px' }}
              title="Convert to readable PDF"
            >
              <Repeat size={11} className={isConverting ? 'animate-spin' : ''} />
              <span>Convert to PDF</span>
            </button>
          )}
          {convertMessage && (
            <div style={{ fontSize: '11px', color: 'var(--accent-primary)', width: '100%', marginTop: '2px' }}>
              {convertMessage}
            </div>
          )}
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
