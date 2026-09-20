import React, { useState } from 'react';
import {
  CheckCircle,
  File,
  FileUp,
  UploadCloud,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import type { IngestionJob } from '../types';

export const IngestionModal: React.FC = () => {
  const { isIngestModalOpen, setIngestModalOpen, loadBooks } = useStore();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [dragOver, setDragOver] = useState(false);

  if (!isIngestModalOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setIsUploading(true);
    try {
      const results = await api.uploadBooks(selectedFiles);
      setJobs(results);
      setSelectedFiles([]);
      await loadBooks();
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setIsUploading(false);
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
          maxWidth: '560px',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        {/* Header */}
        <div
          style={{
            height: '56px',
            padding: '0 1.25rem',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UploadCloud size={18} color="var(--accent-primary)" />
            <h3 style={{ fontSize: '15px', fontWeight: 700 }}>Import Books Into Library</h3>
          </div>
          <button className="btn-icon" onClick={() => setIngestModalOpen(false)}>
            <X size={15} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Drag & Drop Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            style={{
              border: `2px dashed ${dragOver ? 'var(--accent-primary)' : 'var(--border-default)'}`,
              borderRadius: 'var(--radius-md)',
              padding: '2rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              background: dragOver ? 'var(--accent-surface)' : 'var(--bg-surface-elevated)',
              cursor: 'pointer',
              gap: '8px',
            }}
            onClick={() => document.getElementById('book-upload-input')?.click()}
          >
            <FileUp size={36} color="var(--accent-primary)" />
            <div style={{ fontWeight: 600, fontSize: '13px' }}>
              Drag & Drop book files here, or click to browse
            </div>
            <div style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
              Supports EPUB, PDF, MOBI, CBZ, and DOCX
            </div>
            <input
              id="book-upload-input"
              type="file"
              multiple
              accept=".epub,.pdf,.mobi,.cbz,.docx"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '140px', overflowY: 'auto' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Selected Files ({selectedFiles.length}):
              </div>
              {selectedFiles.map((f, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-xs)',
                    background: 'var(--bg-surface-elevated)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
                    <File size={13} color="var(--text-muted)" />
                    <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {f.name}
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {Math.round(f.size / 1024)} KB
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Ingestion Results */}
          {jobs.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle size={14} />
                <span>Successfully Ingested {jobs.length} Book(s)</span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setIngestModalOpen(false)}
            >
              Close
            </button>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={selectedFiles.length === 0 || isUploading}
            >
              <UploadCloud size={14} />
              <span>{isUploading ? 'Ingesting...' : `Import ${selectedFiles.length} File(s)`}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
