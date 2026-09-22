import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Save,
  Download,
  Upload,
  Star,
  Plus,
  Image as ImageIcon,
  Loader2,
  BookOpen,
  Tag,
  Hash,
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';
import { OnlineMetadataDrawer } from './OnlineMetadataDrawer';
import type { Book, OnlineMetadataCandidate } from '../../types';

interface EditMetadataModalProps {
  isOpen: boolean;
  onClose: () => void;
  book: Book | null;
}

export const EditMetadataModal: React.FC<EditMetadataModalProps> = ({
  isOpen,
  onClose,
  book,
}) => {
  const { loadBooks, selectBook, setToastMessage } = useStore();

  // Form State
  const [title, setTitle] = useState('');
  const [sortTitle, setSortTitle] = useState('');
  const [authors, setAuthors] = useState<string[]>([]);
  const [authorInput, setAuthorInput] = useState('');
  const [authorSort, setAuthorSort] = useState('');
  const [publisher, setPublisher] = useState('');
  const [pubdate, setPubdate] = useState('');
  const [rating, setRating] = useState<number>(0);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [seriesName, setSeriesName] = useState('');
  const [seriesIndex, setSeriesIndex] = useState<number>(1.0);
  const [isbn, setIsbn] = useState('');
  const [identifiers, setIdentifiers] = useState<Record<string, string>>({});
  const [newIdType, setNewIdType] = useState('');
  const [newIdVal, setNewIdVal] = useState('');
  const [comments, setComments] = useState('');

  // Cover State
  const [coverPreviewUrl, setCoverPreviewUrl] = useState<string | null>(null);
  const [stagedCoverFile, setStagedCoverFile] = useState<File | null>(null);
  const [isCoverDragging, setIsCoverDragging] = useState(false);

  // Sub-drawer State
  const [isOnlineDrawerOpen, setIsOnlineDrawerOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && book) {
      setTitle(book.title || '');
      setSortTitle(book.sort || book.sort_title || book.title || '');
      setAuthors(book.authors && book.authors.length > 0 ? [...book.authors] : []);
      setAuthorSort(book.sort || (book.authors ? book.authors.join(', ') : ''));
      setPublisher(book.publisher || '');
      setPubdate(book.pubdate || (book.publication_year ? String(book.publication_year) : ''));
      const existingRating = book.custom_values?.rating ?? book.rating ?? 0;
      setRating(existingRating);
      setTags(book.tags ? [...book.tags] : []);
      setSeriesName(book.series || book.series_name || '');
      setSeriesIndex(book.series_index ?? 1.0);
      setIsbn(book.isbn || '');
      setIdentifiers(book.identifiers ? { ...book.identifiers } : {});
      setComments(book.comments || book.description || '');
      setStagedCoverFile(null);
      setSaveError(null);

      // Cover URL
      if (book.has_cover) {
        setCoverPreviewUrl(`/api/books/${book.id}/cover?t=${Date.now()}`);
      } else {
        setCoverPreviewUrl(null);
      }
    }
  }, [isOpen, book]);

  // Global Keyboard Shortcuts inside Modal
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isOnlineDrawerOpen) {
        onClose();
      } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        handleSave();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isOnlineDrawerOpen, title, authors, publisher, pubdate, rating, tags, seriesName, seriesIndex, isbn, comments, stagedCoverFile]);

  // Clipboard paste listener for cover image
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/')) {
        const file = items[i].getAsFile();
        if (file) {
          setStagedCoverFile(file);
          setCoverPreviewUrl(URL.createObjectURL(file));
          setToastMessage('Cover image pasted from clipboard');
        }
        break;
      }
    }
  };

  const handleCoverDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsCoverDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0 && files[0].type.startsWith('image/')) {
      const file = files[0];
      setStagedCoverFile(file);
      setCoverPreviewUrl(URL.createObjectURL(file));
      setToastMessage('Cover image staged');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setStagedCoverFile(file);
      setCoverPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleAddAuthor = () => {
    if (authorInput.trim() && !authors.includes(authorInput.trim())) {
      setAuthors([...authors, authorInput.trim()]);
      setAuthorInput('');
    }
  };

  const handleRemoveAuthor = (idx: number) => {
    setAuthors(authors.filter((_, i) => i !== idx));
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (t: string) => {
    setTags(tags.filter((item) => item !== t));
  };

  const handleAddIdentifier = () => {
    if (newIdType.trim() && newIdVal.trim()) {
      setIdentifiers({
        ...identifiers,
        [newIdType.trim().toLowerCase()]: newIdVal.trim(),
      });
      setNewIdType('');
      setNewIdVal('');
    }
  };

  const handleRemoveIdentifier = (key: string) => {
    const copy = { ...identifiers };
    delete copy[key];
    setIdentifiers(copy);
  };

  const handleApplyOnlineCandidate = async (
    cand: OnlineMetadataCandidate,
    fields: {
      title: boolean;
      authors: boolean;
      publisher: boolean;
      published_date: boolean;
      description: boolean;
      tags: boolean;
      isbn: boolean;
      cover: boolean;
    }
  ) => {
    if (fields.title && cand.title) {
      setTitle(cand.title);
      setSortTitle(cand.title);
    }
    if (fields.authors && cand.authors && cand.authors.length > 0) {
      setAuthors(cand.authors);
      setAuthorSort(cand.authors[0]);
    }
    if (fields.publisher && cand.publisher) {
      setPublisher(cand.publisher);
    }
    if (fields.published_date && cand.published_date) {
      setPubdate(cand.published_date);
    }
    if (fields.description && cand.description) {
      setComments(cand.description);
    }
    if (fields.tags && cand.tags && cand.tags.length > 0) {
      const merged = Array.from(new Set([...tags, ...cand.tags]));
      setTags(merged);
    }
    if (fields.isbn && cand.isbn) {
      setIsbn(cand.isbn);
    }
    if (fields.cover && cand.cover_url) {
      try {
        setToastMessage('Fetching high-resolution cover image...');
        const res = await fetch(cand.cover_url);
        const blob = await res.blob();
        const file = new File([blob], 'cover.jpg', { type: 'image/jpeg' });
        setStagedCoverFile(file);
        setCoverPreviewUrl(URL.createObjectURL(file));
        setToastMessage('Cover image imported from candidate');
      } catch (err) {
        console.warn('Could not fetch candidate cover directly, saving preview URL:', err);
      }
    }
  };

  const handleSave = async () => {
    if (!book) return;
    setIsSaving(true);
    setSaveError(null);

    try {
      // 1. Update text metadata
      await api.updateBookMetadata(book.id, {
        title: title.trim() || undefined,
        sort_title: sortTitle.trim() || undefined,
        authors: authors.length > 0 ? authors : undefined,
        author_sort: authorSort.trim() || undefined,
        publisher: publisher.trim() || undefined,
        pubdate: pubdate.trim() || undefined,
        rating: rating > 0 ? rating : undefined,
        tags: tags,
        series_name: seriesName.trim() || undefined,
        series_index: seriesIndex,
        isbn: isbn.trim() || undefined,
        identifiers: identifiers,
        comments: comments.trim() || undefined,
      });

      // 2. Upload staged cover file if changed
      if (stagedCoverFile) {
        await api.uploadBookCover(book.id, stagedCoverFile);
      }

      setToastMessage('Book metadata saved successfully');
      await loadBooks();
      await selectBook(book.id);
      onClose();
    } catch (err: any) {
      setSaveError(err.message || 'Failed to save metadata');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen || !book) return null;

  return (
    <div
      onPaste={handlePaste}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 70,
        background: 'var(--bg-modal, rgba(0, 0, 0, 0.75))',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '980px',
          height: '88vh',
          maxHeight: '880px',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-default)',
          boxShadow: 'var(--shadow-glass)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '12px 20px',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-surface)',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-surface)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <BookOpen size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  Edit Metadata
                </h2>
                <span
                  style={{
                    fontSize: '11px',
                    padding: '1px 6px',
                    borderRadius: 'var(--radius-full)',
                    background: 'var(--bg-surface-elevated)',
                    color: 'var(--text-muted)',
                    fontFamily: 'monospace',
                  }}
                >
                  ID: {book.id}
                </span>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
                In-place Calibre database & OPF metadata editor
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setIsOnlineDrawerOpen(true)}
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '6px 10px', gap: '6px' }}
            >
              <Download size={14} color="var(--accent-primary)" />
              <span>Download Metadata</span>
            </button>
            <button
              onClick={onClose}
              className="btn-icon"
              title="Close (Esc)"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Modal Body: Two Column Split */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Left Column: Cover Art */}
          <div
            style={{
              width: '280px',
              minWidth: '280px',
              maxWidth: '280px',
              borderRight: '1px solid var(--border-default)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              overflowY: 'auto',
              background: 'var(--bg-surface-elevated)',
            }}
          >
            <div
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Cover Art
            </div>

            {/* Drop / Preview Box */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsCoverDragging(true);
              }}
              onDragLeave={() => setIsCoverDragging(false)}
              onDrop={handleCoverDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                width: '100%',
                height: '330px',
                borderRadius: 'var(--radius-md)',
                border: isCoverDragging
                  ? '2px dashed var(--accent-primary)'
                  : '2px dashed var(--border-subtle)',
                background: isCoverDragging ? 'var(--accent-surface)' : 'var(--bg-card)',
                overflow: 'hidden',
                position: 'relative',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 'var(--shadow-sm)',
                flexShrink: 0,
                transition: 'border-color var(--transition-fast)',
              }}
              title="Click, drag & drop, or paste (Ctrl+V) an image"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />

              {coverPreviewUrl ? (
                <>
                  <img
                    src={coverPreviewUrl}
                    alt={title}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain',
                      background: '#090d16',
                      display: 'block',
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: 'rgba(0,0,0,0.5)',
                      opacity: 0,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      color: '#fff',
                      fontSize: '11px',
                      fontWeight: 500,
                      transition: 'opacity var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                    onMouseLeave={(e) => (e.currentTarget.style.opacity = '0')}
                  >
                    <Upload size={20} />
                    <span>Change Cover</span>
                  </div>
                </>
              ) : (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '1rem',
                    textAlign: 'center',
                    color: 'var(--text-muted)',
                    gap: '8px',
                  }}
                >
                  <ImageIcon size={36} strokeWidth={1.5} />
                  <p style={{ fontSize: '11px', margin: 0, lineHeight: 1.4 }}>
                    Drag & drop cover image, paste (Ctrl+V), or click to browse
                  </p>
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="btn btn-secondary"
                style={{ fontSize: '11px', padding: '6px' }}
              >
                <Upload size={12} />
                <span>Browse File</span>
              </button>
              <button
                type="button"
                onClick={() => setIsOnlineDrawerOpen(true)}
                className="btn btn-secondary"
                style={{ fontSize: '11px', padding: '6px' }}
              >
                <Download size={12} />
                <span>Fetch Online</span>
              </button>
            </div>

            <p style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', margin: 0 }}>
              Tip: Copy any image to clipboard and press <strong>Ctrl+V</strong>.
            </p>
          </div>

          {/* Right Column: Metadata Fields */}
          <div
            style={{
              flex: 1,
              minWidth: 0,
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              overflowY: 'auto',
            }}
          >
            {saveError && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#ef4444',
                  fontSize: '12px',
                }}
              >
                {saveError}
              </div>
            )}

            {/* Title & Title Sort */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Title <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    if (!sortTitle || sortTitle === title) {
                      setSortTitle(e.target.value);
                    }
                  }}
                  className="input-text"
                  placeholder="e.g. Dune"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Title Sort
                </label>
                <input
                  type="text"
                  value={sortTitle}
                  onChange={(e) => setSortTitle(e.target.value)}
                  className="input-text"
                  placeholder="e.g. Dune"
                />
              </div>
            </div>

            {/* Authors & Author Sort */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600 }}>Authors</label>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Press Enter or click Add</span>
              </div>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                <input
                  type="text"
                  value={authorInput}
                  onChange={(e) => setAuthorInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddAuthor())}
                  placeholder="Add author name..."
                  className="input-text"
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  onClick={handleAddAuthor}
                  className="btn btn-secondary"
                  style={{ padding: '0 12px' }}
                >
                  <Plus size={14} />
                  <span>Add</span>
                </button>
              </div>

              {authors.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
                  {authors.map((auth, idx) => (
                    <span
                      key={idx}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '12px',
                        color: 'var(--text-primary)',
                      }}
                    >
                      <span>{auth}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveAuthor(idx)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'var(--text-muted)',
                          padding: 0,
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Series & Series Index */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 0.7fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Series Name
                </label>
                <input
                  type="text"
                  value={seriesName}
                  onChange={(e) => setSeriesName(e.target.value)}
                  placeholder="e.g. Dune Chronicles"
                  className="input-text"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Series Index
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={seriesIndex}
                  onChange={(e) => setSeriesIndex(parseFloat(e.target.value) || 1.0)}
                  className="input-text"
                  style={{ fontFamily: 'monospace' }}
                />
              </div>
            </div>

            {/* Publisher, Date & Rating */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 0.8fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Publisher
                </label>
                <input
                  type="text"
                  value={publisher}
                  onChange={(e) => setPublisher(e.target.value)}
                  placeholder="e.g. Chilton Books"
                  className="input-text"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Pub Date / Year
                </label>
                <input
                  type="text"
                  value={pubdate}
                  onChange={(e) => setPubdate(e.target.value)}
                  placeholder="YYYY-MM-DD"
                  className="input-text"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Rating
                </label>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    height: '35px',
                    padding: '0 8px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-default)',
                  }}
                >
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(rating === star ? 0 : star)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '2px',
                        color: star <= rating ? '#eab308' : 'var(--text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                      title={`${star} star${star > 1 ? 's' : ''}`}
                    >
                      <Star size={16} fill={star <= rating ? '#eab308' : 'none'} />
                    </button>
                  ))}
                  {rating > 0 && (
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '4px' }}>
                      ({rating}/5)
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Tags Management */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Tag size={13} color="var(--accent-primary)" />
                  <span>Tags / Subjects</span>
                </label>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Press Enter to add tag</span>
              </div>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  placeholder="e.g. Science Fiction, Classics..."
                  className="input-text"
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="btn btn-secondary"
                  style={{ padding: '0 12px' }}
                >
                  Add Tag
                </button>
              </div>

              {tags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {tags.map((t) => (
                    <span
                      key={t}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-full)',
                        background: 'var(--accent-surface)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '11px',
                        fontWeight: 500,
                        color: 'var(--accent-primary)',
                      }}
                    >
                      <span>{t}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(t)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'var(--accent-primary)',
                          padding: 0,
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <X size={11} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Identifiers & ISBN */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <Hash size={13} color="var(--accent-primary)" />
                <span>Identifiers & ISBN</span>
              </label>

              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr auto', gap: '8px', marginBottom: '6px' }}>
                <input
                  type="text"
                  value={isbn}
                  onChange={(e) => setIsbn(e.target.value)}
                  placeholder="ISBN (10 or 13)..."
                  className="input-text"
                />
                <input
                  type="text"
                  value={newIdType}
                  onChange={(e) => setNewIdType(e.target.value)}
                  placeholder="Type (e.g. goodreads)"
                  className="input-text"
                />
                <input
                  type="text"
                  value={newIdVal}
                  onChange={(e) => setNewIdVal(e.target.value)}
                  placeholder="Value..."
                  className="input-text"
                />
                <button
                  type="button"
                  onClick={handleAddIdentifier}
                  className="btn btn-secondary"
                  style={{ padding: '0 12px' }}
                >
                  + Add
                </button>
              </div>

              {Object.keys(identifiers).length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {Object.entries(identifiers).map(([k, v]) => (
                    <span
                      key={k}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      <strong style={{ textTransform: 'uppercase', color: 'var(--accent-primary)' }}>{k}:</strong> {v}
                      <button
                        type="button"
                        onClick={() => handleRemoveIdentifier(k)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'var(--text-muted)',
                          padding: 0,
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <X size={11} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Description / Comments */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Comments / Description
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={4}
                placeholder="Enter HTML or text summary / synopsis..."
                className="input-text"
                style={{ minHeight: '90px', resize: 'vertical', lineHeight: 1.5 }}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid var(--border-default)',
            background: 'var(--bg-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0,
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Press <kbd style={{ padding: '2px 5px', borderRadius: '3px', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-subtle)', fontFamily: 'monospace' }}>Ctrl+Enter</kbd> to save
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="btn btn-primary"
            >
              {isSaving ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save size={14} />
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Online Metadata Drawer */}
      <OnlineMetadataDrawer
        isOpen={isOnlineDrawerOpen}
        onClose={() => setIsOnlineDrawerOpen(false)}
        bookId={book.id}
        initialTitle={title}
        initialAuthor={authors[0] || ''}
        initialIsbn={isbn}
        onApplyCandidate={handleApplyOnlineCandidate}
      />
    </div>
  );
};
