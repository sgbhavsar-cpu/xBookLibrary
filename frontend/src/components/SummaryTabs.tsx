import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';

export const SummaryTabs: React.FC = () => {
  const { selectedBook, selectedBookSummary, refreshSelectedBook } = useStore();
  const [activeTab, setActiveTab] = useState<'exec' | 'chapters' | 'takeaways'>('exec');
  const [isGenerating, setIsGenerating] = useState(false);
  const [expandedChapter, setExpandedChapter] = useState<number | null>(0);

  if (!selectedBook) return null;

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await api.generateSummary(selectedBook.id, 'executive');
      await refreshSelectedBook();
    } catch (err) {
      console.error('Failed to generate summary:', err);
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
          Create executive briefs, key takeaways, and chapter-by-chapter breakdowns.
        </p>
        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={isGenerating}
          style={{ marginTop: '6px' }}
        >
          <Sparkles size={14} />
          <span>{isGenerating ? 'Generating Multi-Resolution Summary...' : 'Generate AI Summary'}</span>
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Tabs Header */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-default)',
          gap: '4px',
        }}
      >
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
          Chapters ({selectedBookSummary.chapter_summaries.length})
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
          Key Points
        </button>
      </div>

      {/* Tab Content */}
      <div style={{ fontSize: '12.5px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
        {activeTab === 'exec' && (
          <div>
            <p style={{ whiteSpace: 'pre-wrap' }}>{selectedBookSummary.executive_summary}</p>
          </div>
        )}

        {activeTab === 'chapters' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {selectedBookSummary.chapter_summaries.map((ch, idx) => {
              const isExpanded = expandedChapter === idx;
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
                      {ch.key_points && ch.key_points.length > 0 && (
                        <ul style={{ paddingLeft: '16px', fontSize: '11.5px', color: 'var(--text-muted)' }}>
                          {ch.key_points.map((pt, i) => (
                            <li key={i}>{pt}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {activeTab === 'takeaways' && (
          <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {selectedBookSummary.key_takeaways.map((pt, i) => (
              <li key={i}>{pt}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
