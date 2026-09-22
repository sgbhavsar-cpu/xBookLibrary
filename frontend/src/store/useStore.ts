/**
 * Centralized Zustand Store for xBookLibrary state management.
 */

import { create } from 'zustand';
import { api } from '../api/client';
import type {
  Annotation,
  AnnotationCreateRequest,
  AudiobookMetadata,
  AudioChapterTranscript,
  AudioPlaybackState,
  Book,
  Bookmark,
  BookmarkCreateRequest,
  BookSummary,
  CustomColumnDefinition,
  Device,
  DeviceSyncLog,
  Library,
  MetadataProposal,
  ReadingProgress,
  SeriesInfo,
  TaxonomyNode,
  VirtualLibrary,
} from '../types';

interface AppStore {
  // Theme
  theme: 'light' | 'dark';
  toggleTheme: () => void;

  // View Mode
  viewMode: 'grid' | 'table';
  setViewMode: (mode: 'grid' | 'table') => void;

  // Libraries
  libraries: Library[];
  activeLibraryId: string | null;
  loadLibraries: () => Promise<void>;
  switchLibrary: (id: string) => Promise<void>;

  // Catalog & Filters
  books: Book[];
  isLoadingBooks: boolean;
  searchQuery: string;
  selectedTaxonomyPath: string | null;
  selectedAuthor: string | null;
  selectedFormat: string | null;
  selectedSeries: string | null;
  taxonomyTree: TaxonomyNode[];

  // Custom Columns & Virtual Libraries & Series
  customColumns: CustomColumnDefinition[];
  seriesList: SeriesInfo[];
  virtualLibraries: VirtualLibrary[];
  activeVirtualLibrary: string | null;

  setSearchQuery: (query: string) => void;
  setSelectedTaxonomyPath: (path: string | null) => void;
  setSelectedAuthor: (author: string | null) => void;
  setSelectedFormat: (format: string | null) => void;
  setSelectedSeries: (series: string | null) => void;
  setActiveVirtualLibrary: (name: string | null) => void;
  loadBooks: () => Promise<void>;
  loadTaxonomies: () => Promise<void>;
  loadCustomColumns: () => Promise<void>;
  loadSeriesList: () => Promise<void>;
  loadVirtualLibraries: () => Promise<void>;

  // Inspector & Selected Book
  selectedBookId: number | null;
  selectedBook: Book | null;
  selectedBookSummary: BookSummary | null;
  selectedBookProposals: MetadataProposal[];
  isLoadingDetail: boolean;
  selectBook: (bookId: number | null) => Promise<void>;
  refreshSelectedBook: () => Promise<void>;

  // Reader View State
  readerBookId: number | null;
  readerFormat: string | null;
  readerTheme: 'light' | 'sepia' | 'dark' | 'black';
  readerFontSize: number;
  readerLayout: 'paginated' | 'scrolled';
  readerComicMode: 'ltr' | 'rtl' | 'webtoon';
  readerProgress: ReadingProgress | null;
  readerAnnotations: Annotation[];
  readerBookmarks: Bookmark[];
  isAnnotationsDrawerOpen: boolean;
  isReaderAIOpen: boolean;
  openReader: (bookId: number, format?: string) => void;
  closeReader: () => void;
  setReaderTheme: (theme: 'light' | 'sepia' | 'dark' | 'black') => void;
  setReaderFontSize: (size: number) => void;
  setReaderLayout: (layout: 'paginated' | 'scrolled') => void;
  setReaderComicMode: (mode: 'ltr' | 'rtl' | 'webtoon') => void;
  toggleAnnotationsDrawer: () => void;
  toggleReaderAI: () => void;
  loadReaderData: (bookId: number, format?: string) => Promise<void>;
  saveProgress: (location: string, percent: number, secondsIncrement?: number) => Promise<void>;
  addAnnotation: (req: AnnotationCreateRequest) => Promise<void>;
  removeAnnotation: (annotationId: string) => Promise<void>;
  addBookmark: (req: BookmarkCreateRequest) => Promise<void>;
  removeBookmark: (bookmarkId: string) => Promise<void>;

