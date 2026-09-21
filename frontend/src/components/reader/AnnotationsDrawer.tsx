import React, { useState } from 'react';
import {
  Bookmark,
  Download,
  Highlighter,
  Plus,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';

interface AnnotationsDrawerProps {
  bookId: number;
  onNavigateToLocation?: (location: string) => void;
}

export const AnnotationsDrawer: React.FC<AnnotationsDrawerProps> = ({
  bookId,
  onNavigateToLocation,
}) => {
  const {
    activeLibraryId,
    readerAnnotations,
    readerBookmarks,
    removeAnnotation,
    removeBookmark,
    addBookmark,
    readerProgress,
    readerFormat,
    toggleAnnotationsDrawer,
  } = useStore();

  const [activeTab, setActiveTab] = useState<'annotations' | 'bookmarks'>('annotations');
  const [selectedColor, setSelectedColor] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [newBookmarkTitle, setNewBookmarkTitle] = useState<string>('');
  const [isAddingBookmark, setIsAddingBookmark] = useState<boolean>(false);

  const colors = ['yellow', 'green', 'blue', 'pink', 'purple'];

  const colorMap: Record<string, string> = {
    yellow: '#eab308',
    green: '#22c55e',
    blue: '#3b82f6',
    pink: '#ec4899',
    purple: '#a855f7',
  };

  const filteredAnnotations = readerAnnotations.filter((ann) => {
    if (selectedColor !== 'all' && ann.color !== selectedColor) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const textMatch = ann.selected_text.toLowerCase().includes(q);
      const noteMatch = ann.note_text?.toLowerCase().includes(q);
      const chapMatch = ann.chapter_title?.toLowerCase().includes(q);
      return textMatch || noteMatch || chapMatch;
    }
    return true;
  });

  const handleCreateBookmark = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBookmarkTitle.trim()) return;
    const loc = readerProgress?.location || 'start';
    await addBookmark({
      format: readerFormat || 'EPUB',
      location: loc,
      title: newBookmarkTitle.trim(),
    });
    setNewBookmarkTitle('');
    setIsAddingBookmark(false);
  };

  const handleExport = () => {
    if (!activeLibraryId) return;
    const exportUrl = api.getAnnotationsExportUrl(activeLibraryId, bookId);
    window.open(exportUrl, '_blank');
  };

  return (
    <div
      style={{
        width: '360px',
        height: '100%',
        background: '#0f172a',
        borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 50,
        boxShadow: '-8px 0 25px rgba(0,0,0,0.5)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Highlighter size={18} color="#818cf8" />
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', margin: 0 }}>
            Notes & Bookmarks
          </h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleExport}
            className="btn-icon"
            style={{ color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}
            title="Export Notes to Markdown"
          >
            <Download size={16} />
          </button>
          <button
            onClick={toggleAnnotationsDrawer}
            className="btn-icon"
            style={{ color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}
            title="Close Drawer"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(255, 255, 255, 0.02)',
        }}
      >
        <button
          onClick={() => setActiveTab('annotations')}
          style={{
            flex: 1,
            padding: '10px',
            fontSize: '13px',
            fontWeight: 500,
            background: 'none',
            border: 'none',
            color: activeTab === 'annotations' ? '#818cf8' : '#94a3b8',
            borderBottom: activeTab === 'annotations' ? '2px solid #818cf8' : 'none',
            cursor: 'pointer',
          }}
        >
          Highlights ({readerAnnotations.length})
        </button>
        <button
          onClick={() => setActiveTab('bookmarks')}
          style={{
            flex: 1,
            padding: '10px',
            fontSize: '13px',
            fontWeight: 500,
            background: 'none',
            border: 'none',
            color: activeTab === 'bookmarks' ? '#818cf8' : '#94a3b8',
            borderBottom: activeTab === 'bookmarks' ? '2px solid #818cf8' : 'none',
            cursor: 'pointer',
          }}
        >
          Bookmarks ({readerBookmarks.length})
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {activeTab === 'annotations' ? (
          <div>
            {/* Color Filter Chips */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginBottom: '12px',
                flexWrap: 'wrap',
              }}
            >
              <button
                onClick={() => setSelectedColor('all')}
                style={{
                  fontSize: '11px',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  background: selectedColor === 'all' ? '#4f46e5' : 'none',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                All
              </button>
              {colors.map((c) => (
                <button
                  key={c}
                  onClick={() => setSelectedColor(c)}
                  style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    background: colorMap[c],
                    border: selectedColor === c ? '2px solid #fff' : 'none',
                    cursor: 'pointer',
                    opacity: selectedColor === 'all' || selectedColor === c ? 1 : 0.4,
                  }}
                  title={`Filter by ${c}`}
                />
              ))}
            </div>

            {/* Search Input */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '6px',
                padding: '6px 10px',
                marginBottom: '16px',
                gap: '8px',
              }}
            >
              <Search size={14} color="#94a3b8" />
              <input
                type="text"
                placeholder="Search highlights and notes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#fff',
                  fontSize: '12px',
                  outline: 'none',
                  width: '100%',
                }}
              />
            </div>

            {/* List */}
            {filteredAnnotations.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: '30px 10px',
                  color: '#64748b',
                  fontSize: '13px',
                }}
              >
                No highlights yet. Select text in the book to highlight or add notes.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {filteredAnnotations.map((ann) => (
                  <div
                    key={ann.id}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      borderRadius: '8px',
                      padding: '12px',
                      borderLeft: `3px solid ${colorMap[ann.color] || '#eab308'}`,
                      position: 'relative',
                    }}
                  >
                    {ann.chapter_title && (
                      <div
                        style={{
                          fontSize: '11px',
                          color: '#818cf8',
                          fontWeight: 500,
                          marginBottom: '4px',
                        }}
                      >
                        {ann.chapter_title}
                      </div>
                    )}
                    <div
                      onClick={() => onNavigateToLocation && onNavigateToLocation(ann.location)}
                      style={{
                        fontSize: '13px',
                        color: '#e2e8f0',
                        lineHeight: '1.4',
                        cursor: onNavigateToLocation ? 'pointer' : 'default',
                      }}
                      title="Click to jump to quote in text"
                    >
                      "{ann.selected_text}"
                    </div>
                    {ann.note_text && (
                      <div
                        style={{
                          marginTop: '8px',
                          padding: '6px 10px',
                          background: 'rgba(255, 255, 255, 0.05)',
                          borderRadius: '6px',
                          fontSize: '12px',
                          color: '#93c5fd',
                        }}
                      >
                        <strong>Note:</strong> {ann.note_text}
                      </div>
                    )}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginTop: '8px',
                      }}
                    >
                      <span style={{ fontSize: '10px', color: '#64748b' }}>
                        {ann.created_at ? new Date(ann.created_at).toLocaleDateString() : ''}
                      </span>
                      <button
                        onClick={() => removeAnnotation(ann.id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#ef4444',
                          cursor: 'pointer',
                          padding: '2px',
                          opacity: 0.6,
                        }}
                        title="Delete highlight"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div>
            {/* Bookmarks Tab */}
            <div style={{ marginBottom: '16px' }}>
              {isAddingBookmark ? (
                <form onSubmit={handleCreateBookmark} style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    placeholder="Bookmark title..."
                    value={newBookmarkTitle}
                    onChange={(e) => setNewBookmarkTitle(e.target.value)}
                    autoFocus
                    style={{
                      flex: 1,
                      padding: '6px 10px',
                      background: 'rgba(255,255,255,0.08)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '6px',
                      color: '#fff',
                      fontSize: '12px',
                      outline: 'none',
                    }}
                  />
                  <button
                    type="submit"
                    style={{
                      padding: '6px 12px',
                      background: '#4f46e5',
                      border: 'none',
                      borderRadius: '6px',
                      color: '#fff',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsAddingBookmark(false)}
                    style={{
                      padding: '6px',
                      background: 'none',
                      border: 'none',
                      color: '#94a3b8',
                      cursor: 'pointer',
                    }}
                  >
                    <X size={14} />
                  </button>
                </form>
              ) : (
                <button
                  onClick={() => setIsAddingBookmark(true)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    background: 'rgba(79, 70, 229, 0.15)',
                    border: '1px dashed #6366f1',
                    borderRadius: '6px',
                    color: '#818cf8',
                    fontSize: '13px',
                    cursor: 'pointer',
                  }}
                >
                  <Plus size={15} /> Bookmark Current Page
                </button>
              )}
            </div>

            {readerBookmarks.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: '30px 10px',
                  color: '#64748b',
                  fontSize: '13px',
                }}
              >
                No bookmarks saved yet. Click the button above to bookmark your current location.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {readerBookmarks.map((bm) => (
                  <div
                    key={bm.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 12px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      borderRadius: '6px',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                    }}
                  >
                    <div
                      onClick={() => onNavigateToLocation && onNavigateToLocation(bm.location)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        cursor: onNavigateToLocation ? 'pointer' : 'default',
                        color: '#f8fafc',
                        fontSize: '13px',
                      }}
                      title="Click to jump to bookmark"
                    >
                      <Bookmark size={14} color="#f59e0b" />
                      <span>{bm.title}</span>
                    </div>
                    <button
                      onClick={() => removeBookmark(bm.id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#ef4444',
                        cursor: 'pointer',
                        padding: '2px',
                        opacity: 0.6,
                      }}
                      title="Delete bookmark"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
