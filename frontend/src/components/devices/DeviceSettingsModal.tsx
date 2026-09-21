import React, { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';
import type { DeviceCreateRequest, DeviceType, SMTPSettings } from '../../types';

export const DeviceSettingsModal: React.FC = () => {
  const {
    isDeviceSettingsOpen,
    setDeviceSettingsOpen,
    activeLibraryId,
    devices,
    deviceSyncLogs,
    loadDevices,
    loadSyncLogs,
  } = useStore();

  const [activeTab, setActiveTab] = useState<'devices' | 'smtp' | 'logs'>('devices');

  // New device form
  const [isAddingDevice, setIsAddingDevice] = useState(false);
  const [newDeviceName, setNewDeviceName] = useState('');
  const [newDeviceType, setNewDeviceType] = useState<DeviceType>('kindle');
  const [newDeviceAddress, setNewDeviceAddress] = useState('');

  // SMTP form
  const [smtp, setSmtp] = useState<SMTPSettings>({
    host: 'smtp.gmail.com',
    port: 587,
    username: '',
    password: '',
    use_tls: true,
    use_ssl: false,
    sender_email: '',
  });
  const [isTestingSmtp, setIsTestingSmtp] = useState(false);
  const [smtpStatus, setSmtpStatus] = useState<{ text: string; isError: boolean } | null>(null);

  useEffect(() => {
    if (isDeviceSettingsOpen && activeLibraryId) {
      loadDevices();
      loadSyncLogs();
      api.getSmtpSettings().then(setSmtp).catch(console.error);
    }
  }, [isDeviceSettingsOpen, activeLibraryId, loadDevices, loadSyncLogs]);

  if (!isDeviceSettingsOpen || !activeLibraryId) return null;

  const handleCreateDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeviceName.trim()) return;

    try {
      const payload: DeviceCreateRequest = {
        name: newDeviceName.trim(),
        device_type: newDeviceType,
        target_address: newDeviceAddress.trim() || undefined,
      };
      await api.createDevice(activeLibraryId, payload);
      setNewDeviceName('');
      setNewDeviceAddress('');
      setIsAddingDevice(false);
      await loadDevices();
    } catch (err: any) {
      alert(`Failed to add device: ${err.message}`);
    }
  };

  const handleDeleteDevice = async (deviceId: string) => {
    if (!confirm('Are you sure you want to remove this device?')) return;
    try {
      await api.deleteDevice(activeLibraryId, deviceId);
      await loadDevices();
    } catch (err: any) {
      alert(`Failed to delete device: ${err.message}`);
    }
  };

  const handleSaveSmtp = async () => {
    try {
      const updated = await api.updateSmtpSettings(smtp);
      setSmtp(updated);
      setSmtpStatus({ text: 'SMTP configuration saved successfully.', isError: false });
    } catch (err: any) {
      setSmtpStatus({ text: `Failed to save: ${err.message}`, isError: true });
    }
  };

  const handleTestSmtp = async () => {
    setIsTestingSmtp(true);
    setSmtpStatus(null);
    try {
      const res = await api.testSmtpSettings(smtp);
      setSmtpStatus({ text: res.message, isError: !res.success });
    } catch (err: any) {
      setSmtpStatus({ text: `Connection test error: ${err.message}`, isError: true });
    } finally {
      setIsTestingSmtp(false);
    }
  };

  const currentOrigin = window.location.origin;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-neutral-900 border border-neutral-700 rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-800 bg-neutral-950/40">
          <div className="flex items-center gap-2">
            <span className="text-xl">⚙️</span>
            <h3 className="font-semibold text-neutral-100 text-base">E-Reader & Wireless Sync Settings</h3>
          </div>
          <button
            onClick={() => setDeviceSettingsOpen(false)}
            className="text-neutral-400 hover:text-neutral-200 text-lg p-1 rounded hover:bg-neutral-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Tab Bar */}
        <div className="flex border-b border-neutral-800 bg-neutral-950/30">
          <button
            onClick={() => setActiveTab('devices')}
            className={`flex-1 py-2.5 text-xs font-medium border-b-2 transition ${
              activeTab === 'devices'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            📱 Registered Devices ({devices.length})
          </button>
          <button
            onClick={() => setActiveTab('smtp')}
            className={`flex-1 py-2.5 text-xs font-medium border-b-2 transition ${
              activeTab === 'smtp'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            ✉️ Kindle SMTP Settings
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`flex-1 py-2.5 text-xs font-medium border-b-2 transition ${
              activeTab === 'logs'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            📋 Sync Logs ({deviceSyncLogs.length})
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4 text-sm">
          {activeTab === 'devices' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-xs text-neutral-400">
                  Manage your Kindles, Kobo e-readers, KOReader devices, and USB destinations.
                </p>
                <button
                  onClick={() => setIsAddingDevice(!isAddingDevice)}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition"
                >
                  {isAddingDevice ? 'Cancel' : '+ Add Device'}
                </button>
              </div>

              {isAddingDevice && (
                <form
                  onSubmit={handleCreateDevice}
                  className="p-4 bg-neutral-950/40 border border-neutral-800 rounded-lg space-y-3"
                >
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-medium text-neutral-400 mb-1">
                        Device Name:
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Bedroom Kindle"
                        value={newDeviceName}
                        onChange={(e) => setNewDeviceName(e.target.value)}
                        required
                        className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 focus:ring-1 focus:ring-indigo-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-neutral-400 mb-1">
                        Device Type:
                      </label>
                      <select
                        value={newDeviceType}
                        onChange={(e) => setNewDeviceType(e.target.value as DeviceType)}
                        className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 focus:ring-1 focus:ring-indigo-500 outline-none"
                      >
                        <option value="kindle">Kindle (Email Delivery)</option>
                        <option value="kobo">Kobo (Wireless Store Sync)</option>
                        <option value="koreader">KOReader (Kosync Protocol)</option>
                        <option value="usb">USB / Local Directory</option>
                      </select>
                    </div>
                  </div>

                  {newDeviceType === 'kindle' && (
                    <div>
                      <label className="block text-[11px] font-medium text-neutral-400 mb-1">
                        Kindle Email Address:
                      </label>
                      <input
                        type="email"
                        placeholder="e.g. user@kindle.com"
                        value={newDeviceAddress}
                        onChange={(e) => setNewDeviceAddress(e.target.value)}
                        required
                        className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 focus:ring-1 focus:ring-indigo-500 outline-none"
                      />
                    </div>
                  )}

                  <div className="flex justify-end pt-1">
                    <button
                      type="submit"
                      className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded transition"
                    >
                      Save Device
                    </button>
                  </div>
                </form>
              )}

              {/* Device List */}
              <div className="space-y-2.5">
                {devices.map((d) => (
                  <div
                    key={d.id}
                    className="p-3.5 bg-neutral-950/25 border border-neutral-800 rounded-lg flex items-start justify-between gap-3"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-neutral-200 text-xs">{d.name}</span>
                        <span className="px-2 py-0.5 text-[10px] rounded uppercase font-medium bg-neutral-800 text-neutral-400">
                          {d.device_type}
                        </span>
                      </div>
                      {d.target_address && (
                        <p className="text-xs text-neutral-400 truncate">{d.target_address}</p>
                      )}
                      {d.device_type === 'kobo' && d.auth_token && (
                        <div className="mt-2 p-2 bg-neutral-900 border border-neutral-800 rounded text-[11px] font-mono text-neutral-300">
                          <p className="text-neutral-400 text-[10px] font-sans mb-1">Kobo Sync Endpoint:</p>
                          <span className="select-all text-indigo-400">{`${currentOrigin}/api/sync/kobo/${d.auth_token}`}</span>
                        </div>
                      )}
                      {d.device_type === 'koreader' && (
                        <div className="mt-2 p-2 bg-neutral-900 border border-neutral-800 rounded text-[11px] font-mono text-neutral-300">
                          <p className="text-neutral-400 text-[10px] font-sans mb-1">Kosync Custom Server URL:</p>
                          <span className="select-all text-indigo-400">{`${currentOrigin}/api/sync/koreader`}</span>
                        </div>
                      )}
                      {d.last_sync_at && (
                        <p className="text-[10px] text-neutral-500">
                          Last sync: {new Date(d.last_sync_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteDevice(d.id)}
                      className="text-neutral-500 hover:text-rose-400 p-1 rounded transition text-xs"
                      title="Delete Device"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
                {devices.length === 0 && (
                  <div className="p-8 text-center text-neutral-500 text-xs border border-dashed border-neutral-800 rounded-lg">
                    No devices registered yet. Click &ldquo;+ Add Device&rdquo; above to get started.
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'smtp' && (
            <div className="space-y-4">
              <p className="text-xs text-neutral-400">
                Configure your outgoing mail server to send books to Amazon Kindle devices wirelessly.
              </p>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-neutral-300 mb-1">
                    SMTP Host:
                  </label>
                  <input
                    type="text"
                    value={smtp.host}
                    onChange={(e) => setSmtp({ ...smtp, host: e.target.value })}
                    className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1">Port:</label>
                  <input
                    type="number"
                    value={smtp.port}
                    onChange={(e) => setSmtp({ ...smtp, port: parseInt(e.target.value) || 587 })}
                    className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1">
                    Username:
                  </label>
                  <input
                    type="text"
                    value={smtp.username}
                    onChange={(e) => setSmtp({ ...smtp, username: e.target.value })}
                    className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1">
                    Password / App Password:
                  </label>
                  <input
                    type="password"
                    placeholder="Leave unchanged or enter new"
                    value={smtp.password || ''}
                    onChange={(e) => setSmtp({ ...smtp, password: e.target.value })}
                    className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">
                  Sender Email Address:
                </label>
                <input
                  type="email"
                  placeholder="Must match your Amazon Approved Sender list"
                  value={smtp.sender_email}
                  onChange={(e) => setSmtp({ ...smtp, sender_email: e.target.value })}
                  className="w-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-xs text-neutral-200 outline-none"
                />
              </div>

              <div className="flex items-center gap-6 pt-1">
                <label className="flex items-center gap-2 text-xs text-neutral-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={smtp.use_tls}
                    onChange={(e) => setSmtp({ ...smtp, use_tls: e.target.checked })}
                    className="rounded border-neutral-700 text-indigo-600 focus:ring-indigo-500"
                  />
                  Use STARTTLS (Port 587)
                </label>
                <label className="flex items-center gap-2 text-xs text-neutral-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={smtp.use_ssl}
                    onChange={(e) => setSmtp({ ...smtp, use_ssl: e.target.checked })}
                    className="rounded border-neutral-700 text-indigo-600 focus:ring-indigo-500"
                  />
                  Use SSL (Port 465)
                </label>
              </div>

              {smtpStatus && (
                <div
                  className={`p-3 rounded-lg text-xs ${
                    smtpStatus.isError
                      ? 'bg-rose-950/50 border border-rose-800 text-rose-300'
                      : 'bg-emerald-950/50 border border-emerald-800 text-emerald-300'
                  }`}
                >
                  {smtpStatus.text}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleTestSmtp}
                  disabled={isTestingSmtp}
                  className="px-3.5 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-medium rounded-lg transition"
                >
                  {isTestingSmtp ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  type="button"
                  onClick={handleSaveSmtp}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition"
                >
                  Save Settings
                </button>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-neutral-400">History of e-reader deliveries and exports.</p>
                <button
                  onClick={() => loadSyncLogs()}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition"
                >
                  🔄 Refresh
                </button>
              </div>

              <div className="border border-neutral-800 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-neutral-950/60 text-neutral-400 border-b border-neutral-800 font-medium">
                    <tr>
                      <th className="p-2.5">Date</th>
                      <th className="p-2.5">Book</th>
                      <th className="p-2.5">Type</th>
                      <th className="p-2.5">Format</th>
                      <th className="p-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800/60 text-neutral-300">
                    {deviceSyncLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-neutral-800/30">
                        <td className="p-2.5 text-[11px] text-neutral-500 whitespace-nowrap">
                          {new Date(log.created_at).toLocaleDateString()}{' '}
                          {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className="p-2.5 font-medium text-neutral-200 truncate max-w-[150px]">
                          {log.book_title}
                        </td>
                        <td className="p-2.5 uppercase text-[10px] text-neutral-400">{log.device_type}</td>
                        <td className="p-2.5 font-mono text-[10px]">{log.format_sent}</td>
                        <td className="p-2.5">
                          <span
                            className={`px-2 py-0.5 text-[10px] rounded font-medium ${
                              log.status === 'completed'
                                ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                                : 'bg-rose-950/60 text-rose-400 border border-rose-800'
                            }`}
                          >
                            {log.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {deviceSyncLogs.length === 0 && (
                      <tr>
                        <td colSpan={5} className="p-6 text-center text-neutral-500 text-xs">
                          No sync logs recorded yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
