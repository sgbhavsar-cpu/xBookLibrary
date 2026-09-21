import React, { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';
import type { DeviceSyncLog } from '../../types';

export const SendToDeviceModal: React.FC = () => {
  const {
    isSendToDeviceOpen,
    setSendToDeviceOpen,
    selectedBook,
    activeLibraryId,
    devices,
    loadDevices,
    loadSyncLogs,
  } = useStore();

  const [mode, setMode] = useState<'kindle' | 'export'>('kindle');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [customEmail, setCustomEmail] = useState<string>('');
  const [preferredFormat, setPreferredFormat] = useState<string>('EPUB');
  const [targetDirectory, setTargetDirectory] = useState<string>('');
  const [isSending, setIsSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError: boolean } | null>(null);

  useEffect(() => {
    if (isSendToDeviceOpen && activeLibraryId) {
      loadDevices();
      loadSyncLogs();
      setStatusMessage(null);
    }
  }, [isSendToDeviceOpen, activeLibraryId, loadDevices, loadSyncLogs]);

  if (!isSendToDeviceOpen || !selectedBook || !activeLibraryId) return null;

  const kindleDevices = devices.filter((d) => d.device_type === 'kindle');

  const handleSendKindle = async () => {
    setIsSending(true);
    setStatusMessage(null);
    try {
      const res: DeviceSyncLog = await api.sendToDevice(activeLibraryId, selectedBook.id, {
        device_id: selectedDeviceId || undefined,
        custom_recipient: selectedDeviceId ? undefined : customEmail,
        preferred_format: preferredFormat,
      });

      if (res.status === 'completed') {
        setStatusMessage({
          text: `Successfully dispatched "${selectedBook.title}" as ${res.format_sent} to e-reader!`,
          isError: false,
        });
        loadSyncLogs();
      } else {
        setStatusMessage({
          text: `Delivery failed: ${res.error_message || 'Unknown SMTP error'}`,
          isError: true,
        });
      }
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Dispatch failed', isError: true });
    } finally {
      setIsSending(false);
    }
  };

  const handleExport = async () => {
    if (!targetDirectory.trim()) {
      setStatusMessage({ text: 'Please enter a destination directory.', isError: true });
      return;
    }
    setIsSending(true);
    setStatusMessage(null);
    try {
      const res = await api.exportToDirectory(activeLibraryId, selectedBook.id, {
        target_directory: targetDirectory.trim(),
        format: preferredFormat,
      });
      setStatusMessage({
        text: `Exported to: ${res.exported_path}`,
        isError: false,
      });
      loadSyncLogs();
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Export failed', isError: true });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-neutral-900 border border-neutral-700 rounded-xl max-w-lg w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-800 bg-neutral-950/40">
          <div className="flex items-center gap-2">
            <span className="text-xl">📡</span>
            <h3 className="font-semibold text-neutral-100 text-base">Send to E-Reader Device</h3>
          </div>
          <button
            onClick={() => setSendToDeviceOpen(false)}
            className="text-neutral-400 hover:text-neutral-200 text-lg p-1 rounded hover:bg-neutral-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Book Preview */}
        <div className="p-4 bg-neutral-950/20 border-b border-neutral-800/80 flex items-center gap-3">
          <div className="w-10 h-14 bg-neutral-800 rounded flex-shrink-0 flex items-center justify-center text-xs text-neutral-500 overflow-hidden">
            {selectedBook.has_cover ? (
              <img
                src={`/api/books/${selectedBook.id}/cover`}
                alt=""
                className="w-full h-full object-cover"
              />
            ) : (
              '📖'
            )}
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-neutral-100 truncate">{selectedBook.title}</h4>
            <p className="text-xs text-neutral-400 truncate">
              {selectedBook.authors?.join(', ') || 'Unknown Author'}
            </p>
          </div>
        </div>

        {/* Tab Selector */}
        <div className="flex border-b border-neutral-800 bg-neutral-950/30">
          <button
            onClick={() => {
              setMode('kindle');
              setStatusMessage(null);
            }}
            className={`flex-1 py-2.5 text-xs font-medium border-b-2 transition ${
              mode === 'kindle'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            ✉️ Send to Kindle (SMTP)
          </button>
          <button
            onClick={() => {
              setMode('export');
              setStatusMessage(null);
            }}
            className={`flex-1 py-2.5 text-xs font-medium border-b-2 transition ${
              mode === 'export'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            💾 Export to USB / Directory
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-sm flex-1">
          {mode === 'kindle' ? (
            <div className="space-y-4">
              {kindleDevices.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                    Saved Kindle Devices:
                  </label>
                  <select
                    value={selectedDeviceId}
                    onChange={(e) => {
                      setSelectedDeviceId(e.target.value);
                      if (e.target.value) setCustomEmail('');
                    }}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-neutral-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                  >
                    <option value="">-- Choose registered Kindle or enter email below --</option>
                    {kindleDevices.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.target_address || 'No address'})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {!selectedDeviceId && (
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                    Kindle Email Address:
                  </label>
                  <input
                    type="email"
                    placeholder="e.g. username@kindle.com"
                    value={customEmail}
                    onChange={(e) => setCustomEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-neutral-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                  />
                  <p className="text-[11px] text-neutral-500 mt-1">
                    Make sure your sender address is whitelisted in your Amazon Approved Personal Document E-mail List.
                  </p>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Preferred Format:
                </label>
                <select
                  value={preferredFormat}
                  onChange={(e) => setPreferredFormat(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-neutral-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                >
                  <option value="EPUB">EPUB (Amazon Recommended)</option>
                  <option value="PDF">PDF</option>
                </select>
                <p className="text-[11px] text-indigo-400/90 mt-1.5 bg-indigo-950/40 border border-indigo-900/50 p-2 rounded">
                  ✨ <strong>Smart Conversion:</strong> If this book only exists in MOBI or DOCX format, xBookLibrary will automatically convert it to EPUB on the fly before delivery.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Target Directory or Mounted USB Drive:
                </label>
                <input
                  type="text"
                  placeholder="e.g. E:\documents or /Volumes/KOBOeReader"
                  value={targetDirectory}
                  onChange={(e) => setTargetDirectory(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-neutral-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                />
                <p className="text-[11px] text-neutral-500 mt-1">
                  Books will be exported in Calibre folder structure: <code>{'{Author}/{Title} ({Year})/{Title} - {Author}.{ext}'}</code>.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Format:
                </label>
                <select
                  value={preferredFormat}
                  onChange={(e) => setPreferredFormat(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-neutral-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                >
                  {selectedBook.formats?.map((f) => (
                    <option key={f.format} value={f.format}>
                      {f.format} ({(f.uncompressed_size / 1024).toFixed(0)} KB)
                    </option>
                  ))}
                  {(!selectedBook.formats || selectedBook.formats.length === 0) && (
                    <option value="EPUB">EPUB</option>
                  )}
                </select>
              </div>
            </div>
          )}

          {statusMessage && (
            <div
              className={`p-3 rounded-lg text-xs ${
                statusMessage.isError
                  ? 'bg-rose-950/50 border border-rose-800 text-rose-300'
                  : 'bg-emerald-950/50 border border-emerald-800 text-emerald-300'
              }`}
            >
              {statusMessage.text}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-neutral-800 bg-neutral-950/40">
          <button
            onClick={() => setSendToDeviceOpen(false)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition"
          >
            Close
          </button>
          {mode === 'kindle' ? (
            <button
              onClick={handleSendKindle}
              disabled={isSending || (!selectedDeviceId && !customEmail)}
              className="px-4 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition flex items-center gap-1.5"
            >
              {isSending ? 'Sending...' : 'Send to Kindle 🚀'}
            </button>
          ) : (
            <button
              onClick={handleExport}
              disabled={isSending || !targetDirectory.trim()}
              className="px-4 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition flex items-center gap-1.5"
            >
              {isSending ? 'Exporting...' : 'Export Book 💾'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
