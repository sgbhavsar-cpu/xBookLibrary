import React, { useState } from 'react';
import {
  BookOpen,
  FolderOpen,
  Grid,
  List,
  MessageSquare,
  Moon,
  Search,
  Sparkles,
  Sun,
  UploadCloud,
  Wifi,
  X,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { OpdsFeedModal } from './OpdsFeedModal';

export const HeaderToolbar: React.FC = () => {
  const [isOpdsModalOpen, setIsOpdsModalOpen] = useState(false);
  const {
    libraries,
    activeLibraryId,
    switchLibrary,
    searchQuery,
    setSearchQuery,
    viewMode,
    setViewMode,
    theme,
    toggleTheme,
    setRAGChatOpen,
    setSynthesisModalOpen,
    setIngestModalOpen,
  } = useStore();

  return (
    <header className="glass-panel" style={{
      height: 'var(--header-height)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 1.25rem',
      zIndex: 20,
      gap: '1rem',
      borderBottom: '1px solid var(--border-default)',
    }}>
      {/* Brand & Library Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            background: 'linear-gradient(135deg, var(--accent-primary), #8b5cf6)',
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 2px 8px var(--accent-glow)',
          }}>
            <BookOpen size={18} />
          </div>
          <span style={{
            fontWeight: 700,
            fontSize: '16px',
            letterSpacing: '-0.02em',
            background: 'linear-gradient(135deg, var(--text-primary), var(--accent-primary))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            xBookLibrary
          </span>
        </div>

        {/* Library Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <FolderOpen size={16} color="var(--text-muted)" />
          <select
            value={activeLibraryId || ''}
            onChange={(e) => switchLibrary(e.target.value)}
            style={{
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-surface-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-default)',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {libraries.map((lib) => (
              <option key={lib.id} value={lib.id}>
                {lib.name} ({lib.book_count} books)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Global Search Bar */}
      <div style={{ flex: 1, maxWidth: '420px', position: 'relative' }}>
        <Search
          size={16}
          style={{
            position: 'absolute',
            left: '10px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)',
          }}
        />
        <input
          type="text"
          className="input-text"
          placeholder="Search by title, author, tag, BISAC/DDC..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ paddingLeft: '32px', paddingRight: searchQuery ? '30px' : '12px' }}
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            style={{
              position: 'absolute',
              right: '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              display: 'flex',
            }}
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Action Controls & AI Launchers */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* View Mode Toggle */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-surface-elevated)',
          borderRadius: 'var(--radius-sm)',
          padding: '2px',
          border: '1px solid var(--border-default)',
        }}>
          <button
            className="btn-icon"
            style={{
              border: 'none',
              background: viewMode === 'grid' ? 'var(--bg-card)' : 'transparent',
              color: viewMode === 'grid' ? 'var(--accent-primary)' : 'var(--text-muted)',
              boxShadow: viewMode === 'grid' ? 'var(--shadow-sm)' : 'none',
            }}
            onClick={() => setViewMode('grid')}
            title="Grid / Cover Flow"
          >
            <Grid size={16} />
          </button>
          <button
            className="btn-icon"
            style={{
              border: 'none',
              background: viewMode === 'table' ? 'var(--bg-card)' : 'transparent',
              color: viewMode === 'table' ? 'var(--accent-primary)' : 'var(--text-muted)',
              boxShadow: viewMode === 'table' ? 'var(--shadow-sm)' : 'none',
            }}
            onClick={() => setViewMode('table')}
            title="Dense Calibre Table"
          >
            <List size={16} />
          </button>
        </div>

        {/* Upload Button */}
        <button
          className="btn btn-secondary"
          onClick={() => setIngestModalOpen(true)}
          title="Import books into library"
        >
          <UploadCloud size={15} />
          <span>Import</span>
        </button>

        {/* OPDS Wireless Feed */}
        <button
          className="btn btn-secondary"
          onClick={() => setIsOpdsModalOpen(true)}
          title="OPDS wireless feed for KOReader & Moon+ Reader"
          style={{ borderColor: 'rgba(16, 185, 129, 0.4)' }}
        >
          <Wifi size={15} color="#10b981" />
          <span>OPDS Feed</span>
        </button>

        {/* RAG QA Chat Launcher */}
        <button
          className="btn btn-secondary"
          onClick={() => setRAGChatOpen(true)}
          title="Ask library conversational AI"
          style={{ borderColor: 'var(--accent-glow)' }}
        >
          <MessageSquare size={15} color="var(--accent-primary)" />
          <span>Library Chat</span>
        </button>

        {/* Synthesis Studio Launcher */}
        <button
          className="btn btn-primary"
          onClick={() => setSynthesisModalOpen(true)}
          title="Generate multi-book research brief"
        >
          <Sparkles size={15} />
          <span>Synthesis Studio</span>
        </button>

        {/* Theme Toggle */}
        <button
          className="btn-icon"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>

      <OpdsFeedModal isOpen={isOpdsModalOpen} onClose={() => setIsOpdsModalOpen(false)} />
    </header>
  );
};