  // Global Modals & Drawers
  isRAGChatOpen: boolean;
  isSynthesisModalOpen: boolean;
  isIngestModalOpen: boolean;
  isSendToDeviceOpen: boolean;
  isDeviceSettingsOpen: boolean;
  setRAGChatOpen: (open: boolean) => void;
  setSynthesisModalOpen: (open: boolean) => void;
  setIngestModalOpen: (open: boolean) => void;
  setSendToDeviceOpen: (open: boolean) => void;
  setDeviceSettingsOpen: (open: boolean) => void;

  // Devices & E-Reader Sync
  devices: Device[];
  deviceSyncLogs: DeviceSyncLog[];
  loadDevices: () => Promise<void>;
  loadSyncLogs: () => Promise<void>;

  // Audiobook Hub & Whisper Transcription
  activeAudiobook: {
    bookId: number;
    title: string;
    author: string;
    coverUrl?: string;
    format: string;
    narrator?: string;
  } | null;
  audioMetadata: AudiobookMetadata | null;
  audioPlayback: AudioPlaybackState;
  audioTranscripts: AudioChapterTranscript[];
  isAudiobookPlayerOpen: boolean;
  isTranscribing: boolean;
  audioSeekTarget: number | null;
  sleepTimerMinutes: number | null;
  sleepTimerRemaining: number | null;

  playAudiobook: (book: Book, format?: string) => Promise<void>;
  closeAudiobookPlayer: () => void;
  openAudiobookPlayer: () => void;
  stopAudiobook: () => void;
  setAudioPlaying: (isPlaying: boolean) => void;
  setAudioCurrentTime: (time: number) => void;
  setAudioDuration: (duration: number) => void;
  setAudioPlaybackSpeed: (speed: number) => void;
  setAudioVolume: (volume: number) => void;
  setAudioChapter: (chapterIndex: number) => void;
  seekAudio: (time: number) => void;
  clearAudioSeekTarget: () => void;
  setSleepTimer: (minutes: number | null) => void;
  tickSleepTimer: () => void;
  syncAudioProgress: () => Promise<void>;
  loadAudioTranscripts: (bookId: number) => Promise<void>;
  transcribeAudioChapter: (bookId: number, chapterIndex?: number) => Promise<void>;
}

const initialTheme = (localStorage.getItem('xbook_theme') as 'light' | 'dark') || 'dark';
document.documentElement.setAttribute('data-theme', initialTheme);

