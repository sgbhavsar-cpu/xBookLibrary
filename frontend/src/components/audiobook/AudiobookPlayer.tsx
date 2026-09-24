import React, { useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  ChevronDown,
  Download,
  FastForward,
  FileText,
  Headphones,
  List,
  Loader2,
  Mic,
  Moon,
  Pause,
  Play,
  RotateCcw,
  RotateCw,
  SkipBack,
  SkipForward,
  Sparkles,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';
import type { AudioChapter, AudioTranscriptSegment } from '../../types';

export const AudiobookPlayer: React.FC = () => {
  const {
    activeLibraryId,
    activeAudiobook,
    audioMetadata,
    audioPlayback,
    audioTranscripts,
    isTranscribing,
    sleepTimerMinutes,
    sleepTimerRemaining,
    closeAudiobookPlayer,
    setAudioPlaying,
    setAudioPlaybackSpeed,
    setAudioVolume,
    setAudioChapter,
    seekAudio,
    setSleepTimer,
    syncAudioProgress,
    transcribeAudioChapter,
  } = useStore();

  const transcriptScrollRef = useRef<HTMLDivElement | null>(null);

  const [activeTab, setActiveTab] = useState<'chapters' | 'transcript'>('chapters');
  const [isSpeedMenuOpen, setIsSpeedMenuOpen] = useState(false);
  const [isSleepMenuOpen, setIsSleepMenuOpen] = useState(false);
  const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);

  const chapters: AudioChapter[] = audioMetadata?.chapters || [];
  const currentChapter = chapters[audioPlayback.currentChapterIndex] || null;

  // Active chapter's transcript
  const currentTranscript = audioTranscripts.find(
    (t) => t.chapter_index === audioPlayback.currentChapterIndex
  );

  // Auto-scroll transcript to active segment
  useEffect(() => {
    if (activeTab !== 'transcript' || !transcriptScrollRef.current) return;
    const activeElem = transcriptScrollRef.current.querySelector('.active-transcript-segment');
    if (activeElem) {
      activeElem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [audioPlayback.currentTime, activeTab]);

  // Global Escape key listener: closes any book open for listening
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        syncAudioProgress();
        closeAudiobookPlayer();
      }
    };
    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [closeAudiobookPlayer, syncAudioProgress]);

  if (!activeAudiobook || !activeLibraryId) {
    return null;
  }

  const formatSeconds = (sec: number) => {
    const s = Math.floor(sec || 0);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    if (hrs > 0) {
      return `${hrs}:${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleSeek = (newTime: number) => {
    seekAudio(newTime);

    // Update current chapter index if seeking across boundaries
    const newChapIdx = chapters.findIndex(
      (c) => newTime >= c.start_time && newTime < c.end_time
    );
    if (newChapIdx >= 0 && newChapIdx !== audioPlayback.currentChapterIndex) {
      setAudioChapter(newChapIdx);
    }
  };

  const handleSkip = (seconds: number) => {
    const nextTime = Math.max(0, Math.min(audioPlayback.duration, audioPlayback.currentTime + seconds));
    handleSeek(nextTime);
  };

  const handleNextChapter = () => {
    if (audioPlayback.currentChapterIndex + 1 < chapters.length) {
      setAudioChapter(audioPlayback.currentChapterIndex + 1);
    }
  };

  const handlePrevChapter = () => {
    if (audioPlayback.currentChapterIndex > 0) {
      setAudioChapter(audioPlayback.currentChapterIndex - 1);
    }
  };

  const isSegmentActive = (seg: AudioTranscriptSegment) => {
    return audioPlayback.currentTime >= seg.start && audioPlayback.currentTime <= seg.end;
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-app)',
        color: 'var(--text-primary)',
        overflow: 'hidden',
        zIndex: 100,
      }}
    >

      {/* Top Navigation Bar */}
      <header
        className="glass-panel"
        style={{
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 1.5rem',
          borderBottom: '1px solid var(--border-default)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            className="btn btn-secondary"
            onClick={() => {
              syncAudioProgress();
              closeAudiobookPlayer();
            }}
            title="Return to Library"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px' }}
          >
            <ArrowLeft size={16} />
            <span>Library</span>
          </button>
          <div>
            <div style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
              {activeAudiobook.title}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {activeAudiobook.author}
              {activeAudiobook.narrator && ` • Narrated by ${activeAudiobook.narrator}`}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(59, 130, 246, 0.15)',
              color: '#3b82f6',
              fontWeight: 600,
              textTransform: 'uppercase',
            }}
          >
            {activeAudiobook.format} AUDIOBOOK
          </span>
        </div>
      </header>

      {/* Main Studio Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left: Player Stage */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
            overflowY: 'auto',
          }}
        >
          {/* Cover Art Stage */}
          <div
            style={{
              width: '280px',
              height: '280px',
              borderRadius: '16px',
              overflow: 'hidden',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(59, 130, 246, 0.2)',
              position: 'relative',
              marginBottom: '1.5rem',
              background: 'var(--bg-card)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {activeAudiobook.coverUrl ? (
              <img
                src={activeAudiobook.coverUrl}
                alt={activeAudiobook.title}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : (
              <Headphones size={80} style={{ color: 'var(--accent-primary)', opacity: 0.6 }} />
            )}
          </div>

          {/* Chapter & Title Indicator */}
          <div style={{ textAlign: 'center', marginBottom: '1.5rem', maxWidth: '420px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 4px 0', color: 'var(--text-primary)' }}>
              {currentChapter ? currentChapter.title : 'Audiobook Playback'}
            </h2>
            <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
              Chapter {audioPlayback.currentChapterIndex + 1} of {Math.max(1, chapters.length)}
            </div>
          </div>

          {/* Scrubber / Progress Bar */}
          <div style={{ width: '100%', maxWidth: '520px', marginBottom: '1.5rem' }}>
            <input
              type="range"
              min={0}
              max={audioPlayback.duration || 100}
              step={0.5}
              value={audioPlayback.currentTime}
              onChange={(e) => handleSeek(Number(e.target.value))}
              style={{
                width: '100%',
                cursor: 'pointer',
                accentColor: 'var(--accent-primary)',
              }}
            />
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '12px',
                color: 'var(--text-muted)',
                marginTop: '4px',
              }}
            >
              <span>{formatSeconds(audioPlayback.currentTime)}</span>
              <span>
                {audioPlayback.duration > 0
                  ? `-${formatSeconds(Math.max(0, audioPlayback.duration - audioPlayback.currentTime))}`
                  : '00:00'}
              </span>
            </div>
          </div>

          {/* Primary Transport Controls */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '16px',
              marginBottom: '1.5rem',
            }}
          >
            {/* Rewind 15s */}
            <button
              className="btn btn-secondary"
              onClick={() => handleSkip(-15)}
              title="Rewind 15 seconds"
              style={{ borderRadius: '50%', width: '42px', height: '42px', padding: 0 }}
            >
              <RotateCcw size={18} />
            </button>

            {/* Prev Chapter */}
            <button
              className="btn btn-secondary"
              onClick={handlePrevChapter}
              disabled={audioPlayback.currentChapterIndex <= 0}
              title="Previous Chapter"
              style={{ borderRadius: '50%', width: '42px', height: '42px', padding: 0 }}
            >
              <SkipBack size={18} />
            </button>

            {/* Big Play / Pause */}
            <button
              onClick={() => setAudioPlaying(!audioPlayback.isPlaying)}
              title={audioPlayback.isPlaying ? 'Pause' : 'Play'}
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'var(--accent-primary)',
                color: '#ffffff',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
                transition: 'transform 0.15s ease',
              }}
            >
              {audioPlayback.isPlaying ? <Pause size={28} /> : <Play size={28} style={{ marginLeft: '4px' }} />}
            </button>

            {/* Next Chapter */}
            <button
              className="btn btn-secondary"
              onClick={handleNextChapter}
              disabled={audioPlayback.currentChapterIndex >= chapters.length - 1}
              title="Next Chapter"
              style={{ borderRadius: '50%', width: '42px', height: '42px', padding: 0 }}
            >
              <SkipForward size={18} />
            </button>

            {/* Forward 30s */}
            <button
              className="btn btn-secondary"
              onClick={() => handleSkip(30)}
              title="Forward 30 seconds"
              style={{ borderRadius: '50%', width: '42px', height: '42px', padding: 0 }}
            >
              <RotateCw size={18} />
            </button>
          </div>

          {/* Secondary Controls Bar (Speed, Sleep, Volume) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-default)',
            }}
          >
            {/* Speed Selector */}
            <div style={{ position: 'relative' }}>
              <button
                className="btn btn-secondary"
                onClick={() => setIsSpeedMenuOpen(!isSpeedMenuOpen)}
                style={{ fontSize: '11.5px', padding: '4px 8px' }}
                title="Playback Speed"
              >
                <FastForward size={13} />
                <span>{audioPlayback.playbackSpeed}x</span>
              </button>
              {isSpeedMenuOpen && (
                <div
                  className="glass-panel"
                  style={{
                    position: 'absolute',
                    bottom: '100%',
                    left: 0,
                    marginBottom: '6px',
                    borderRadius: 'var(--radius-sm)',
                    boxShadow: 'var(--shadow-md)',
                    display: 'flex',
                    flexDirection: 'column',
                    zIndex: 60,
                    minWidth: '70px',
                    overflow: 'hidden',
                  }}
                >
                  {[0.75, 1.0, 1.25, 1.5, 1.75, 2.0].map((s) => (
                    <button
                      key={s}
                      onClick={() => {
                        setAudioPlaybackSpeed(s);
                        setIsSpeedMenuOpen(false);
                      }}
                      style={{
                        padding: '6px 10px',
                        background: audioPlayback.playbackSpeed === s ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                        color: audioPlayback.playbackSpeed === s ? 'var(--accent-primary)' : 'var(--text-primary)',
                        border: 'none',
                        textAlign: 'left',
                        cursor: 'pointer',
                        fontSize: '11.5px',
                      }}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Sleep Timer */}
            <div style={{ position: 'relative' }}>
              <button
                className="btn btn-secondary"
                onClick={() => setIsSleepMenuOpen(!isSleepMenuOpen)}
                style={{ fontSize: '11.5px', padding: '4px 8px' }}
                title="Sleep Timer"
              >
                <Moon size={13} />
                <span>
                  {sleepTimerRemaining !== null
                    ? `${Math.ceil(sleepTimerRemaining / 60)}m`
                    : 'Timer'}
                </span>
              </button>
              {isSleepMenuOpen && (
                <div
                  className="glass-panel"
                  style={{
                    position: 'absolute',
                    bottom: '100%',
                    left: 0,
                    marginBottom: '6px',
                    borderRadius: 'var(--radius-sm)',
                    boxShadow: 'var(--shadow-md)',
                    display: 'flex',
                    flexDirection: 'column',
                    zIndex: 60,
                    minWidth: '100px',
                    overflow: 'hidden',
                  }}
                >
                  {[null, 15, 30, 45, 60].map((mins) => (
                    <button
                      key={mins ?? 'off'}
                      onClick={() => {
                        setSleepTimer(mins);
                        setIsSleepMenuOpen(false);
                      }}
                      style={{
                        padding: '6px 10px',
                        background: sleepTimerMinutes === mins ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                        color: sleepTimerMinutes === mins ? 'var(--accent-primary)' : 'var(--text-primary)',
                        border: 'none',
                        textAlign: 'left',
                        cursor: 'pointer',
                        fontSize: '11.5px',
                      }}
                    >
                      {mins === null ? 'Off' : `${mins} Minutes`}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Volume Control */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <button
                onClick={() => setAudioVolume(audioPlayback.volume > 0 ? 0 : 1.0)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}
              >
                {audioPlayback.volume === 0 ? <VolumeX size={15} /> : <Volume2 size={15} />}
              </button>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={audioPlayback.volume}
                onChange={(e) => setAudioVolume(Number(e.target.value))}
                style={{ width: '60px', cursor: 'pointer', accentColor: 'var(--accent-primary)' }}
              />
            </div>
          </div>
        </div>

        {/* Right Panel: Chapters & Synchronized Transcript */}
        <div
          style={{
            width: '380px',
            borderLeft: '1px solid var(--border-default)',
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--bg-card)',
          }}
        >
          {/* Tabs */}
          <div
            style={{
              display: 'flex',
              borderBottom: '1px solid var(--border-default)',
              padding: '0 8px',
            }}
          >
            <button
              onClick={() => setActiveTab('chapters')}
              style={{
                flex: 1,
                padding: '12px 8px',
                border: 'none',
                background: 'transparent',
                fontWeight: activeTab === 'chapters' ? 700 : 500,
                color: activeTab === 'chapters' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                borderBottom: activeTab === 'chapters' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '12.5px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <List size={14} />
              <span>Chapters ({chapters.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('transcript')}
              style={{
                flex: 1,
                padding: '12px 8px',
                border: 'none',
                background: 'transparent',
                fontWeight: activeTab === 'transcript' ? 700 : 500,
                color: activeTab === 'transcript' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                borderBottom: activeTab === 'transcript' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '12.5px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <FileText size={14} />
              <span>Live Transcript</span>
            </button>
          </div>

          {/* Tab 1: Chapter Outline */}
          {activeTab === 'chapters' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
              {chapters.map((ch, idx) => {
                const isCur = idx === audioPlayback.currentChapterIndex;
                return (
                  <div
                    key={idx}
                    onClick={() => setAudioChapter(idx)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      marginBottom: '4px',
                      cursor: 'pointer',
                      background: isCur ? 'rgba(59, 130, 246, 0.12)' : 'transparent',
                      border: isCur ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <div>
                      <div
                        style={{
                          fontSize: '13px',
                          fontWeight: isCur ? 700 : 500,
                          color: isCur ? 'var(--accent-primary)' : 'var(--text-primary)',
                        }}
                      >
                        {ch.title}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Starts at {formatSeconds(ch.start_time)}
                      </div>
                    </div>
                    <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                      {formatSeconds(ch.duration)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Tab 2: Live Synchronized Transcript */}
          {activeTab === 'transcript' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* Transcript Toolbar */}
              <div
                style={{
                  padding: '8px 12px',
                  borderBottom: '1px solid var(--border-default)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <button
                  className="btn btn-secondary"
                  disabled={isTranscribing}
                  onClick={() => transcribeAudioChapter(activeAudiobook.bookId, audioPlayback.currentChapterIndex)}
                  style={{ fontSize: '11.5px', padding: '4px 8px', gap: '4px', color: 'var(--accent-primary)' }}
                >
                  {isTranscribing ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                  <span>{currentTranscript ? 'Re-Transcribe' : 'Transcribe Chapter'}</span>
                </button>

                {/* Export Dropdown */}
                {currentTranscript && (
                  <div style={{ position: 'relative' }}>
                    <button
                      className="btn btn-secondary"
                      onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}
                      style={{ fontSize: '11.5px', padding: '4px 8px', gap: '4px' }}
                    >
                      <Download size={12} />
                      <span>Export</span>
                      <ChevronDown size={11} />
                    </button>
                    {isExportMenuOpen && (
                      <div
                        className="glass-panel"
                        style={{
                          position: 'absolute',
                          right: 0,
                          top: '100%',
                          marginTop: '4px',
                          borderRadius: 'var(--radius-sm)',
                          boxShadow: 'var(--shadow-md)',
                          display: 'flex',
                          flexDirection: 'column',
                          zIndex: 60,
                          minWidth: '120px',
                          overflow: 'hidden',
                        }}
                      >
                        {(['vtt', 'srt', 'md'] as const).map((fmt) => (
                          <a
                            key={fmt}
                            href={api.getAudioTranscriptExportUrl(activeLibraryId, activeAudiobook.bookId, fmt)}
                            download
                            onClick={() => setIsExportMenuOpen(false)}
                            style={{
                              padding: '8px 12px',
                              color: 'var(--text-primary)',
                              textDecoration: 'none',
                              fontSize: '11.5px',
                              textAlign: 'left',
                            }}
                          >
                            Export as .{fmt.toUpperCase()}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Transcript Body */}
              <div
                ref={transcriptScrollRef}
                style={{
                  flex: 1,
                  overflowY: 'auto',
                  padding: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                {currentTranscript ? (
                  currentTranscript.segments.map((seg, idx) => {
                    const active = isSegmentActive(seg);
                    return (
                      <div
                        key={idx}
                        onClick={() => handleSeek(seg.start)}
                        className={active ? 'active-transcript-segment' : ''}
                        style={{
                          padding: '6px 8px',
                          borderRadius: 'var(--radius-sm)',
                          cursor: 'pointer',
                          background: active ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                          borderLeft: active ? '3px solid var(--accent-primary)' : '3px solid transparent',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <span
                          style={{
                            fontSize: '10.5px',
                            fontWeight: 700,
                            color: active ? 'var(--accent-primary)' : 'var(--text-muted)',
                            marginRight: '6px',
                          }}
                        >
                          [{formatSeconds(seg.start)}]
                        </span>
                        <span
                          style={{
                            fontSize: '12.5px',
                            lineHeight: 1.5,
                            color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                            fontWeight: active ? 600 : 400,
                          }}
                        >
                          {seg.text}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <div
                    style={{
                      padding: '2rem 1rem',
                      textAlign: 'center',
                      color: 'var(--text-muted)',
                      fontSize: '12.5px',
                    }}
                  >
                    <Mic size={32} style={{ margin: '0 auto 8px auto', opacity: 0.4 }} />
                    <p style={{ margin: '0 0 8px 0' }}>No transcript generated for this chapter yet.</p>
                    <button
                      className="btn btn-secondary"
                      disabled={isTranscribing}
                      onClick={() => transcribeAudioChapter(activeAudiobook.bookId, audioPlayback.currentChapterIndex)}
                      style={{ fontSize: '11.5px', padding: '6px 12px', color: 'var(--accent-primary)' }}
                    >
                      {isTranscribing ? 'Transcribing...' : 'Transcribe with Whisper'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
