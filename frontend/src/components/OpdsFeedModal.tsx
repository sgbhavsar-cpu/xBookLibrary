import React, { useState } from 'react';
import {
  Check,
  Copy,
  ExternalLink,
  HelpCircle,
  Radio,
  Smartphone,
  Tablet,
  Wifi,
  X,
} from 'lucide-react';

interface OpdsFeedModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OpdsFeedModal: React.FC<OpdsFeedModalProps> = ({ isOpen, onClose }) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'koreader' | 'moon' | 'general'>('koreader');

  if (!isOpen) return null;

  // Determine host and base URL
  const host = window.location.hostname || '127.0.0.1';
  // Use port 8000 (backend direct) or current port if proxying
  const backendBase = `${window.location.protocol}//${host}:8000`;
  const opds12Url = `${backendBase}/opds`;
  const opds20Url = `${backendBase}/api/opds/v2.0`;
  const opensearchUrl = `${backendBase}/opds/opensearch.xml`;

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => {
      setCopiedKey(null);
    }, 2000);
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
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '640px',
          maxHeight: '90vh',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-glass)',
          border: '1px solid var(--border-default)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, #10b981, #059669)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
              }}
            >
              <Wifi size={17} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: 700, margin: 0 }}>
                  OPDS Wireless Catalog Feed
                </h3>
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px',
                    padding: '2px 8px',
                    borderRadius: '10px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#10b981',
                    fontWeight: 600,
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: '#10b981',
                      display: 'inline-block',
                    }}
                  />
                  Live on LAN
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0, marginTop: '2px' }}>
                Sync and download books directly on KOReader, Moon+ Reader, Kindle, or Kobo.
              </p>
            </div>
          </div>
          <button className="btn-icon" onClick={onClose} title="Close">
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div
          style={{
            padding: '1.25rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
          }}
        >
          {/* Feed URL 1: OPDS 1.2 Atom XML */}
          <div
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Radio size={14} color="var(--accent-primary)" />
                <span style={{ fontSize: '13px', fontWeight: 600 }}>
                  OPDS 1.2 Feed (Atom XML)
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 500,
                    padding: '1px 6px',
                    borderRadius: '4px',
                    background: 'var(--accent-surface)',
                    color: 'var(--accent-primary)',
                  }}
                >
                  Recommended for KOReader & Moon+
                </span>
              </div>
              <a
                href={opds12Url}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                  textDecoration: 'none',
                }}
              >
                Inspect <ExternalLink size={11} />
              </a>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                gap: '8px',
              }}
            >
              <input
                type="text"
                readOnly
                value={opds12Url}
                style={{
                  flex: 1,
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  outline: 'none',
                }}
              />
              <button
                className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
                onClick={() => copyToClipboard(opds12Url, 'opds12')}
              >
                {copiedKey === 'opds12' ? (
                  <>
                    <Check size={12} color="#10b981" />
                    <span style={{ color: '#10b981' }}>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy URL</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Feed URL 2: OPDS 2.0 Readium JSON */}
          <div
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600 }}>
                  OPDS 2.0 Catalog (Readium JSON)
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 500,
                    padding: '1px 6px',
                    borderRadius: '4px',
                    background: 'var(--bg-card)',
                    color: 'var(--text-muted)',
                  }}
                >
                  Modern E-Readers
                </span>
              </div>
              <a
                href={opds20Url}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                  textDecoration: 'none',
                }}
              >
                Inspect <ExternalLink size={11} />
              </a>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                gap: '8px',
              }}
            >
              <input
                type="text"
                readOnly
                value={opds20Url}
                style={{
                  flex: 1,
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  outline: 'none',
                }}
              />
              <button
                className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
                onClick={() => copyToClipboard(opds20Url, 'opds20')}
              >
                {copiedKey === 'opds20' ? (
                  <>
                    <Check size={12} color="#10b981" />
                    <span style={{ color: '#10b981' }}>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy URL</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quick Setup Instructions */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <HelpCircle size={15} color="var(--accent-primary)" />
                Quick E-Reader Setup Guides
              </span>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  style={{
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-default)',
                    background: activeTab === 'koreader' ? 'var(--accent-primary)' : 'transparent',
                    color: activeTab === 'koreader' ? '#fff' : 'var(--text-secondary)',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveTab('koreader')}
                >
                  KOReader
                </button>
                <button
                  style={{
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-default)',
                    background: activeTab === 'moon' ? 'var(--accent-primary)' : 'transparent',
                    color: activeTab === 'moon' ? '#fff' : 'var(--text-secondary)',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveTab('moon')}
                >
                  Moon+ Reader
                </button>
                <button
                  style={{
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-default)',
                    background: activeTab === 'general' ? 'var(--accent-primary)' : 'transparent',
                    color: activeTab === 'general' ? '#fff' : 'var(--text-secondary)',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveTab('general')}
                >
                  Other Apps
                </button>
              </div>
            </div>

            <div
              style={{
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 16px',
                fontSize: '12px',
                lineHeight: 1.6,
                color: 'var(--text-secondary)',
              }}
            >
              {activeTab === 'koreader' && (
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Tablet size={14} color="var(--accent-primary)" />
                    Setting up KOReader (Kindle, Kobo, Android, Tolino)
                  </div>
                  <ol style={{ margin: 0, paddingLeft: '1.25rem' }}>
                    <li>Ensure your e-reader is on the same local Wi-Fi network as this computer.</li>
                    <li>In KOReader, open the top menu bar and tap the <strong>magnifying glass / search</strong> or <strong>Library</strong> icon.</li>
                    <li>Select <strong>OPDS catalog</strong> ➔ <strong>Add new catalog</strong>.</li>
                    <li>Set <strong>Catalog name</strong> to <code>xBookLibrary</code>.</li>
                    <li>Set <strong>Catalog URL</strong> to <code>{opds12Url}</code>.</li>
                    <li>Tap <strong>Save</strong>. You can now browse Recent, Authors, Genres, and download books instantly!</li>
                  </ol>
                </div>
              )}

              {activeTab === 'moon' && (
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Smartphone size={14} color="var(--accent-primary)" />
                    Setting up Moon+ Reader (Android Phone / Tablet)
                  </div>
                  <ol style={{ margin: 0, paddingLeft: '1.25rem' }}>
                    <li>Open Moon+ Reader on Android connected to your home Wi-Fi.</li>
                    <li>Open the side drawer menu and tap <strong>Net Library</strong>.</li>
                    <li>Tap the <strong>+ (Add new catalog)</strong> button in the top right.</li>
                    <li>Enter <strong>Title</strong>: <code>xBookLibrary</code>.</li>
                    <li>Enter <strong>URL</strong>: <code>{opds12Url}</code>.</li>
                    <li>Tap <strong>OK</strong> to connect and access your entire catalog with covers and metadata.</li>
                  </ol>
                </div>
              )}

              {activeTab === 'general' && (
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    Compatible OPDS Applications
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                    <li><strong>iOS:</strong> Marvin, KyBook 3, TiReader (enter <code>{opds12Url}</code>).</li>
                    <li><strong>Windows / Linux / macOS:</strong> Foliate, Thorium Reader, Calibre.</li>
                    <li><strong>Search Integration:</strong> KOReader and Moon+ automatically query <code>{opensearchUrl}</code> for full-text catalog search.</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '10px 1.25rem',
            borderTop: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-surface-elevated)',
          }}
        >
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Authentication: Open LAN (Default). Optional HTTP Basic Auth in Settings.
          </span>
          <button className="btn btn-secondary" onClick={onClose} style={{ padding: '6px 16px', fontSize: '12px' }}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
