import React, { useEffect, useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { api } from './api/client';
import { BookGrid } from './components/BookGrid';
import { BookTable } from './components/BookTable';
import { DetailInspector } from './components/DetailInspector';
import { ErrorBoundary } from './components/ErrorBoundary';
import { FilterSidebar } from './components/FilterSidebar';
import { HeaderToolbar } from './components/HeaderToolbar';
import { IngestionModal } from './components/IngestionModal';
import { RAGChatDrawer } from './components/RAGChatDrawer';
import { StatusBar } from './components/StatusBar';
import { SynthesisStudioModal } from './components/SynthesisStudioModal';
import { VirtualLibraryBar } from './components/VirtualLibraryBar';
import { SendToDeviceModal } from './components/devices/SendToDeviceModal';
import { DeviceSettingsModal } from './components/devices/DeviceSettingsModal';
import { AudioController } from './components/audiobook/AudioController';
import { AudiobookPlayer } from './components/audiobook/AudiobookPlayer';
import { PersistentAudioBar } from './components/audiobook/PersistentAudioBar';
import { useStore } from './store/useStore';
import { ReaderView } from './views/ReaderView';
import { EditMetadataModal } from './components/metadata/EditMetadataModal';
import { BulkEditModal } from './components/metadata/BulkEditModal';
import { BulkActionBar } from './components/metadata/BulkActionBar';
import { ImportConflictModal, type DuplicateConflictInfo } from './components/metadata/ImportConflictModal';
import { FormatConversionModal } from './components/conversion/FormatConversionModal';
import { ManageLibrariesModal } from './components/library/ManageLibrariesModal';
import { PreferencesModal } from './components/preferences/PreferencesModal';

export const App: React.FC = () => {
  const {
    readerBookId,
    viewMode,
    loadLibraries,
    loadBooks,
    activeAudiobook,
    isAudiobookPlayerOpen,
    selectedBook,
    isEditMetadataOpen,
    setEditMetadataOpen,
    isBulkEditOpen,
    setBulkEditOpen,
    openConversionModal,
    openReader,
    clearSelectedBooks,
    selectedBookIds,
    toastMessage,
    setToastMessage,
  } = useStore();

  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [conflict, setConflict] = useState<DuplicateConflictInfo | null>(null);

  useEffect(() => {
    loadLibraries();
  }, [loadLibraries]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget === e.target) {
      setIsDraggingOver(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    for (const file of files) {
      try {
        const check = await api.checkBookDuplicate(file);
        if (check.duplicate && check.match) {
          setConflict({ file, match: check.match });
          return; // Pause for conflict prompt
        }
        await api.uploadBooks([file], 'merge');
        setToastMessage(`Imported "${file.name}" successfully`);
        await loadBooks();
      } catch (err: any) {
        console.error('Import error:', err);
        setToastMessage(`Import failed: ${err.message}`);
      }
    }
  };

  const handleResolveConflict = async (action: 'merge' | 'create_new' | 'skip') => {
    if (!conflict) return;
    const file = conflict.file;
    setConflict(null);
    if (action === 'skip') {
      setToastMessage(`Skipped "${file.name}"`);
      return;
    }
    try {
      await api.uploadBooks([file], action);
      setToastMessage(`Imported "${file.name}" (${action === 'create_new' ? 'New Book' : 'Merged'})`);
      await loadBooks();
    } catch (err: any) {
      setToastMessage(`Failed to import "${file.name}": ${err.message}`);
    }
  };

  // Global Calibre Hotkeys: E (Edit), C (Convert), V (View/Reader), Esc (Deselect)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeTag = document.activeElement?.tagName.toLowerCase();
      if (activeTag === 'input' || activeTag === 'textarea') return;

      // Escape -> Clear selected books
      if (e.key === 'Escape') {
        if (selectedBookIds.length > 0 || selectedBook) {
          clearSelectedBooks();
        }
        return;
      }

      // E -> Edit metadata
      if ((e.key === 'e' || e.key === 'E') && !isEditMetadataOpen && !isBulkEditOpen) {
        if (selectedBookIds.length > 1) {
          e.preventDefault();
          setBulkEditOpen(true);
        } else if (selectedBook) {
          e.preventDefault();
          setEditMetadataOpen(true);
        }
        return;
      }

      // C -> Convert book formats
      if ((e.key === 'c' || e.key === 'C')) {
        const idsToConvert = selectedBookIds.length > 0 ? selectedBookIds : (selectedBook ? [selectedBook.id] : []);
        if (idsToConvert.length > 0) {
          e.preventDefault();
          openConversionModal(idsToConvert);
        }
        return;
      }

      // V -> View / Read book
      if ((e.key === 'v' || e.key === 'V') && selectedBook && readerBookId === null) {
        e.preventDefault();
        openReader(selectedBook.id);
        return;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    selectedBook,
    selectedBookIds,
    isEditMetadataOpen,
    isBulkEditOpen,
    readerBookId,
    setEditMetadataOpen,
    setBulkEditOpen,
    openConversionModal,
    openReader,
    clearSelectedBooks,
  ]);

  // If reading a book, show the dedicated full-screen reader workspace
  if (readerBookId !== null) {
    return <ReaderView />;
  }

  const isMiniPlayerActive = activeAudiobook !== null && !isAudiobookPlayerOpen;

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        background: 'var(--bg-app)',
        color: 'var(--text-primary)',
        position: 'relative',
      }}
    >
      {/* 1. Header & Global Toolbar */}
      <HeaderToolbar />

      {/* 2. Responsive 3-Pane Body */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          overflow: 'hidden',
          position: 'relative',
          paddingBottom: isMiniPlayerActive ? '64px' : undefined,
          transition: 'padding-bottom 0.2s ease',
        }}
      >
        {/* Left Pane: Hierarchy & Taxonomy Filter Sidebar */}
        <ErrorBoundary fallbackTitle="Filter Sidebar Error">
          <FilterSidebar />
        </ErrorBoundary>

        {/* Center Pane: Virtualized Book Cover Grid / Classic Table */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <ErrorBoundary fallbackTitle="Virtual Library Bar Error">
            <VirtualLibraryBar />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Catalog View Error">
            {viewMode === 'grid' ? <BookGrid /> : <BookTable />}
          </ErrorBoundary>
        </main>

        {/* Right Pane: Detail Inspector & Knowledge Summaries */}
        <ErrorBoundary fallbackTitle="Inspector Error">
          <DetailInspector />
        </ErrorBoundary>
      </div>

      {/* 3. Bottom Status Bar */}
      <StatusBar />

      {/* Headless Audio Controller (always active during playback) */}
      {activeAudiobook && <AudioController />}

      {/* Persistent Mini-Player Bar (visible in library mode) */}
      <PersistentAudioBar />

      {/* Full Audiobook Player Workspace (modal overlay) */}
      {activeAudiobook && isAudiobookPlayerOpen && <AudiobookPlayer />}

      {/* Global Drawers & Modals */}
      <RAGChatDrawer />
      <SynthesisStudioModal />
      <IngestionModal />
      <SendToDeviceModal />
      <DeviceSettingsModal />

      {/* Core Metadata Editor & Bulk Management Modals (Feature 015) */}
      <BulkActionBar />
      <EditMetadataModal
        isOpen={isEditMetadataOpen}
        onClose={() => setEditMetadataOpen(false)}
        book={selectedBook}
      />
      <BulkEditModal
        isOpen={isBulkEditOpen}
        onClose={() => setBulkEditOpen(false)}
      />

      {/* Duplicate Conflict Prompt Modal (Feature 015 US5) */}
      <ImportConflictModal
        isOpen={conflict !== null}
        conflict={conflict}
        onResolve={handleResolveConflict}
        onClose={() => setConflict(null)}
      />

      {/* Calibre Format Conversion Modal */}
      <FormatConversionModal />

      {/* Calibre Library Manager Modal */}
      <ManageLibrariesModal />

      {/* Calibre Preferences & Admin Console Modal */}
      <PreferencesModal />

      {/* Global Drag-and-Drop Visual Overlay (Feature 015 US5) */}
      {isDraggingOver && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 100,
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(10px)',
            border: '3px dashed var(--accent-primary, #6366f1)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '50%',
              background: 'var(--accent-surface, rgba(99, 102, 241, 0.2))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-primary, #818cf8)',
            }}
          >
            <UploadCloud size={38} />
          </div>
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, margin: '0 0 6px 0', color: '#fff' }}>
              Drop Books to Ingest into Library
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary, #94a3b8)', margin: 0 }}>
              Automatic format detection, metadata extraction, and duplicate handling
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center', maxWidth: '400px' }}>
            {['EPUB', 'PDF', 'MOBI', 'AZW3', 'CBZ', 'CBR', 'DOCX', 'AUDIO'].map((fmt) => (
              <span
                key={fmt}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: '#e2e8f0',
                  padding: '4px 10px',
                  borderRadius: '16px',
                  fontSize: '11px',
                  fontWeight: 600,
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                }}
              >
                {fmt}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Global Toast Notification */}
      {toastMessage && (
        <div
          className="glass-panel"
          style={{
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 120,
            backgroundColor: 'var(--bg-modal, #18181b)',
            border: '1px solid var(--accent-primary)',
            color: 'var(--text-primary)',
            fontSize: '13px',
            fontWeight: 600,
            padding: '10px 18px',
            borderRadius: 'var(--radius-lg, 12px)',
            boxShadow: 'var(--shadow-xl)',
            backdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            animation: 'fadeIn 0.2s ease-out',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--accent-primary)',
              boxShadow: '0 0 8px var(--accent-primary)',
            }}
          />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
};

export default App;

