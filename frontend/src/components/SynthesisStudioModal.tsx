import React, { useEffect, useState } from 'react';
import {
  Download,
  Layers,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import type { SynthesisDocument, SynthesisJobStatus } from '../types';

export const SynthesisStudioModal: React.FC = () => {
  const {
    books,
    activeLibraryId,
    isSynthesisModalOpen,
    setSynthesisModalOpen,
  } = useStore();

  const [title, setTitle] = useState('');
  const [topicPrompt, setTopicPrompt] = useState('');
  const [templateType, setTemplateType] = useState('literature_review');
  const [selectedBookIds, setSelectedBookIds] = useState<number[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobStatus, setJobStatus] = useState<SynthesisJobStatus | null>(null);
  const [activeDoc, setActiveDoc] = useState<SynthesisDocument | null>(null);
  const [documents, setDocuments] = useState<SynthesisDocument[]>([]);

  useEffect(() => {
    if (!activeLibraryId || !isSynthesisModalOpen) return;
    api.getSynthesisDocuments(activeLibraryId)
      .then(setDocuments)
      .catch((err) => console.error('Failed to load synthesis documents:', err));
  }, [activeLibraryId, isSynthesisModalOpen]);

  if (!isSynthesisModalOpen) return null;

  const toggleBook = (id: number) => {
    setSelectedBookIds((prev) =>
      prev.includes(id) ? prev.filter((b) => b !== id) : [...prev, id]
    );
  };

  const handleGenerate = async () => {
    if (!title.trim() || !topicPrompt.trim()) return;
    setIsGenerating(true);
    setJobStatus(null);
    setActiveDoc(null);

    try {
      // Trigger synthesis asynchronously and poll job status
      const res = await api.generateSynthesis({
        title: title.trim(),
        topic_prompt: topicPrompt.trim(),
        template_type: templateType,
        book_ids: selectedBookIds.length > 0 ? selectedBookIds : undefined,
        library_id: activeLibraryId || undefined,
        wait: false,
      });

      if ('job_id' in res) {
        const pollTimer = setInterval(async () => {
          try {
            const status = await api.getSynthesisJob(res.job_id);
            setJobStatus(status);
            if (status.status === 'completed' && status.document_id) {
              clearInterval(pollTimer);
              setIsGenerating(false);
              const doc = await api.getSynthesisDocument(status.document_id);
              setActiveDoc(doc);
              setDocuments((prev) => [doc, ...prev]);
            } else if (status.status === 'failed') {
              clearInterval(pollTimer);
              setIsGenerating(false);
            }
          } catch {
            clearInterval(pollTimer);
            setIsGenerating(false);
          }
        }, 1200);
      } else {
        setIsGenerating(false);
        setActiveDoc(res as SynthesisDocument);
        setDocuments((prev) => [res as SynthesisDocument, ...prev]);
      }
    } catch (err) {
      console.error('Synthesis generation failed:', err);
      setIsGenerating(false);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await api.deleteSynthesisDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (activeDoc?.id === docId) setActiveDoc(null);
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'var(--bg-modal)',
        backdropFilter: 'blur(8px)',
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '1080px',
          height: '85vh',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            height: '60px',
            padding: '0 1.5rem',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={20} color="var(--accent-primary)" />
            <h2 style={{ fontSize: '16px', fontWeight: 700 }}>Multi-Book Document Synthesis Studio</h2>
          </div>
          <button className="btn-icon" onClick={() => setSynthesisModalOpen(false)}>
            <X size={16} />
          </button>
        </div>

        {/* Modal Body: Two Columns */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Left Form & Library Selector Column */}
          <div
            style={{
              width: '420px',
              borderRight: '1px solid var(--border-default)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              overflowY: 'auto',
            }}
          >
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Document Title
              </label>
              <input
                type="text"
                className="input-text"
                placeholder="e.g. Comparative Analysis of Quantum Hardware"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Research Topic & Instructions
              </label>
              <textarea
                className="input-text"
                rows={3}
                placeholder="Explain engineering tradeoffs, error correction strategies, and coherence time..."
                value={topicPrompt}
                onChange={(e) => setTopicPrompt(e.target.value)}
                style={{ resize: 'none' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Template Type
              </label>
              <select
                className="input-text"
                value={templateType}
                onChange={(e) => setTemplateType(e.target.value)}
              >
                <option value="literature_review">Literature Review (Comparative Depth)</option>
                <option value="topic_brief">Topic Brief (Comprehensive Multi-Section)</option>
                <option value="executive_summary">Executive Summary (High-Level Decision Brief)</option>
                <option value="custom_research">Custom Multi-Perspective Research</option>
              </select>
            </div>

            {/* Select Source Books */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Source Books ({selectedBookIds.length === 0 ? 'All Library Books' : `${selectedBookIds.length} Selected`})
              </label>
              <div
                style={{
                  maxHeight: '140px',
                  overflowY: 'auto',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '6px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  background: 'var(--bg-surface-elevated)',
                }}
              >
                {books.map((b) => {
                  const checked = selectedBookIds.includes(b.id);
                  return (
                    <label
                      key={b.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        padding: '3px 6px',
                        borderRadius: 'var(--radius-xs)',
                        background: checked ? 'var(--accent-surface)' : 'transparent',
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleBook(b.id)}
                      />
                      <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {b.title}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>

            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={isGenerating || !title.trim() || !topicPrompt.trim()}
              style={{ padding: '8px 12px', marginTop: '4px' }}
            >
              <Sparkles size={16} />
              <span>{isGenerating ? 'Synthesizing Brief...' : 'Generate Synthesized Brief'}</span>
            </button>

            {/* Recent Synthesized Documents List */}
            {documents.length > 0 && (
              <div style={{ marginTop: 'auto', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Recent Syntheses ({documents.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '120px', overflowY: 'auto' }}>
                  {documents.map((d) => (
                    <div
                      key={d.id}
                      onClick={() => setActiveDoc(d)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-xs)',
                        fontSize: '12px',
                        background: activeDoc?.id === d.id ? 'var(--accent-surface)' : 'var(--bg-surface-elevated)',
                        cursor: 'pointer',
                      }}
                    >
                      <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {d.title}
                      </span>
                      <button
                        className="btn-icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(d.id);
                        }}
                        style={{ border: 'none', background: 'transparent', width: '20px', height: '20px' }}
                      >
                        <Trash2 size={12} color="var(--text-muted)" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Live Preview Column */}
          <div
            style={{
              flex: 1,
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto',
              background: 'var(--bg-surface)',
            }}
          >
            {isGenerating && (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '16px',
                }}
              >
                <Sparkles size={40} color="var(--accent-primary)" className="animate-spin" />
                <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Synthesizing Knowledge Across Books...</h3>
                <div style={{ width: '320px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                    <span style={{ textTransform: 'capitalize' }}>
                      {jobStatus?.stage.replace(/_/g, ' ') || 'Extracting Cross-Book Outline'}
                    </span>
                    <span>{jobStatus?.percent_complete || 15}%</span>
                  </div>
                  <div style={{ height: '8px', background: 'var(--border-default)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${jobStatus?.percent_complete || 15}%`,
                        height: '100%',
                        background: 'var(--accent-primary)',
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {!isGenerating && activeDoc && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
                {/* Preview Toolbar */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-default)', paddingBottom: '12px' }}>
                  <div>
                    <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {activeDoc.title}
                    </h3>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {activeDoc.word_count} words &bull; {activeDoc.sources.length} sources cited
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <a
                      href={api.getSynthesisExportUrl(activeDoc.id, 'markdown')}
                      download
                      className="btn btn-secondary"
                    >
                      <Download size={14} />
                      <span>Markdown (.md)</span>
                    </a>
                    <a
                      href={api.getSynthesisExportUrl(activeDoc.id, 'html')}
                      download
                      className="btn btn-primary"
                    >
                      <Download size={14} />
                      <span>Styled HTML (.html)</span>
                    </a>
                  </div>
                </div>

                {/* Markdown Viewer */}
                <div
                  style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '1rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '13px',
                    lineHeight: 1.7,
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'monospace',
                  }}
                >
                  {activeDoc.content_markdown}
                </div>
              </div>
            )}

            {!isGenerating && !activeDoc && (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-muted)',
                  gap: '12px',
                }}
              >
                <Layers size={48} strokeWidth={1.5} />
                <h3 style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Ready to Synthesize</h3>
                <p style={{ fontSize: '13px', maxWidth: '380px', textAlign: 'center' }}>
                  Select books, configure a research topic, and click "Generate Synthesized Brief".
                  The 4-stage engine will ground every section with verified inline citations.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
