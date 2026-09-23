import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Sparkles, RefreshCw, Quote, Compass, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';

export const SummaryTabs: React.FC = () => {
  const { selectedBook, selectedBookSummary, refreshSelectedBook } = useStore();
  const [activeTab, setActiveTab] = useState<'exec' | 'chapters' | 'takeaways'>('exec');
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [expandedChapter, setExpandedChapter] = useState<number | null>(0);

  if (!selectedBook) return null;

  const handleGenerate = async () => {
    setIsGenerating(true);
    setErrorMsg(null);
    try {
      await api.generateSummary(selectedBook.id, 'executive');
      await refreshSelectedBook();
    } catch (err: any) {
      console.error('Failed to generate summary:', err);
      setErrorMsg(err?.message || 'Failed to generate summary with local Ollama.');
    } finally {
      setIsGenerating(false);
    }
  };

  if (!selectedBookSummary) {
    return (
      <div
        style={{
          padding: '1.25rem',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: '8px',
          margin: '1rem 0',
        }}
      >
        <Sparkles size={24} color="var(--accent-primary)" />
        <h4 style={{ fontSize: '13px', fontWeight: 600 }}>No AI Summaries Generated Yet</h4>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Synthesize executive snapshot, conceptual frameworks, and chapter breakdowns via Ollama.
        </p>

        {errorMsg && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              color: '#ef4444',
              fontSize: '11.5px',
              margin: '4px 0',
              textAlign: 'left',
            }}
          >
            <AlertCircle size={14} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={isGenerating}
          style={{ marginTop: '6px' }}
        >
          {isGenerating ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : (
            <Sparkles size={14} />
          )}
          <span>{isGenerating ? 'Synthesizing with Ollama...' : 'Generate AI Summary'}</span>
        </button>
      </div>
    );
  }

  // Safe data extraction across both new multi-resolution and legacy schemas
  const snapshot = selectedBookSummary.executive_snapshot;
  const conceptual = selectedBookSummary.conceptual_index;
  const chapters = selectedBookSummary.chapters || selectedBookSummary.chapter_summaries || [];
  const takeaways = conceptual?.key_takeaways || selectedBookSummary.key_takeaways || [];
  const frameworks = conceptual?.frameworks || [];
  const actionItems = conceptual?.action_items || [];
  const quotableMoments = conceptual?.quotable_moments || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Header bar with tabs and regenerate button */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-default)',
        }}
      >
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setActiveTab('exec')}
            style={{
              padding: '6px 10px',
              fontSize: '12px',
              fontWeight: 600,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'exec' ? '2px solid var(--accent-primary)' : '2px solid transparent',
              color: activeTab === 'exec' ? 'var(--accent-primary)' : 'var(--text-muted)',
              cursor: 'pointer',
            }}
          >
            Executive
          </button>

          <button
            onClick={() => setActiveTab('chapters')}
            style={{
              padding: '6px 10px',
              fontSize: '12px',
              fontWeight: 600,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'chapters' ? '2px solid var(--accent-primary)' : '2px solid transparent',
              color: activeTab === 'chapters' ? 'var(--accent-primary)' : 'var(--text-muted)',
              cursor: 'pointer',
            }}
          >
            Chapters ({chapters.length})
          </button>

          <button
            onClick={() => setActiveTab('takeaways')}
            style={{
              padding: '6px 10px',
              fontSize: '12px',
              fontWeight: 600,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'takeaways' ? '2px solid var(--accent-primary)' : '2px solid transparent',
              color: activeTab === 'takeaways' ? 'var(--accent-primary)' : 'var(--text-muted)',
              cursor: 'pointer',
            }}
          >
            Key Insights
          </button>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          title="Regenerate Summary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '11px',
            cursor: isGenerating ? 'not-allowed' : 'pointer',
            padding: '4px 6px',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <RefreshCw size={12} className={isGenerating ? 'animate-spin' : ''} />
          <span>{isGenerating ? 'Regenerating...' : 'Regenerate'}</span>
        </button>
      </div>

      {errorMsg && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 10px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            color: '#ef4444',
            fontSize: '11.5px',
          }}
        >
          <AlertCircle size={14} style={{ flexShrink: 0 }} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Tab Content */}
      <div style={{ fontSize: '12.5px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
        {/* Executive Tab */}
        {activeTab === 'exec' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {snapshot ? (
              <>
                {snapshot.hook && (
                  <div
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(99, 102, 241, 0.08)',
                      borderLeft: '3px solid var(--accent-primary)',
                      fontStyle: 'italic',
                      fontSize: '12.5px',
                      color: 'var(--text-primary)',
                    }}
                  >
                    "{snapshot.hook}"
                  </div>
                )}

                {snapshot.core_thesis && (
                  <div>
                    <h5 style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Core Thesis
                    </h5>
                    <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{snapshot.core_thesis}</p>
                  </div>
                )}

                {snapshot.target_audience && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11.5px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Target Audience:</span>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {snapshot.target_audience}
                    </span>
                  </div>
                )}

                {snapshot.key_arguments && snapshot.key_arguments.length > 0 && (
                  <div>
                    <h5 style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
                      Key Arguments
                    </h5>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {snapshot.key_arguments.map((arg, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: '6px 10px',
                            borderRadius: 'var(--radius-sm)',
                            background: 'var(--bg-surface-elevated)',
                            border: '1px solid var(--border-subtle)',
                            fontSize: '12px',
                          }}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--accent-primary)', marginRight: '6px' }}>
                            {idx + 1}.
                          </span>
                          {arg}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p style={{ whiteSpace: 'pre-wrap' }}>{selectedBookSummary.executive_summary || 'No executive summary available.'}</p>
            )}
          </div>
        )}

        {/* Chapters Tab */}
        {activeTab === 'chapters' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {chapters.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No chapter breakdowns recorded for this book.</p>
            ) : (
              chapters.map((ch, idx) => {
                const isExpanded = expandedChapter === idx;
                const points = ch.key_takeaways || ch.key_points || [];
                const quotes = ch.important_quotes || [];

                return (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-surface-elevated)',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      onClick={() => setExpandedChapter(isExpanded ? null : idx)}
                      style={{
                        padding: '8px 10px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        fontWeight: 600,
                        fontSize: '12px',
                      }}
                    >
                      <span>{ch.chapter_title || `Chapter ${idx + 1}`}</span>
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </div>

                    {isExpanded && (
                      <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-card)' }}>
                        <p style={{ marginBottom: '6px' }}>{ch.summary}</p>

                        {points.length > 0 && (
                          <div style={{ marginTop: '8px' }}>
                            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                              Takeaways:
                            </div>
                            <ul style={{ paddingLeft: '16px', fontSize: '11.5px', color: 'var(--text-secondary)', margin: 0 }}>
                              {points.map((pt, i) => (
                                <li key={i}>{pt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {quotes.length > 0 && (
                          <div style={{ marginTop: '8px' }}>
                            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                              Notable Quotes:
                            </div>
                            {quotes.map((q, i) => (
                              <blockquote
                                key={i}
                                style={{
                                  margin: '4px 0',
                                  padding: '4px 8px',
                                  borderLeft: '2px solid var(--accent-primary)',
                                  fontSize: '11.5px',
                                  fontStyle: 'italic',
                                  color: 'var(--text-muted)',
                                }}
                              >
                                "{q}"
                              </blockquote>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Key Takeaways Tab */}
        {activeTab === 'takeaways' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {frameworks.length > 0 && (
              <div>
                <h5 style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  <Compass size={13} color="var(--accent-primary)" />
                  <span>Conceptual Frameworks</span>
                </h5>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {frameworks.map((f, i) => (
                    <span
                      key={i}
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        background: 'rgba(99, 102, 241, 0.12)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        color: 'var(--accent-primary)',
                        fontSize: '11.5px',
                        fontWeight: 500,
                      }}
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h5 style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Key Takeaways
              </h5>
              {takeaways.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No takeaways listed.</p>
              ) : (
                <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px', margin: 0 }}>
                  {takeaways.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>
              )}
            </div>

            {actionItems.length > 0 && (
              <div>
                <h5 style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  <CheckCircle2 size={13} color="#10b981" />
                  <span>Action Items</span>
                </h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {actionItems.map((item, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '6px 8px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '11.5px',
                      }}
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {quotableMoments.length > 0 && (
              <div>
                <h5 style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  <Quote size={13} color="var(--accent-primary)" />
                  <span>Quotable Moments</span>
                </h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {quotableMoments.map((q, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '6px 8px',
                        borderLeft: '2px solid var(--accent-primary)',
                        background: 'var(--bg-surface-elevated)',
                        fontSize: '11.5px',
                      }}
                    >
                      <div style={{ fontStyle: 'italic', color: 'var(--text-primary)' }}>"{q.quote}"</div>
                      {q.source && <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', marginTop: '2px' }}>— {q.source}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
