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
import { useStore } from './store/useStore';
import { ReaderView } from './views/ReaderView';

export const App: React.FC = () => {
  const {
    readerBookId,
    viewMode,
    loadLibraries,
  } = useStore();

  useEffect(() => {
    loadLibraries();
  }, [loadLibraries]);

  // If reading a book, show the dedicated full-screen reader workspace
  if (readerBookId !== null) {
    return <ReaderView />;
  }

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
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        {/* Left Pane: Hierarchy & Taxonomy Filter Sidebar */}
        <FilterSidebar />

        {/* Center Pane: Virtualized Book Cover Grid / Classic Table */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {viewMode === 'grid' ? <BookGrid /> : <BookTable />}
        </main>

        {/* Right Pane: Detail Inspector & Knowledge Summaries */}
        <DetailInspector />
      </div>

      {/* 3. Bottom Status Bar */}
      <StatusBar />

      {/* Global Drawers & Modals */}
      <RAGChatDrawer />
      <SynthesisStudioModal />
      <IngestionModal />
    </div>
  );
};

export default App;
