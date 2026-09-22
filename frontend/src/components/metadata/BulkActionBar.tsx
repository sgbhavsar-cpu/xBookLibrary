import React, { useState } from 'react';
import { Edit3, X, CheckSquare, Repeat, Trash2, AlertTriangle, Loader2 } from 'lucide-react';
import { useStore } from '../../store/useStore';

export const BulkActionBar: React.FC = () => {
  const {
    selectedBookIds,
    books,
    clearSelectedBooks,
    selectAllBooks,
    setBulkEditOpen,
    openConversionModal,
    bulkDeleteBooks,
  } = useStore();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  if (selectedBookIds.length === 0) return null;

  const handleDeleteConfirm = async () => {
    setIsDeleting(true);
    try {
      await bulkDeleteBooks(selectedBookIds);
      setShowDeleteConfirm(false);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div
        style={{
          position: 'fixed',
          bottom: '24px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 40,
          animation: 'fadeIn 0.2s ease-out',
        }}
      >
        <div
          className="glass-panel"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-lg, 16px)',
            backgroundColor: 'var(--bg-modal, #18181b)',
            border: '1px solid var(--border-default)',
            boxShadow: 'var(--shadow-xl)',
            backdropFilter: 'blur(16px)',
            color: 'var(--text-primary)',
          }}
        >
          {/* Badge count */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '26px',
                height: '26px',
                borderRadius: '6px',
                backgroundColor: 'var(--accent-primary)',
                color: '#fff',
                fontSize: '12px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 6px var(--accent-glow)',
              }}
            >
              {selectedBookIds.length}
            </div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              {selectedBookIds.length === 1 ? '1 book' : `${selectedBookIds.length} books`}
            </span>
          </div>

          <div style={{ width: '1px', height: '18px', backgroundColor: 'var(--border-default)' }} />

          {/* Action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {selectedBookIds.length < books.length && (
              <button
                onClick={selectAllBooks}
                className="btn btn-secondary"
                style={{ fontSize: '12px', padding: '6px 10px' }}
                title="Select all books in current library"
              >
                <CheckSquare size={14} />
                <span>All ({books.length})</span>
              </button>
            )}

            {/* Convert selected */}
            <button
              onClick={() => openConversionModal(selectedBookIds)}
              className="btn btn-secondary"
              style={{
                fontSize: '12px',
                padding: '6px 12px',
                borderColor: 'rgba(99, 102, 241, 0.4)',
                color: 'var(--accent-primary)',
              }}
              title="Convert selected books to another format"
            >
              <Repeat size={14} />
              <span>Convert</span>
            </button>

            {/* Bulk Edit */}
            <button
              onClick={() => setBulkEditOpen(true)}
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '6px 12px' }}
              title="Edit tags, series, authors, or ratings across all selected books"
            >
              <Edit3 size={14} />
              <span>Bulk Edit</span>
            </button>

            {/* Bulk Delete */}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="btn btn-secondary"
              style={{
                fontSize: '12px',
                padding: '6px 12px',
                borderColor: 'rgba(239, 68, 68, 0.3)',
                color: '#ef4444',
              }}
              title="Delete selected books from library and disk"
            >
              <Trash2 size={14} />
              <span>Delete</span>
            </button>

            {/* Clear Selection */}
            <button
              onClick={clearSelectedBooks}
              title="Clear selection (Esc)"
              className="btn-icon"
              style={{
                color: 'var(--text-muted)',
                width: '28px',
                height: '28px',
              }}
            >
              <X size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Bulk Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 110,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            padding: '1.5rem',
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget && !isDeleting) setShowDeleteConfirm(false);
          }}
        >
          <div
            className="glass-panel"
            style={{
              width: '100%',
              maxWidth: '460px',
              backgroundColor: 'var(--bg-modal, #18181b)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: 'var(--radius-lg, 16px)',
              boxShadow: 'var(--shadow-xl)',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
              animation: 'fadeIn 0.2s ease-out',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(239, 68, 68, 0.15)',
                  color: '#ef4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <AlertTriangle size={22} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Delete {selectedBookIds.length} Books?
                </h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Calibre library permanent removal
                </span>
              </div>
            </div>

            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Are you sure you want to permanently delete these <strong>{selectedBookIds.length}</strong> selected books?
              This will remove the records from <code>metadata.db</code>, vector embeddings, and permanently delete the book files and folders from disk.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
              <button
                className="btn btn-secondary"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                style={{
                  backgroundColor: '#ef4444',
                  borderColor: '#ef4444',
                  color: '#fff',
                }}
              >
                {isDeleting ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 size={15} />
                    <span>Delete Permanently</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