export const useStore = create<AppStore>((set, get) => ({
  // Theme
  theme: initialTheme,
  toggleTheme: () => {
    const next = get().theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('xbook_theme', next);
    document.documentElement.setAttribute('data-theme', next);
    set({ theme: next });
  },

  // View Mode
  viewMode: 'grid',
  setViewMode: (mode) => set({ viewMode: mode }),

  // Libraries
  libraries: [],
  activeLibraryId: null,
  loadLibraries: async () => {
    try {
      const libs = await api.getLibraries();
      let activeId = get().activeLibraryId;
      if (!activeId && libs.length > 0) {
        activeId = libs[0].id;
      }
      set({ libraries: libs, activeLibraryId: activeId });
      if (activeId) {
        await Promise.all([
          get().loadBooks(),
          get().loadTaxonomies(),
          get().loadCustomColumns(),
          get().loadSeriesList(),
          get().loadVirtualLibraries(),
        ]);
      }
    } catch (err) {
      console.error('Failed to load libraries:', err);
    }
  },
  switchLibrary: async (id: string) => {
    try {
      await api.switchLibrary(id);
      set({
        activeLibraryId: id,
        selectedBookId: null,
        selectedBook: null,
        activeVirtualLibrary: null,
        selectedSeries: null,
      });
      await Promise.all([
        get().loadBooks(),
        get().loadTaxonomies(),
        get().loadCustomColumns(),
        get().loadSeriesList(),
        get().loadVirtualLibraries(),
      ]);
    } catch (err) {
      console.error('Failed to switch library:', err);
    }
  },

  // Catalog & Filtering
  books: [],
  isLoadingBooks: false,
  searchQuery: '',
  selectedTaxonomyPath: null,
  selectedAuthor: null,
  selectedFormat: null,
  selectedSeries: null,
  taxonomyTree: [],

  // Custom Columns & Virtual Libraries & Series
  customColumns: [],
  seriesList: [],
  virtualLibraries: [],
  activeVirtualLibrary: null,

  setSearchQuery: (searchQuery) => {
    set({ searchQuery });
  },
  setSelectedTaxonomyPath: (path) => {
    set({ selectedTaxonomyPath: path });
  },
  setSelectedAuthor: (author) => {
    set({ selectedAuthor: author });
  },
  setSelectedFormat: (format) => {
    set({ selectedFormat: format });
  },
  setSelectedSeries: (series) => {
    set({ selectedSeries: series });
  },
  setActiveVirtualLibrary: (activeVirtualLibrary) => {
    set({ activeVirtualLibrary });
  },

  loadBooks: async () => {
    set({ isLoadingBooks: true });
    try {
      const books = await api.getBooks({ limit: 500 });
      set({ books, isLoadingBooks: false });
      if (!get().selectedBookId && books.length > 0) {
        await get().selectBook(books[0].id);
      }
    } catch (err) {
      console.error('Failed to load books:', err);
      set({ isLoadingBooks: false });
    }
  },

  loadTaxonomies: async () => {
    try {
      const tree = await api.getTaxonomyTree();
      set({ taxonomyTree: tree });
    } catch (err) {
      console.error('Failed to load taxonomies:', err);
    }
  },

  loadCustomColumns: async () => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    try {
      const cols = await api.getCustomColumns(libId);
      set({ customColumns: cols });
    } catch (err) {
      console.error('Failed to load custom columns:', err);
    }
  },

  loadSeriesList: async () => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    try {
      const series = await api.getSeriesList(libId);
      set({ seriesList: series });
    } catch (err) {
      console.error('Failed to load series list:', err);
    }
  },

  loadVirtualLibraries: async () => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    try {
      const vls = await api.getVirtualLibraries(libId);
      set({ virtualLibraries: vls });
    } catch (err) {
      console.error('Failed to load virtual libraries:', err);
    }
  },

  // Inspector & Selected Book
  selectedBookId: null,
  selectedBook: null,
  selectedBookSummary: null,
  selectedBookProposals: [],
  isLoadingDetail: false,

  selectBook: async (bookId: number | null) => {
    if (bookId === null) {
      set({
        selectedBookId: null,
        selectedBook: null,
        selectedBookSummary: null,
        selectedBookProposals: [],
      });
      return;
    }

    set({ selectedBookId: bookId, isLoadingDetail: true });
    try {
      const [book, summary, proposals] = await Promise.all([
        api.getBook(bookId),
        api.getSummary(bookId),
        api.getProposals(bookId),
      ]);
      set({
        selectedBook: book,
        selectedBookSummary: summary,
        selectedBookProposals: proposals,
        isLoadingDetail: false,
      });
    } catch (err) {
      console.error('Failed to load book details:', err);
      set({ isLoadingDetail: false });
    }
  },

  refreshSelectedBook: async () => {
    const id = get().selectedBookId;
    if (id) {
      await get().selectBook(id);
    }
  },

  // Reader View
  readerBookId: null,
  readerFormat: null,
  readerTheme: 'dark',
  readerFontSize: 18,
  readerLayout: 'paginated',
  readerComicMode: 'ltr',
  readerProgress: null,
  readerAnnotations: [],
  readerBookmarks: [],
  isAnnotationsDrawerOpen: false,
  isReaderAIOpen: false,

  openReader: (bookId: number, format?: string) => {
    const fmt = format || 'EPUB';
    set({
      readerBookId: bookId,
      readerFormat: fmt,
      readerProgress: null,
      readerAnnotations: [],
      readerBookmarks: [],
      isAnnotationsDrawerOpen: false,
    });
    get().loadReaderData(bookId, fmt);
  },
  closeReader: () => {
    set({
      readerBookId: null,
      readerFormat: null,
      readerProgress: null,
      readerAnnotations: [],
      readerBookmarks: [],
      isAnnotationsDrawerOpen: false,
      isReaderAIOpen: false,
    });
  },
  setReaderTheme: (theme) => set({ readerTheme: theme }),
  setReaderFontSize: (size) => set({ readerFontSize: size }),
  setReaderLayout: (layout) => set({ readerLayout: layout }),
  setReaderComicMode: (mode) => set({ readerComicMode: mode }),
  toggleAnnotationsDrawer: () =>
    set((state) => ({ isAnnotationsDrawerOpen: !state.isAnnotationsDrawerOpen })),
  toggleReaderAI: () => set((state) => ({ isReaderAIOpen: !state.isReaderAIOpen })),

  loadReaderData: async (bookId: number, format?: string) => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    try {
      const [prog, anns, bms] = await Promise.all([
        api.getReadingProgress(libId, bookId, format),
        api.getAnnotations(libId, bookId),
        api.getBookmarks(libId, bookId),
      ]);
      set({
        readerProgress: prog,
        readerAnnotations: anns,
        readerBookmarks: bms,
      });
    } catch (err) {
      console.error('Failed to load reader data:', err);
    }
  },

  saveProgress: async (location: string, percent: number, secondsIncrement = 0) => {
    const libId = get().activeLibraryId;
    const bookId = get().readerBookId;
    const format = get().readerFormat || 'EPUB';
    if (!libId || !bookId) return;
    try {
      const updated = await api.saveReadingProgress(libId, bookId, {
        format,
        location,
        progress_percent: percent,
        seconds_increment: secondsIncrement,
      });
      set({ readerProgress: updated });
    } catch (err) {
      console.error('Failed to save reading progress:', err);
    }
  },

  addAnnotation: async (req: AnnotationCreateRequest) => {
    const libId = get().activeLibraryId;
    const bookId = get().readerBookId;
    if (!libId || !bookId) return;
    try {
      const created = await api.createAnnotation(libId, bookId, req);
      set((state) => ({
        readerAnnotations: [...state.readerAnnotations, created],
      }));
    } catch (err) {
      console.error('Failed to create annotation:', err);
    }
  },

  removeAnnotation: async (annotationId: string) => {
    const libId = get().activeLibraryId;
    const bookId = get().readerBookId;
    if (!libId || !bookId) return;
    try {
      await api.deleteAnnotation(libId, bookId, annotationId);
      set((state) => ({
        readerAnnotations: state.readerAnnotations.filter((a) => a.id !== annotationId),
      }));
    } catch (err) {
      console.error('Failed to delete annotation:', err);
    }
  },

  addBookmark: async (req: BookmarkCreateRequest) => {
    const libId = get().activeLibraryId;
    const bookId = get().readerBookId;
    if (!libId || !bookId) return;
    try {
      const created = await api.createBookmark(libId, bookId, req);
      set((state) => ({
        readerBookmarks: [...state.readerBookmarks, created],
      }));
    } catch (err) {
      console.error('Failed to create bookmark:', err);
    }
  },

  removeBookmark: async (bookmarkId: string) => {
    const libId = get().activeLibraryId;
    const bookId = get().readerBookId;
    if (!libId || !bookId) return;
    try {
      await api.deleteBookmark(libId, bookId, bookmarkId);
      set((state) => ({
        readerBookmarks: state.readerBookmarks.filter((b) => b.id !== bookmarkId),
      }));
    } catch (err) {
      console.error('Failed to delete bookmark:', err);
    }
  },

  // Modals & Drawers
  isRAGChatOpen: false,
  isSynthesisModalOpen: false,
  isIngestModalOpen: false,
  isSendToDeviceOpen: false,
  isDeviceSettingsOpen: false,
  setRAGChatOpen: (open) => set({ isRAGChatOpen: open }),
  setSynthesisModalOpen: (open) => set({ isSynthesisModalOpen: open }),
  setIngestModalOpen: (open) => set({ isIngestModalOpen: open }),
  setSendToDeviceOpen: (open) => set({ isSendToDeviceOpen: open }),
  setDeviceSettingsOpen: (open) => set({ isDeviceSettingsOpen: open }),

  // Devices & E-Reader Sync
  devices: [],
  deviceSyncLogs: [],
  loadDevices: async () => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    try {
      const devices = await api.listDevices(libId);
      set({ devices });
    } catch (err) {
      console.error('Failed to load devices:', err);
    }
  },
  loadSyncLogs: async () => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    try {
      const logs = await api.listSyncLogs(libId);
      set({ deviceSyncLogs: logs });
    } catch (err) {
      console.error('Failed to load sync logs:', err);
    }
  },

  // Audiobook Hub & Whisper Transcription
  activeAudiobook: null,
  audioMetadata: null,
  audioPlayback: {
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    playbackSpeed: 1.0,
    volume: 1.0,
    currentChapterIndex: 0,
  },
  audioTranscripts: [],
  isAudiobookPlayerOpen: false,
  isTranscribing: false,
  audioSeekTarget: null,
  sleepTimerMinutes: null,
  sleepTimerRemaining: null,

  playAudiobook: async (book: Book, format?: string) => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    const fmt = (
      format ||
      book.formats.find((f) => ['M4B', 'MP3'].includes(f.format.toUpperCase()))?.format ||
      'M4B'
    ).toUpperCase();

    // Set active audiobook shell
    set({
      activeAudiobook: {
        bookId: book.id,
        title: book.title,
        author: (book.authors || []).join(', ') || 'Unknown',
        coverUrl: book.has_cover ? api.getBookCoverUrl(book.id) : undefined,
        format: fmt,
      },
      isAudiobookPlayerOpen: true,
    });

    try {
      // Load technical metadata and saved progress
      const [meta, progress] = await Promise.all([
        api.getAudioMetadata(libId, book.id),
        api.getAudioProgress(libId, book.id),
      ]);

      const curTime = progress?.current_time || 0;
      const curChap = progress?.current_chapter_index || 0;
      const curSpeed = progress?.playback_speed || 1.0;

      set((state) => ({
        audioMetadata: meta,
        audioSeekTarget: curTime > 0 ? curTime : null,
        activeAudiobook: state.activeAudiobook
          ? {
              ...state.activeAudiobook,
              narrator: meta.narrator,
            }
          : null,
        audioPlayback: {
          ...state.audioPlayback,
          currentTime: curTime,
          duration: meta.duration_seconds,
          playbackSpeed: curSpeed,
          currentChapterIndex: curChap,
          isPlaying: true,
        },
      }));

      // Also load transcripts
      get().loadAudioTranscripts(book.id);
    } catch (err) {
      console.error('Failed to initialize audiobook playback:', err);
    }
  },

  closeAudiobookPlayer: () => {
    get().closeReader();
    set({ isAudiobookPlayerOpen: false });
  },
  openAudiobookPlayer: () => set({ isAudiobookPlayerOpen: true }),
  stopAudiobook: () => {
    get().syncAudioProgress();
    get().closeReader();
    set({
      activeAudiobook: null,
      audioMetadata: null,
      audioTranscripts: [],
      isAudiobookPlayerOpen: false,
      audioSeekTarget: null,
      sleepTimerMinutes: null,
      sleepTimerRemaining: null,
      audioPlayback: {
        ...get().audioPlayback,
        isPlaying: false,
        currentTime: 0,
      },
    });
  },
  setAudioPlaying: (isPlaying: boolean) =>
    set((state) => ({
      audioPlayback: { ...state.audioPlayback, isPlaying },
    })),
  setAudioCurrentTime: (time: number) =>
    set((state) => ({
      audioPlayback: { ...state.audioPlayback, currentTime: time },
    })),
  setAudioDuration: (duration: number) =>
    set((state) => ({
      audioPlayback: { ...state.audioPlayback, duration },
    })),
  setAudioPlaybackSpeed: (speed: number) =>
    set((state) => ({
      audioPlayback: { ...state.audioPlayback, playbackSpeed: speed },
    })),
  setAudioVolume: (volume: number) =>
    set((state) => ({
      audioPlayback: { ...state.audioPlayback, volume },
    })),
  setAudioChapter: (chapterIndex: number) => {
    const meta = get().audioMetadata;
    if (!meta || !meta.chapters[chapterIndex]) return;
    const targetSec = meta.chapters[chapterIndex].start_time;
    set((state) => ({
      audioSeekTarget: targetSec,
      audioPlayback: {
        ...state.audioPlayback,
        currentChapterIndex: chapterIndex,
        currentTime: targetSec,
      },
    }));
    get().syncAudioProgress();
  },
  seekAudio: (time: number) => {
    set((state) => ({
      audioSeekTarget: time,
      audioPlayback: {
        ...state.audioPlayback,
        currentTime: time,
      },
    }));
  },
  clearAudioSeekTarget: () => set({ audioSeekTarget: null }),
  setSleepTimer: (minutes: number | null) => {
    set({
      sleepTimerMinutes: minutes,
      sleepTimerRemaining: minutes ? minutes * 60 : null,
    });
  },
  tickSleepTimer: () => {
    const rem = get().sleepTimerRemaining;
    if (rem === null) return;
    if (rem <= 1) {
      set((state) => ({
        sleepTimerMinutes: null,
        sleepTimerRemaining: null,
        audioPlayback: { ...state.audioPlayback, isPlaying: false },
      }));
    } else {
      set({ sleepTimerRemaining: rem - 1 });
    }
  },

  syncAudioProgress: async () => {
    const libId = get().activeLibraryId;
    const active = get().activeAudiobook;
    const playback = get().audioPlayback;
    if (!libId || !active) return;
    try {
      await api.saveAudioProgress(libId, active.bookId, {
        current_time: playback.currentTime,
        current_chapter_index: playback.currentChapterIndex,
        playback_speed: playback.playbackSpeed,
      });
    } catch (err) {
      console.error('Failed to sync audio progress:', err);
    }
  },

  loadAudioTranscripts: async (bookId: number) => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    try {
      const transcripts = await api.getAudioTranscripts(libId, bookId);
      set({ audioTranscripts: transcripts });
    } catch (err) {
      console.error('Failed to load audio transcripts:', err);
    }
  },

  transcribeAudioChapter: async (bookId: number, chapterIndex?: number) => {
    const libId = get().activeLibraryId;
    if (!libId) return;
    set({ isTranscribing: true });
    try {
      const newTranscripts = await api.transcribeAudio(libId, bookId, chapterIndex);
      set((state) => {
        const existing = [...state.audioTranscripts];
        for (const nt of newTranscripts) {
          const idx = existing.findIndex((t) => t.chapter_index === nt.chapter_index);
          if (idx >= 0) {
            existing[idx] = nt;
          } else {
            existing.push(nt);
          }
        }
        existing.sort((a, b) => a.chapter_index - b.chapter_index);
        return { audioTranscripts: existing, isTranscribing: false };
      });
    } catch (err) {
      console.error('Failed to transcribe audio:', err);
      set({ isTranscribing: false });
    }
  },
}));
