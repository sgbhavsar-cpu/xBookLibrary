import React from 'react';
import {
  FastForward,
  Headphones,
  Maximize2,
  Moon,
  Pause,
  Play,
  RotateCcw,
  RotateCw,
  X,
} from 'lucide-react';
import { useStore } from '../../store/useStore';

export const PersistentAudioBar: React.FC = () => {
  const {
    activeAudiobook,
    audioMetadata,
    audioPlayback,
    isAudiobookPlayerOpen,
    sleepTimerRemaining,
    openAudiobookPlayer,
    stopAudiobook,
    setAudioPlaying,
    setAudioPlaybackSpeed,
    seekAudio,
  } = useStore();

  if (!activeAudiobook || isAudiobookPlayerOpen) {
    return null;
  }

  const chapters = audioMetadata?.chapters || [];
  const currentChapter = chapters[audioPlayback.currentChapterIndex] || null;

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
    const clamped = Math.max(0, Math.min(audioPlayback.duration || 0, newTime));
    seekAudio(clamped);
  };

  const handleSkip = (seconds: number) => {
    const nextTime = Math.max(
      0,
      Math.min(audioPlayback.duration || 0, audioPlayback.currentTime + seconds)
    );
    seekAudio(nextTime);
  };

  const cycleSpeed = () => {
    const speeds = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0];
    const curIdx = speeds.indexOf(audioPlayback.playbackSpeed);
    const nextSpeed = curIdx >= 0 && curIdx < speeds.length - 1 ? speeds[curIdx + 1] : speeds[0];
    setAudioPlaybackSpeed(nextSpeed);
  };

  const progressPercent =
    audioPlayback.duration > 0
      ? Math.min(100, (audioPlayback.currentTime / audioPlayback.duration) * 100)
      : 0;

  return (
    <div
      className="glass-panel"
      style={{
        position: 'fixed',
        bottom: 'var(--status-bar-height, 28px)',
        left: 0,
        right: 0,
        height: '64px',
        zIndex: 35,
        borderTop: '1px solid var(--border-default)',
        background: 'var(--bg-surface-elevated)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.25rem',
        boxShadow: '0 -4px 16px rgba(0, 0, 0, 0.2)',
      }}
    >
      {/* Top Scrubber Track */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: 'var(--border-subtle)',
          cursor: 'pointer',
        }}
        onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const ratio = (e.clientX - rect.left) / rect.width;
          handleSeek(ratio * (audioPlayback.duration || 0));
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            background: 'var(--accent-primary)',
            transition: 'width 0.15s ease',
          }}
        />
      </div>

      {/* Left: Book Cover, Title, and Chapter */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          minWidth: '220px',
          maxWidth: '30%',
          overflow: 'hidden',
          cursor: 'pointer',
        }}
        onClick={openAudiobookPlayer}
        title="Click to open full player"
      >
        <div
          style={{
            width: '40px',
            height: '48px',
            borderRadius: 'var(--radius-sm)',
            overflow: 'hidden',
            background: 'var(--bg-surface)',
            boxShadow: 'var(--shadow-sm)',
            flexShrink: 0,
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
            <Headphones size={20} color="var(--accent-primary)" />
          )}
        </div>

        <div style={{ overflow: 'hidden' }}>
          <div
            style={{
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {activeAudiobook.title}
          </div>
          <div
            style={{
              fontSize: '11.5px',
              color: 'var(--text-secondary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {currentChapter ? currentChapter.title : activeAudiobook.author}
          </div>
        </div>
      </div>

      {/* Center: Scrubber & Transport Controls */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '4px',
          flex: 1,
          maxWidth: '520px',
          padding: '0 1rem',
        }}
      >
        {/* Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            className="btn-icon"
            onClick={() => handleSkip(-15)}
            title="Rewind 15 seconds"
            style={{ width: '30px', height: '30px' }}
          >
            <RotateCcw size={15} />
          </button>

          <button
            onClick={() => setAudioPlaying(!audioPlayback.isPlaying)}
            title={audioPlayback.isPlaying ? 'Pause' : 'Play'}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'var(--accent-primary)',
              color: '#fff',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              boxShadow: 'var(--shadow-md)',
              transition: 'transform 0.15s ease',
            }}
            onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.92)')}
            onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
          >
            {audioPlayback.isPlaying ? (
              <Pause size={18} fill="#fff" />
            ) : (
              <Play size={18} fill="#fff" style={{ marginLeft: '2px' }} />
            )}
          </button>

          <button
            className="btn-icon"
            onClick={() => handleSkip(30)}
            title="Forward 30 seconds"
            style={{ width: '30px', height: '30px' }}
          >
            <RotateCw size={15} />
          </button>
        </div>

        {/* Timestamp Range Slider */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '11px',
            color: 'var(--text-muted)',
          }}
        >
          <span style={{ minWidth: '45px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
            {formatSeconds(audioPlayback.currentTime)}
          </span>
          <input
            type="range"
            min={0}
            max={audioPlayback.duration || 100}
            step={0.5}
            value={audioPlayback.currentTime || 0}
            onChange={(e) => handleSeek(parseFloat(e.target.value))}
            style={{
              flex: 1,
              height: '4px',
              cursor: 'pointer',
              accentColor: 'var(--accent-primary)',
            }}
          />
          <span style={{ minWidth: '45px', fontVariantNumeric: 'tabular-nums' }}>
            {formatSeconds(audioPlayback.duration)}
          </span>
        </div>
      </div>

      {/* Right: Auxiliary Controls & Expand / Close */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          minWidth: '180px',
          justifyContent: 'flex-end',
        }}
      >
        {/* Sleep Timer Indicator */}
        {sleepTimerRemaining !== null && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11px',
              color: 'var(--accent-primary)',
              background: 'var(--accent-surface)',
              padding: '2px 8px',
              borderRadius: '12px',
              fontWeight: 600,
            }}
            title="Sleep timer active"
          >
            <Moon size={11} />
            <span>{Math.ceil(sleepTimerRemaining / 60)}m</span>
          </div>
        )}

        {/* Speed Button */}
        <button
          className="btn btn-secondary"
          onClick={cycleSpeed}
          title="Cycle playback speed"
          style={{
            padding: '3px 7px',
            fontSize: '11.5px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
          }}
        >
          <FastForward size={12} />
          <span>{audioPlayback.playbackSpeed}x</span>
        </button>

        {/* Expand to Full Player */}
        <button
          className="btn btn-secondary"
          onClick={openAudiobookPlayer}
          title="Expand to Full Player"
          style={{
            padding: '4px 8px',
            fontSize: '11.5px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Maximize2 size={13} />
          <span>Expand</span>
        </button>

        {/* Close / Stop Button */}
        <button
          className="btn-icon"
          onClick={stopAudiobook}
          title="Stop and Close Player"
          style={{ width: '28px', height: '28px' }}
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
};
