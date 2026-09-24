import React, { useEffect, useState } from 'react';
import {
  Bot,
  Brain,
  CheckCircle2,
  Cpu,
  Eye,
  EyeOff,
  FolderInput,
  FolderSync,
  Globe,
  Link,
  RefreshCw,
  Server,
  Settings,
  Sliders,
  Sparkles,
  Wifi,
  X,
  XCircle,
} from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';
import type { UserPreferences } from '../../types';

export const PreferencesModal: React.FC = () => {
  const {
    isPreferencesOpen,
    setPreferencesOpen,
    userPreferences,
    loadPreferences,
    savePreferences,
    loadBooks,
    setToastMessage,
  } = useStore();

  const [activeTab, setActiveTab] = useState<'ai' | 'drop_folder' | 'sharing' | 'defaults'>('ai');

  // Local form state
  const [pref, setPref] = useState<UserPreferences>({
    theme: 'dark',
    default_page_size: 50,
    default_format: 'EPUB',
    view_mode: 'grid',
    active_ai_provider: 'gemini',
    gemini_api_key: '',
    openai_api_key: '',
    ollama_endpoint: 'http://localhost:11434',
    ollama_model: 'llama3',
    embedding_model: 'all-MiniLM-L6-v2',
    auto_import_folder: '',
    auto_import_enabled: false,
    auto_import_action: 'merge',
    delete_source_after_import: true,
    auto_download_metadata: false,
    auto_index_rag: false,
    auto_generate_summary: false,
    opds_enabled: true,
    opds_port: 8000,
  });

  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showOpenAIKey, setShowOpenAIKey] = useState(false);

  // Testing states
  const [isTestingAI, setIsTestingAI] = useState(false);
  const [aiTestResult, setAiTestResult] = useState<{
    success: boolean;
    message: string;
    models?: string[];
  } | null>(null);

  const [isScanningDrop, setIsScanningDrop] = useState(false);
  const [dropScanResult, setDropScanResult] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isPreferencesOpen) {
      loadPreferences();
      setAiTestResult(null);
      setDropScanResult(null);
    }
  }, [isPreferencesOpen, loadPreferences]);

  useEffect(() => {
    if (userPreferences) {
      setPref({
        ...userPreferences,
        gemini_api_key: userPreferences.gemini_api_key || '',
        openai_api_key: userPreferences.openai_api_key || '',
        ollama_endpoint: userPreferences.ollama_endpoint || 'http://localhost:11434',
        ollama_model: userPreferences.ollama_model || 'llama3',
        embedding_model: userPreferences.embedding_model || 'all-MiniLM-L6-v2',
        auto_import_folder: userPreferences.auto_import_folder || '',
        delete_source_after_import: userPreferences.delete_source_after_import ?? true,
        auto_download_metadata: userPreferences.auto_download_metadata ?? false,
        auto_index_rag: userPreferences.auto_index_rag ?? false,
        auto_generate_summary: userPreferences.auto_generate_summary ?? false,
      });
    }
  }, [userPreferences]);

  if (!isPreferencesOpen) return null;

  const handleTestAI = async () => {
    setIsTestingAI(true);
    setAiTestResult(null);
    try {
      const res = await api.testAIConnection({
        provider: pref.active_ai_provider,
        gemini_api_key: pref.gemini_api_key,
        openai_api_key: pref.openai_api_key,
        ollama_endpoint: pref.ollama_endpoint,
        ollama_model: pref.ollama_model,
      });
      setAiTestResult({
        success: res.success,
        message: res.message,
        models: res.available_models,
      });
    } catch (err: any) {
      setAiTestResult({
        success: false,
        message: `Connection failed: ${err.message}`,
      });
    } finally {
      setIsTestingAI(false);
    }
  };

  const handleScanDropFolder = async () => {
    setIsScanningDrop(true);
    setDropScanResult(null);
    try {
      const res = await api.scanDropFolder();
      setDropScanResult(res.message);
      setToastMessage(res.message);
      await loadBooks();
    } catch (err: any) {
      setDropScanResult(`Scan error: ${err.message}`);
    } finally {
      setIsScanningDrop(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await savePreferences(pref);
      setPreferencesOpen(false);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <div
        style={{
          width: '840px',
          maxWidth: '96vw',
          height: '680px',
          maxHeight: '92vh',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1rem 1.25rem',
            borderBottom: '1px solid var(--border-default)',
            background: 'var(--bg-surface-elevated)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--accent-surface)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-primary)',
              }}
            >
              <Settings size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                Preferences &amp; Configuration
              </h2>
              <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', margin: 0 }}>
                Calibre system options, AI service endpoints, auto-import folders, and network sharing
              </p>
            </div>
          </div>

          <button
            onClick={() => setPreferencesOpen(false)}
            className="btn btn-ghost"
            style={{ padding: '6px' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Body with Sidebar Tabs */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Tabs Nav */}
          <div
            style={{
              width: '200px',
              borderRight: '1px solid var(--border-default)',
              background: 'var(--bg-surface-elevated)',
              padding: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <button
              onClick={() => setActiveTab('ai')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'ai' ? 'var(--accent-surface)' : 'transparent',
                color: activeTab === 'ai' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'ai' ? 600 : 400,
                fontSize: '12.5px',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <Bot size={15} />
              <span>AI &amp; LLM Models</span>
            </button>

            <button
              onClick={() => setActiveTab('drop_folder')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'drop_folder' ? 'var(--accent-surface)' : 'transparent',
                color: activeTab === 'drop_folder' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'drop_folder' ? 600 : 400,
                fontSize: '12.5px',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <FolderInput size={15} />
              <span>Drop Folder / Import</span>
            </button>

            <button
              onClick={() => setActiveTab('sharing')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'sharing' ? 'var(--accent-surface)' : 'transparent',
                color: activeTab === 'sharing' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'sharing' ? 600 : 400,
                fontSize: '12.5px',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <Globe size={15} />
              <span>Sharing &amp; OPDS</span>
            </button>

            <button
              onClick={() => setActiveTab('defaults')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: activeTab === 'defaults' ? 'var(--accent-surface)' : 'transparent',
                color: activeTab === 'defaults' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'defaults' ? 600 : 400,
                fontSize: '12.5px',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <Sliders size={15} />
              <span>Defaults &amp; UI</span>
            </button>
          </div>

          {/* Tab Content Area */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1.25rem 1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
            }}
          >
            {/* TAB 1: AI & LLM Services */}
            {activeTab === 'ai' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
                    AI &amp; Large Language Model Configuration
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                    Powers RAG semantic search, chapter summaries, multi-book synthesis, and AI metadata extraction.
                  </p>
                </div>

                {/* Provider Selector Cards */}
                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                    Active AI Engine
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                    {[
                      {
                        id: 'gemini',
                        title: 'Google Gemini',
                        subtitle: 'Gemini 1.5 Flash / Pro',
                        icon: <Sparkles size={16} color="var(--accent-primary)" />,
                      },
                      {
                        id: 'openai',
                        title: 'OpenAI',
                        subtitle: 'GPT-4o / GPT-4o-mini',
                        icon: <Brain size={16} color="#10b981" />,
                      },
                      {
                        id: 'ollama',
                        title: 'Ollama (Local LLM)',
                        subtitle: 'Self-hosted & offline',
                        icon: <Cpu size={16} color="#f59e0b" />,
                      },
                    ].map((p) => {
                      const active = pref.active_ai_provider === p.id;
                      return (
                        <div
                          key={p.id}
                          onClick={() => setPref({ ...pref, active_ai_provider: p.id as any })}
                          style={{
                            padding: '10px 12px',
                            borderRadius: 'var(--radius-md)',
                            border: active ? '2px solid var(--accent-primary)' : '1px solid var(--border-default)',
                            background: active ? 'var(--accent-surface)' : 'var(--bg-card)',
                            cursor: 'pointer',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '4px',
                            transition: 'all var(--transition-fast)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            {p.icon}
                            {active && <CheckCircle2 size={14} color="var(--accent-primary)" />}
                          </div>
                          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                            {p.title}
                          </span>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            {p.subtitle}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Gemini Settings */}
                {pref.active_ai_provider === 'gemini' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      Google Gemini API Key
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showGeminiKey ? 'text' : 'password'}
                        value={pref.gemini_api_key}
                        onChange={(e) => setPref({ ...pref, gemini_api_key: e.target.value })}
                        placeholder="AIzaSy..."
                        className="input"
                        style={{ width: '100%', paddingRight: '36px', fontFamily: 'monospace', fontSize: '12px' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowGeminiKey(!showGeminiKey)}
                        style={{
                          position: 'absolute',
                          right: '8px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'var(--text-muted)',
                        }}
                      >
                        {showGeminiKey ? <EyeOff size={15} /> : <Eye size={15} />}
                      </button>
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Get your free API key at <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)' }}>Google AI Studio</a>.
                    </span>
                  </div>
                )}

                {/* OpenAI Settings */}
                {pref.active_ai_provider === 'openai' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      OpenAI API Key
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showOpenAIKey ? 'text' : 'password'}
                        value={pref.openai_api_key}
                        onChange={(e) => setPref({ ...pref, openai_api_key: e.target.value })}
                        placeholder="sk-proj-..."
                        className="input"
                        style={{ width: '100%', paddingRight: '36px', fontFamily: 'monospace', fontSize: '12px' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowOpenAIKey(!showOpenAIKey)}
                        style={{
                          position: 'absolute',
                          right: '8px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'var(--text-muted)',
                        }}
                      >
                        {showOpenAIKey ? <EyeOff size={15} /> : <Eye size={15} />}
                      </button>
                    </div>
                  </div>
                )}

                {/* Ollama Settings */}
                {pref.active_ai_provider === 'ollama' && (
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        Ollama Base Endpoint
                      </label>
                      <input
                        type="text"
                        value={pref.ollama_endpoint}
                        onChange={(e) => setPref({ ...pref, ollama_endpoint: e.target.value })}
                        placeholder="http://localhost:11434"
                        className="input"
                        style={{ fontSize: '12px' }}
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        Model Name
                      </label>
                      <input
                        type="text"
                        value={pref.ollama_model}
                        onChange={(e) => setPref({ ...pref, ollama_model: e.target.value })}
                        placeholder="llama3 / mistral"
                        className="input"
                        style={{ fontSize: '12px' }}
                      />
                    </div>
                  </div>
                )}

                {/* Test Connection Button & Result */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <button
                    onClick={handleTestAI}
                    disabled={isTestingAI}
                    className="btn btn-secondary"
                    style={{ fontSize: '12px', gap: '6px' }}
                  >
                    <RefreshCw size={13} className={isTestingAI ? 'animate-spin' : ''} />
                    <span>{isTestingAI ? 'Testing Connection...' : 'Test AI Connection'}</span>
                  </button>

                  {aiTestResult && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '12px',
                        color: aiTestResult.success ? '#10b981' : '#ef4444',
                      }}
                    >
                      {aiTestResult.success ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
                      <span>{aiTestResult.message}</span>
                    </div>
                  )}
                </div>

                {/* Available models preview */}
                {aiTestResult?.models && aiTestResult.models.length > 0 && (
                  <div style={{ padding: '8px 10px', background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                      Detected Models:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {aiTestResult.models.map((m) => (
                        <span key={m} style={{ fontSize: '10.5px', padding: '1px 6px', background: 'var(--bg-surface-elevated)', borderRadius: '3px' }}>
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Drop Folder / Auto-Import */}
            {activeTab === 'drop_folder' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
                    Auto-Import Directory &amp; Drop Folder
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                    Calibre-compatible automatic adding: drop ebook files into this folder to automatically ingest and catalog them.
                  </p>
                </div>

                {/* Folder Path */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Intake / Drop Folder Path
                  </label>
                  <input
                    type="text"
                    value={pref.auto_import_folder}
                    onChange={(e) => setPref({ ...pref, auto_import_folder: e.target.value })}
                    placeholder="e.g. C:\Users\YourName\Downloads\Books Intake"
                    className="input"
                    style={{ fontSize: '12.5px', fontFamily: 'monospace' }}
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Supports EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ, and MP3/M4B audiobooks.
                  </span>
                </div>

                {/* Watcher Toggle */}
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={pref.auto_import_enabled}
                    onChange={(e) => setPref({ ...pref, auto_import_enabled: e.target.checked })}
                    style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
                  />
                  <div>
                    <span style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Enable Background File System Watcher
                    </span>
                    <span style={{ fontSize: '11.5px', color: 'var(--text-muted)', display: 'block' }}>
                      Continuously monitors intake folder in real time (built-in; no external Windows services required).
                    </span>
                  </div>
                </label>

                {/* Remove Source File After Ingestion Toggle */}
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={pref.delete_source_after_import ?? true}
                    onChange={(e) => setPref({ ...pref, delete_source_after_import: e.target.checked })}
                    style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
                  />
                  <div>
                    <span style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Remove Source Files From Drop Folder After Successful Import
                    </span>
                    <span style={{ fontSize: '11.5px', color: 'var(--text-muted)', display: 'block' }}>
                      Deletes imported books from the intake directory once safely stored in the library. If import fails, files are kept.
                    </span>
                  </div>
                </label>

                {/* Duplicate Strategy */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Duplicate Handling Action
                  </label>
                  <select
                    value={pref.auto_import_action}
                    onChange={(e) => setPref({ ...pref, auto_import_action: e.target.value as any })}
                    className="select"
                    style={{ width: '100%', fontSize: '12.5px' }}
                  >
                    <option value="merge">Merge into existing book (Attach new format)</option>
                    <option value="skip">Skip if duplicate is detected</option>
                    <option value="create_new">Always create a new book entry</option>
                  </select>
                </div>

                {/* Automated Post-Ingestion Workflows Card */}
                <div
                  style={{
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                    backgroundColor: 'var(--bg-secondary)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    marginTop: '4px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={15} style={{ color: 'var(--accent-primary)' }} />
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Automated Post-Ingestion Workflows
                    </span>
                  </div>
                  <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', margin: 0 }}>
                    Automatically trigger intelligent background operations whenever books are imported (via drop folder or manual upload).
                  </p>

                  <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={pref.auto_download_metadata ?? false}
                      onChange={(e) => setPref({ ...pref, auto_download_metadata: e.target.checked })}
                      style={{ width: '16px', height: '16px', marginTop: '2px', accentColor: 'var(--accent-primary)' }}
                    />
                    <div>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Automatically Download &amp; Enrich Online Metadata
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>
                        Queries Google Books, OpenLibrary, and CrossRef in the background to fetch covers, ISBNs, publishers, and descriptions.
                      </span>
                    </div>
                  </label>

                  <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={pref.auto_index_rag ?? false}
                      onChange={(e) => setPref({ ...pref, auto_index_rag: e.target.checked })}
                      style={{ width: '16px', height: '16px', marginTop: '2px', accentColor: 'var(--accent-primary)' }}
                    />
                    <div>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Automatically Index for RAG Library Chat
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>
                        Extracts text and indexes semantic vectors into LanceDB for instant search &amp; conversational chat.
                      </span>
                    </div>
                  </label>

                  <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={pref.auto_generate_summary ?? false}
                      onChange={(e) => setPref({ ...pref, auto_generate_summary: e.target.checked })}
                      style={{ width: '16px', height: '16px', marginTop: '2px', accentColor: 'var(--accent-primary)' }}
                    />
                    <div>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Automatically Generate AI Multi-Resolution Summary
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>
                        Produces Executive Snapshot, Conceptual Index, and Chapter Breakdowns using your configured AI provider ({pref.active_ai_provider}).
                      </span>
                    </div>
                  </label>
                </div>

                {/* Trigger Manual Scan */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingTop: '8px' }}>
                  <button
                    onClick={handleScanDropFolder}
                    disabled={isScanningDrop || !pref.auto_import_folder}
                    className="btn btn-secondary"
                    style={{ fontSize: '12px', gap: '6px' }}
                  >
                    <FolderSync size={14} className={isScanningDrop ? 'animate-spin' : ''} />
                    <span>{isScanningDrop ? 'Scanning Intake...' : 'Scan Drop Folder Now'}</span>
                  </button>

                  {dropScanResult && (
                    <span style={{ fontSize: '12px', color: 'var(--accent-primary)', fontWeight: 500 }}>
                      {dropScanResult}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* TAB 3: Sharing & OPDS */}
            {activeTab === 'sharing' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
                    Network Sharing &amp; Content Server
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                    Wirelessly browse your library from e-readers, tablets, and phones.
                  </p>
                </div>

                {/* OPDS Server Card */}
                <div
                  style={{
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-default)',
                    background: 'var(--bg-card)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Wifi size={16} color="var(--accent-primary)" />
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        OPDS Catalog Server
                      </span>
                    </div>
                    <span style={{ fontSize: '10.5px', color: '#10b981', fontWeight: 700, background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '3px' }}>
                      RUNNING (Port 8000)
                    </span>
                  </div>

                  <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', margin: 0 }}>
                    Enter this URL into Moon+ Reader, KOReader, Apple Books, or KyBook to browse and download books directly:
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <code
                      style={{
                        flex: 1,
                        padding: '6px 10px',
                        background: 'var(--bg-surface-elevated)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-default)',
                        fontSize: '12px',
                        color: 'var(--accent-primary)',
                      }}
                    >
                      http://127.0.0.1:8000/opds
                    </code>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText('http://127.0.0.1:8000/opds');
                        setToastMessage('OPDS feed URL copied to clipboard');
                      }}
                      className="btn btn-ghost"
                      style={{ fontSize: '11px', padding: '6px 10px', gap: '4px' }}
                    >
                      <Link size={12} />
                      <span>Copy</span>
                    </button>
                  </div>
                </div>

                {/* Kosync Card */}
                <div
                  style={{
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-default)',
                    background: 'var(--bg-card)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Server size={16} color="#8b5cf6" />
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      KOReader Kosync Server
                    </span>
                  </div>
                  <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', margin: 0 }}>
                    Endpoint: <code style={{ color: 'var(--accent-primary)' }}>http://127.0.0.1:8000/api/kosync</code>
                  </p>
                  <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
                    Synchronize your reading position across devices automatically.
                  </p>
                </div>
              </div>
            )}

            {/* TAB 4: Defaults & Look and Feel */}
            {activeTab === 'defaults' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
                    Default Formats &amp; User Interface
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                    Configure default conversion targets, catalog presentation, and visual theme.
                  </p>
                </div>

                {/* Default Format */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Default Conversion Target Format
                  </label>
                  <select
                    value={pref.default_format}
                    onChange={(e) => setPref({ ...pref, default_format: e.target.value })}
                    className="select"
                    style={{ fontSize: '12.5px' }}
                  >
                    <option value="EPUB">EPUB (Recommended for modern e-readers)</option>
                    <option value="PDF">PDF (Fixed layout &amp; printable)</option>
                    <option value="MOBI">MOBI (Legacy Kindle format)</option>
                    <option value="AZW3">AZW3 (KF8 Kindle format)</option>
                    <option value="TXT">TXT (Plain text)</option>
                    <option value="DOCX">DOCX (Word Document)</option>
                  </select>
                </div>

                {/* Default Page Size */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Catalog Batch Limit
                  </label>
                  <select
                    value={pref.default_page_size}
                    onChange={(e) => setPref({ ...pref, default_page_size: Number(e.target.value) })}
                    className="select"
                    style={{ fontSize: '12.5px' }}
                  >
                    <option value="50">50 Books per fetch</option>
                    <option value="100">100 Books per fetch</option>
                    <option value="250">250 Books per fetch</option>
                    <option value="500">500 Books per fetch</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            padding: '0.85rem 1.25rem',
            borderTop: '1px solid var(--border-default)',
            background: 'var(--bg-surface-elevated)',
            gap: '8px',
          }}
        >
          <button
            onClick={() => setPreferencesOpen(false)}
            className="btn btn-ghost"
            style={{ fontSize: '12px' }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn btn-primary"
            style={{ fontSize: '12px', minWidth: '100px' }}
          >
            {isSaving ? 'Saving...' : 'Apply & Save'}
          </button>
        </div>
      </div>
    </div>
  );
};
