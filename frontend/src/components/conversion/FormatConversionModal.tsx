import React, { useState, useEffect } from 'react';
import {
  Repeat,
  X,
  CheckCircle2,
  AlertCircle,
  FileText,
  Loader2,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';
import type { Book } from '../../types';

const COMMON_FORMATS = ['EPUB', 'PDF', 'MOBI', 'AZW3', 'TXT', 'DOCX'];

const FORMAT_DESCRIPTIONS: Record<string, string> = {
  EPUB: 'Universal reflowable e-book format for phones, tablets & readers',
  PDF: 'Fixed-layout document with preserved typography & margins',
  MOBI: 'Legacy Amazon Kindle format for older e-readers',
  AZW3: 'Modern Amazon KF8 e-book format with rich CSS styling',
  TXT: 'Plain-text clean transcript stripped of formatting',
  DOCX: 'Microsoft Word document for manuscript editing',
};

export const FormatConversionModal: React.FC = () => {
  const {
    isConversionModalOpen,
    conversionTargetBookIds,
    closeConversionModal,
    books,
    loadBooks,
    refreshSelectedBook,
    setToastMessage,
  } = useStore();

  const targetBooks = books.filter((b) => conversionTargetBookIds.includes(b.id));
  const isBulk = targetBooks.length > 1;
  const singleBook: Book | undefined = targetBooks[0];

  // Form states
  const [sourceFormat, setSourceFormat] = useState<string>('');
  const [targetFormat, setTargetFormat] = useState<string>('EPUB');

  // Job states
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  // Initialize available formats on open
  useEffect(() => {
    if (!isConversionModalOpen) {
      setIsProcessing(false);
      setLogs([]);
      setErrorMessage(null);
      setIsSuccess(false);
      setProgressPercent(0);
      return;
    }

    if (singleBook && singleBook.formats && singleBook.formats.length > 0) {
      const avail = singleBook.formats.map((f) => f.format.toUpperCase());
      const initialSource = avail[0];
      setSourceFormat(initialSource);

      // Default target to something other than source
      if (initialSource === 'EPUB') {
        setTargetFormat('PDF');
      } else {
        setTargetFormat('EPUB');
      }
    } else {
      setSourceFormat('EPUB');
      setTargetFormat('PDF');
    }
  }, [isConversionModalOpen, conversionTargetBookIds]);

  if (!isConversionModalOpen || targetBooks.length === 0) return null;

  const handleStartConversion = async () => {
    setIsProcessing(true);
    setErrorMessage(null);
    setIsSuccess(false);
    setLogs([`Queuing format conversion to ${targetFormat}...`]);
    setProgressPercent(10);

    try {
      for (let i = 0; i < targetBooks.length; i++) {
        const b = targetBooks[i];
        setLogs((prev) => [...prev, `[${i + 1}/${targetBooks.length}] Converting "${b.title}"...`]);

        // Submit job to backend
        const job = await api.startConversion({
          book_id: b.id,
          target_format: targetFormat,
          source_format: isBulk ? undefined : sourceFormat || undefined,
        });

        // Poll job until complete or failed
        let pollCount = 0;
        let jobFinished = false;

        while (!jobFinished && pollCount < 60) {
          await new Promise((r) => setTimeout(r, 1200));
          pollCount++;

          const latest = await api.getConversionJob(job.id);
          setProgressPercent(Math.max(20, latest.percent_complete));

          if (latest.logs && latest.logs.length > 0) {
            setLogs((prev) => {
              const combined = [...prev];
              for (const l of latest.logs) {
                if (!combined.includes(l)) combined.push(l);
              }
              return combined;
            });
          }

          if (latest.status === 'completed') {
            jobFinished = true;
            setProgressPercent(100);
            setLogs((prev) => [
              ...prev,
              `✓ Successfully converted "${b.title}" to ${targetFormat}!`,
            ]);
          } else if (latest.status === 'failed') {
            jobFinished = true;
            throw new Error(latest.error_message || 'Conversion failed');
          }
        }
      }

      setIsSuccess(true);
      setIsProcessing(false);
      await loadBooks();
      await refreshSelectedBook();
      setToastMessage(
        isBulk
          ? `Successfully converted ${targetBooks.length} books to ${targetFormat}`
          : `Successfully converted "${singleBook?.title}" to ${targetFormat}`
      );
    } catch (err: any) {
      setIsProcessing(false);
      setErrorMessage(err.message || 'Conversion failed');
      setLogs((prev) => [...prev, `❌ Error: ${err.message || 'Conversion failed'}`]);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        padding: '1.5rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !isProcessing) closeConversionModal();
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '720px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'var(--bg-modal, #18181b)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg, 16px)',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden',
          animation: 'fadeIn 0.2s ease-out',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-md, 8px)',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Repeat size={18} />
            </div>
            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: '16px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                }}
              >
                {isBulk ? `Convert Books (${targetBooks.length} Selected)` : 'Convert Book'}
              </h2>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Calibre-compatible format conversion engine
              </span>
            </div>
          </div>

          <button
            className="btn-icon"
            onClick={closeConversionModal}
            disabled={isProcessing}
            style={{ color: 'var(--text-muted)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div
          style={{
            padding: '1.5rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
          }}
        >
          {/* Target Preview */}
          {!isBulk && singleBook && (
            <div
              style={{
                display: 'flex',
                gap: '1.25rem',
                padding: '1rem',
                backgroundColor: 'var(--bg-surface-elevated)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {singleBook.has_cover ? (
                <img
                  src={api.getBookCoverUrl(singleBook.id)}
                  alt={singleBook.title}
                  style={{
                    width: '64px',
                    height: '96px',
                    objectFit: 'cover',
                    borderRadius: '4px',
                    boxShadow: 'var(--shadow-sm)',
                    flexShrink: 0,
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '64px',
                    height: '96px',
                    backgroundColor: 'var(--bg-card)',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--text-muted)',
                    flexShrink: 0,
                  }}
                >
                  <FileText size={24} />
                </div>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '4px' }}>
                <div style={{ fontWeight: 600, fontSize: '15px', color: 'var(--text-primary)' }}>
                  {singleBook.title}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  {singleBook.authors.join(', ') || 'Unknown Author'}
                </div>
                <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                  {singleBook.formats.map((f) => (
                    <span
                      key={f.format}
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 600,
                        backgroundColor: 'var(--bg-card)',
                        border: '1px solid var(--border-default)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {f.format.toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {isBulk && (
            <div
              style={{
                padding: '1rem',
                backgroundColor: 'var(--bg-surface-elevated)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                fontSize: '13px',
                color: 'var(--text-secondary)',
              }}
            >
              Batch converting <strong>{targetBooks.length} books</strong> into{' '}
              <strong style={{ color: 'var(--accent-primary)' }}>{targetFormat}</strong> format.
            </div>
          )}

          {/* Format Selection Matrix */}
          <div style={{ display: 'grid', gridTemplateColumns: isBulk ? '1fr' : '1fr auto 1fr', gap: '1rem', alignItems: 'center' }}>
            {!isBulk && singleBook && (
              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: '8px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  Input Format
                </label>
                <select
                  value={sourceFormat}
                  onChange={(e) => setSourceFormat(e.target.value)}
                  disabled={isProcessing}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                >
                  {singleBook.formats.map((f) => (
                    <option key={f.format} value={f.format.toUpperCase()}>
                      {f.format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {!isBulk && (
              <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '20px', color: 'var(--text-muted)' }}>
                <ArrowRight size={20} />
              </div>
            )}

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                Output Target Format
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                {COMMON_FORMATS.map((fmt) => {
                  const isCurrentSource = !isBulk && sourceFormat === fmt;
                  const isSelected = targetFormat === fmt;
                  return (
                    <button
                      key={fmt}
                      type="button"
                      disabled={isProcessing || isCurrentSource}
                      onClick={() => setTargetFormat(fmt)}
                      style={{
                        padding: '10px 8px',
                        borderRadius: 'var(--radius-sm)',
                        border: isSelected
                          ? '1px solid var(--accent-primary)'
                          : '1px solid var(--border-subtle)',
                        backgroundColor: isSelected
                          ? 'rgba(99, 102, 241, 0.15)'
                          : 'var(--bg-surface-elevated)',
                        color: isSelected
                          ? 'var(--accent-primary)'
                          : isCurrentSource
                          ? 'var(--text-muted)'
                          : 'var(--text-secondary)',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: isCurrentSource ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '2px',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <span>{fmt}</span>
                      {isCurrentSource && (
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 400 }}>
                          (Source)
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Format Description Help Text */}
          {FORMAT_DESCRIPTIONS[targetFormat] && (
            <div
              style={{
                fontSize: '12px',
                color: 'var(--text-muted)',
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                borderLeft: '3px solid var(--accent-primary)',
              }}
            >
              {FORMAT_DESCRIPTIONS[targetFormat]}
            </div>
          )}

          {/* Progress & Console Log */}
          {(isProcessing || logs.length > 0) && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Conversion Progress
                </span>
                <span style={{ fontSize: '12px', color: 'var(--accent-primary)', fontWeight: 600 }}>
                  {progressPercent}%
                </span>
              </div>

              {/* Progress bar */}
              <div
                style={{
                  width: '100%',
                  height: '6px',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  borderRadius: '3px',
                  overflow: 'hidden',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    width: `${progressPercent}%`,
                    height: '100%',
                    backgroundColor: isSuccess
                      ? '#10b981'
                      : errorMessage
                      ? '#ef4444'
                      : 'var(--accent-primary)',
                    transition: 'width 0.3s ease',
                  }}
                />
              </div>

              {/* Terminal Logs */}
              <div
                style={{
                  marginTop: '6px',
                  backgroundColor: 'var(--bg-primary, #09090b)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '10px 12px',
                  maxHeight: '130px',
                  overflowY: 'auto',
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  color: '#d4d4d8',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                {logs.map((line, idx) => (
                  <div key={idx} style={{ wordBreak: 'break-all' }}>
                    {line}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#ef4444',
                fontSize: '13px',
              }}
            >
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Success Banner */}
          {isSuccess && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#10b981',
                fontSize: '13px',
              }}
            >
              <CheckCircle2 size={16} />
              <span>
                Format conversion complete! The new <strong>{targetFormat}</strong> format is attached to the book catalog.
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '10px',
            backgroundColor: 'var(--bg-surface-elevated)',
          }}
        >
          <button
            className="btn btn-secondary"
            onClick={closeConversionModal}
            disabled={isProcessing}
          >
            {isSuccess ? 'Close' : 'Cancel'}
          </button>

          {!isSuccess && (
            <button
              className="btn btn-primary"
              onClick={handleStartConversion}
              disabled={isProcessing || (!isBulk && sourceFormat === targetFormat)}
              style={{ minWidth: '140px' }}
            >
              {isProcessing ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  <span>Converting...</span>
                </>
              ) : (
                <>
                  <Sparkles size={15} />
                  <span>Convert to {targetFormat}</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
