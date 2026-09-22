import React, { useState } from 'react';
import {
  FolderOpen,
  X,
  Plus,
  Check,
  HardDrive,
  FolderPlus,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';

export const ManageLibrariesModal: React.FC = () => {
  const {
    isManageLibrariesOpen,
    setManageLibrariesOpen,
    libraries,
    activeLibraryId,
    switchLibrary,
    loadLibraries,
    setToastMessage,
  } = useStore();

  const [activeTab, setActiveTab] = useState<'list' | 'adopt' | 'create'>('list');
  const [libPath, setLibPath] = useState<string>('');
  const [libName, setLibName] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isManageLibrariesOpen) return null;

  const handleSwitch = async (libId: string) => {
    try {
      await switchLibrary(libId);
      setToastMessage('Switched active library');
      setManageLibrariesOpen(false);
    } catch (err: any) {
      setErrorMessage(`Failed to switch library: ${err.message}`);
    }
  };

  const handleAdoptExisting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!libPath.trim()) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const trimmedPath = libPath.trim();
      const defaultName = libName.trim() || trimmedPath.split(/[/\\]/).filter(Boolean).pop() || 'Calibre Library';

      await api.adoptLibrary(trimmedPath, defaultName);
      await loadLibraries();
      setToastMessage(`Successfully adopted library "${defaultName}"`);
      setLibPath('');
      setLibName('');
      setActiveTab('list');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to adopt Calibre library');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateNew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!libPath.trim() || !libName.trim()) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await api.createLibrary(libPath.trim(), libName.trim(), false);
      await loadLibraries();
      setToastMessage(`Successfully created new library "${libName.trim()}"`);
      setLibPath('');
      setLibName('');
      setActiveTab('list');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create new library');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        padding: '1.5rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) setManageLibrariesOpen(false);
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '640px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'var(--bg-modal, #18181b)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg, 16px)',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden',
          animation: 'fadeIn 0.2s ease-out',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-md, 8px)',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FolderOpen size={18} />
            </div>
            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: '16px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                }}
              >
                Manage Calibre Libraries
              </h2>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Switch, adopt existing Calibre directories, or create new libraries
              </span>
            </div>
          </div>

          <button
            className="btn-icon"
            onClick={() => setManageLibrariesOpen(false)}
            disabled={isSubmitting}
            style={{ color: 'var(--text-muted)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface-elevated)',
            padding: '0 1.5rem',
            gap: '8px',
          }}
        >
          <button
            onClick={() => {
              setActiveTab('list');
              setErrorMessage(null);
            }}
            style={{
              padding: '10px 16px',
              border: 'none',
              background: 'none',
              fontSize: '13px',
              fontWeight: 600,
              color: activeTab === 'list' ? 'var(--accent-primary)' : 'var(--text-muted)',
              borderBottom: activeTab === 'list' ? '2px solid var(--accent-primary)' : '2px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <HardDrive size={15} />
            <span>Registered ({libraries.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('adopt');
              setErrorMessage(null);
            }}
            style={{
              padding: '10px 16px',
              border: 'none',
              background: 'none',
              fontSize: '13px',
              fontWeight: 600,
              color: activeTab === 'adopt' ? 'var(--accent-primary)' : 'var(--text-muted)',
              borderBottom: activeTab === 'adopt' ? '2px solid var(--accent-primary)' : '2px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Plus size={15} />
            <span>Adopt Existing Calibre</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('create');
              setErrorMessage(null);
            }}
            style={{
              padding: '10px 16px',
              border: 'none',
              background: 'none',
              fontSize: '13px',
              fontWeight: 600,
              color: activeTab === 'create' ? 'var(--accent-primary)' : 'var(--text-muted)',
              borderBottom: activeTab === 'create' ? '2px solid var(--accent-primary)' : '2px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <FolderPlus size={15} />
            <span>Create New Library</span>
          </button>
        </div>

        {/* Modal Body */}
        <div
          style={{
            padding: '1.5rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          {errorMessage && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#ef4444',
                fontSize: '13px',
              }}
            >
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Tab 1: Library List */}
          {activeTab === 'list' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {libraries.map((lib) => {
                const isActive = lib.id === activeLibraryId;
                return (
                  <div
                    key={lib.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isActive ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-surface-elevated)',
                      border: isActive ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>
                          {lib.name}
                        </span>
                        {isActive && (
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '11px',
                              fontWeight: 600,
                              backgroundColor: 'rgba(16, 185, 129, 0.15)',
                              color: '#10b981',
                              border: '1px solid rgba(16, 185, 129, 0.3)',
                            }}
                          >
                            Active
                          </span>
                        )}
                      </div>
                      <span
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-muted)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          maxWidth: '400px',
                        }}
                        title={lib.path}
                      >
                        {lib.path}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        {lib.book_count} books in library
                      </span>
                    </div>

                    {!isActive && (
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleSwitch(lib.id)}
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                      >
                        <span>Switch</span>
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Tab 2: Adopt Existing Calibre */}
          {activeTab === 'adopt' && (
            <form onSubmit={handleAdoptExisting} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div
                style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.5',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: '3px solid var(--accent-primary)',
                }}
              >
                Select an existing directory containing a Calibre <code>metadata.db</code> file.
                xBookLibrary will link to the library without modifying your files.
              </div>

              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: '6px',
                    textTransform: 'uppercase',
                  }}
                >
                  Library Directory Path *
                </label>
                <input
                  type="text"
                  className="input-text"
                  placeholder="e.g. C:\Users\Username\Calibre Library or /home/user/books"
                  value={libPath}
                  onChange={(e) => setLibPath(e.target.value)}
                  required
                />
              </div>

              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: '6px',
                    textTransform: 'uppercase',
                  }}
                >
                  Display Name (Optional)
                </label>
                <input
                  type="text"
                  className="input-text"
                  placeholder="e.g. Master Library"
                  value={libName}
                  onChange={(e) => setLibName(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting || !libPath.trim()}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={15} className="animate-spin" />
                      <span>Adopting...</span>
                    </>
                  ) : (
                    <>
                      <Check size={15} />
                      <span>Adopt Library</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Tab 3: Create New Library */}
          {activeTab === 'create' && (
            <form onSubmit={handleCreateNew} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div
                style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.5',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: '3px solid var(--accent-primary)',
                }}
              >
                Creates a new empty Calibre library directory with initialized <code>metadata.db</code> SQLite tables and Calibre schema compatibility.
              </div>

              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: '6px',
                    textTransform: 'uppercase',
                  }}
                >
                  New Library Directory Path *
                </label>
                <input
                  type="text"
                  className="input-text"
                  placeholder="e.g. C:\Books\SciFiCollection"
                  value={libPath}
                  onChange={(e) => setLibPath(e.target.value)}
                  required
                />
              </div>

              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: '6px',
                    textTransform: 'uppercase',
                  }}
                >
                  Library Name *
                </label>
                <input
                  type="text"
                  className="input-text"
                  placeholder="e.g. Sci-Fi & Fantasy Collection"
                  value={libName}
                  onChange={(e) => setLibName(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting || !libPath.trim() || !libName.trim()}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={15} className="animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    <>
                      <FolderPlus size={15} />
                      <span>Create New Library</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'flex-end',
            backgroundColor: 'var(--bg-surface-elevated)',
          }}
        >
          <button
            className="btn btn-secondary"
            onClick={() => setManageLibrariesOpen(false)}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
