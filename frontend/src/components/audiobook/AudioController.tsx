import React, { useEffect, useRef } from 'react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';

/**
 * Headless, persistent audio controller component.
 * Stays mounted whenever activeAudiobook is non-null so audio continues
 * playing seamlessly whether the full player, mini-player, or library is visible.
 */
export const AudioController: React.FC = () => {
  const {
    activeLibraryId,
    activeAudiobook,
    audioMetadata,
    audioPlayback,
    audioSeekTarget,
    sleepTimerRemaining,
    setAudioPlaying,
    setAudioCurrentTime,
    setAudioDuration,
    setAudioChapter,
    clearAudioSeekTarget,
    syncAudioProgress,
    tickSleepTimer,
  } = useStore();

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const chapters = audioMetadata?.chapters || [];
  const currentChapter = chapters[audioPlayback.currentChapterIndex] || null;

  // Stream URL
  const streamUrl =
    activeLibraryId && activeAudiobook
      ? api.getAudioStreamUrl(activeLibraryId, activeAudiobook.bookId, activeAudiobook.format)
      : undefined;

  // Handle play / pause changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !streamUrl) return;

    if (audioPlayback.isPlaying) {
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          console.warn('Audio play was prevented or aborted:', err);
          setAudioPlaying(false);
        });
      }
    } else {
      audio.pause();
    }
  }, [audioPlayback.isPlaying, streamUrl, setAudioPlaying]);

  // Handle seek requests from store
  useEffect(() => {
    if (audioSeekTarget === null || !audioRef.current) return;
    const target = audioSeekTarget;
    audioRef.current.currentTime = target;
    clearAudioSeekTarget();
  }, [audioSeekTarget, clearAudioSeekTarget]);

  // Handle playback rate changes
  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.playbackRate = audioPlayback.playbackSpeed;
  }, [audioPlayback.playbackSpeed]);

  // Handle volume changes
  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.volume = audioPlayback.volume;
  }, [audioPlayback.volume]);

  // Sleep Timer Countdown (1-second tick)
  useEffect(() => {
    if (sleepTimerRemaining === null) return;
    const timer = setInterval(() => {
      tickSleepTimer();
    }, 1000);
    return () => clearInterval(timer);
  }, [sleepTimerRemaining, tickSleepTimer]);

  // Periodic Progress Sync (every 8 seconds while playing)
  useEffect(() => {
    if (!audioPlayback.isPlaying) return;
    const interval = setInterval(() => {
      syncAudioProgress();
    }, 8000);
    return () => clearInterval(interval);
  }, [audioPlayback.isPlaying, syncAudioProgress]);

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    const cur = audio.currentTime;
    setAudioCurrentTime(cur);

    // Track chapter boundary crossings
    if (currentChapter && (cur < currentChapter.start_time || cur >= currentChapter.end_time)) {
      const idx = chapters.findIndex((c) => cur >= c.start_time && cur < c.end_time);
      if (idx >= 0 && idx !== audioPlayback.currentChapterIndex) {
        setAudioChapter(idx);
      }
    }
  };

  const handleLoadedMetadata = () => {
    const audio = audioRef.current;
    if (!audio) return;
    const dur = audio.duration || audioPlayback.duration;
    if (dur > 0) {
      setAudioDuration(dur);
    }
    if (audioPlayback.currentTime > 0 && Math.abs(audio.currentTime - audioPlayback.currentTime) > 1) {
      audio.currentTime = audioPlayback.currentTime;
    }
  };

  const handleEnded = () => {
    setAudioPlaying(false);
    syncAudioProgress();
  };

  if (!streamUrl) return null;

  return (
    <audio
      ref={audioRef}
      src={streamUrl}
      preload="metadata"
      onTimeUpdate={handleTimeUpdate}
      onLoadedMetadata={handleLoadedMetadata}
      onEnded={handleEnded}
      onError={(e) => {
        console.error('Audio playback error:', e);
        setAudioPlaying(false);
      }}
      style={{ display: 'none' }}
    />
  );
};
