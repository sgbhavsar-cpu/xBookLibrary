import React, { useEffect } from 'react';
import { BookGrid } from './components/BookGrid';
import { BookTable } from './components/BookTable';
import { DetailInspector } from './components/DetailInspector';
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

export const App: React.FC = () => {
  const {
    readerBookId,
    viewMode,
    loadLibraries,
    activeAudiobook,
    isAudiobookPlayerOpen,
  } = useStore();

  useEffect(() => {
    loadLibraries();
  }, [loadLibraries]);

  // If reading a book, show the dedicated full-screen reader workspace
  if (readerBookId !== null) {
    return <ReaderView />;
  }

  const isMiniPlayerActive = activeAudiobook !== null && !isAudiobookPlayerOpen;

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        background: 'var(--bg-app)',
        color: 'var(--text-primary)',
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
        <FilterSidebar />

        {/* Center Pane: Virtualized Book Cover Grid / Classic Table */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <VirtualLibraryBar />
          {viewMode === 'grid' ? <BookGrid /> : <BookTable />}
        </main>

        {/* Right Pane: Detail Inspector & Knowledge Summaries */}
        <DetailInspector />
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
    </div>
  );
};

export default App;

