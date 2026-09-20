import React, { useState } from 'react';
import {
  Bookmark,
  Layers,
  Plus,
  Sliders,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';

export const VirtualLibraryBar: React.FC = () => {
  const {
    books,
    activeLibraryId,
    virtualLibraries,
    activeVirtualLibrary,
    setActiveVirtualLibrary,
    loadVirtualLibraries,
    customColumns,
    loadCustomColumns,
  } = useStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newLibName, setNewLibName] = useState('');
  const [newLibQuery, setNewLibQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isInstallingPresets, setIsInstallingPresets] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeLibraryId || !newLibName.trim() || !newLibQuery.trim()) return;

    setIsSubmitting(true);
    try {
      await api.createVirtualLibrary(activeLibraryId, {
        name: newLibName.trim(),
        query: newLibQuery.trim(),
      });
      await loadVirtualLibraries();
      setActiveVirtualLibrary(newLibName.trim());
      setNewLibName('');
      setNewLibQuery('');
      setIsModalOpen(false);
    } catch (err) {
      console.error('Failed to create virtual library:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, name: string) => {
    e.stopPropagation();
    if (!activeLibraryId) return;
    try {
      await api.deleteVirtualLibrary(activeLibraryId, name);
      if (activeVirtualLibrary === name) {
        setActiveVirtualLibrary(null);
      }
      await loadVirtualLibraries();
    } catch (err) {
      console.error('Failed to delete virtual library:', err);
    }
  };

  const handleInstallPresets = async () => {
    if (!activeLibraryId) return;
    setIsInstallingPresets(true);
    try {
      await api.installCustomColumnPresets(activeLibraryId);
      await loadCustomColumns();
    } catch (err) {
      console.error('Failed to install presets:', err);
    } finally {
      setIsInstallingPresets(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '6px 1rem',
        borderBottom: '1px solid var(--border-default)',
        background: 'var(--bg-surface)',
        gap: '8px',
        overflowX: 'auto',
        minHeight: '40px',
      }}
    >
      {/* Tab Row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flex: 1 }}>
        {/* All Books Default Tab */}
        <button
          onClick={() => setActiveVirtualLibrary(null)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            background:
              activeVirtualLibrary === null ? 'var(--accent-primary)' : 'transparent',
            color: activeVirtualLibrary === null ? '#fff' : 'var(--text-secondary)',
            fontWeight: activeVirtualLibrary === null ? 600 : 500,
            fontSize: '12px',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <Layers size={13} />
          <span>All Books</span>
          <span
            style={{
              fontSize: '10px',
              opacity: 0.8,
              padding: '1px 5px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.15)',
            }}
          >
            {books.length}
          </span>
        </button>

        {/* Dynamic Virtual Library Tabs */}
        {virtualLibraries.map((vl) => {
          const isActive = activeVirtualLibrary === vl.name;
          return (
            <div
              key={vl.name}
              onClick={() => setActiveVirtualLibrary(vl.name)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                background: isActive ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '12px',
                cursor: 'pointer',
                border: `1px solid ${isActive ? 'transparent' : 'var(--border-default)'}`,
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
              title={`Filter: ${vl.query}`}
            >
              <Bookmark size={12} />
              <span>{vl.name}</span>
              <button
                onClick={(e) => handleDelete(e, vl.name)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  color: isActive ? 'rgba(255,255,255,0.7)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  marginLeft: '2px',
                }}
                title="Remove virtual library tab"
              >
                <Trash2 size={11} />
              </button>
            </div>
          );
        })}

        {/* Add Tab Button */}
        <button
          onClick={() => setIsModalOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--border-default)',
            background: 'transparent',
            color: 'var(--text-muted)',
            fontSize: '11px',
            fontWeight: 500,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
          title="Create a new virtual library tab"
        >
          <Plus size={12} />
          <span>New Tab</span>
        </button>
      </div>

      {/* Right Action: Presets Installer (if none configured) */}
      {customColumns.length === 0 && (
        <button
          onClick={handleInstallPresets}
          disabled={isInstallingPresets}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '3px 8px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--accent-glow)',
            background: 'var(--accent-surface)',
            color: 'var(--accent-primary)',
            fontSize: '11px',
            fontWeight: 600,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
          title="Install Calibre standard presets (#read_status, #rating, #pages, #difficulty)"
        >
          <Sparkles size={12} />
          <span>{isInstallingPresets ? 'Installing...' : 'Install Custom Columns'}</span>
        </button>
      )}

      {/* Create Virtual Library Modal */}
      {isModalOpen && (
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
            padding: '1.5rem',
          }}
          onClick={() => setIsModalOpen(false)}
        >
          <div
            className="glass-panel"
            style={{
              width: '100%',
              maxWidth: '460px',
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
              boxShadow: 'var(--shadow-glass)',
              border: '1px solid var(--border-default)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                padding: '1rem 1.25rem',
                borderBottom: '1px solid var(--border-default)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'var(--bg-surface-elevated)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={16} color="var(--accent-primary)" />
                <h3 style={{ fontSize: '14px', fontWeight: 700, margin: 0 }}>
                  Create Virtual Library
                </h3>
              </div>
              <button className="btn-icon" onClick={() => setIsModalOpen(false)}>
                <X size={15} />
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
                  Virtual Library Name
                </label>
                <input
                  type="text"
                  className="input-text"
                  placeholder="e.g. Currently Reading, Sci-Fi Favorites"
                  value={newLibName}
                  onChange={(e) => setNewLibName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
                  Search Query Expression
                </label>
                <input
                  type="text"
                  className="input-text"
                  placeholder="e.g. #read_status:Reading or tag:&quot;Science Fiction&quot;"
                  value={newLibQuery}
                  onChange={(e) => setNewLibQuery(e.target.value)}
                  required
                />
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', lineHeight: 1.5 }}>
                  <strong>Examples:</strong>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                    <span
                      style={{ background: 'var(--bg-card)', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer', fontFamily: 'monospace' }}
                      onClick={() => setNewLibQuery('#read_status:Reading')}
                    >
                      #read_status:Reading
                    </span>
                    <span
                      style={{ background: 'var(--bg-card)', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer', fontFamily: 'monospace' }}
                      onClick={() => setNewLibQuery('#read_status:Unread')}
                    >
                      #read_status:Unread
                    </span>
                    <span
                      style={{ background: 'var(--bg-card)', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer', fontFamily: 'monospace' }}
                      onClick={() => setNewLibQuery('series:"Foundation"')}
                    >
                      series:"Foundation"
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting || !newLibName.trim() || !newLibQuery.trim()}
                >
                  {isSubmitting ? 'Saving...' : 'Save Virtual Library'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
