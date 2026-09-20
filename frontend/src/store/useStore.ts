/**
 * Centralized Zustand Store for xBookLibrary state management.
 */

import { create } from 'zustand';
import { api } from '../api/client';
import type {
  Book,
  BookSummary,
  Library,
  MetadataProposal,
  TaxonomyNode,
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
  taxonomyTree: TaxonomyNode[];

  setSearchQuery: (query: string) => void;
  setSelectedTaxonomyPath: (path: string | null) => void;
  setSelectedAuthor: (author: string | null) => void;
  setSelectedFormat: (format: string | null) => void;
  loadBooks: () => Promise<void>;
  loadTaxonomies: () => Promise<void>;

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
  isReaderAIOpen: boolean;
  openReader: (bookId: number, format?: string) => void;
  closeReader: () => void;
  setReaderTheme: (theme: 'light' | 'sepia' | 'dark' | 'black') => void;
  setReaderFontSize: (size: number) => void;
  toggleReaderAI: () => void;

  // Global Modals & Drawers
  isRAGChatOpen: boolean;
  isSynthesisModalOpen: boolean;
  isIngestModalOpen: boolean;
  setRAGChatOpen: (open: boolean) => void;
  setSynthesisModalOpen: (open: boolean) => void;
  setIngestModalOpen: (open: boolean) => void;
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
        await get().loadBooks();
        await get().loadTaxonomies();
      }
    } catch (err) {
      console.error('Failed to load libraries:', err);
    }
  },
  switchLibrary: async (id: string) => {
    try {
      await api.switchLibrary(id);
      set({ activeLibraryId: id, selectedBookId: null, selectedBook: null });
      await get().loadBooks();
      await get().loadTaxonomies();
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
  taxonomyTree: [],

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
  isReaderAIOpen: false,

  openReader: (bookId: number, format?: string) => {
    set({
      readerBookId: bookId,
      readerFormat: format || 'EPUB',
    });
  },
  closeReader: () => {
    set({ readerBookId: null, readerFormat: null, isReaderAIOpen: false });
  },
  setReaderTheme: (theme) => set({ readerTheme: theme }),
  setReaderFontSize: (size) => set({ readerFontSize: size }),
  toggleReaderAI: () => set((state) => ({ isReaderAIOpen: !state.isReaderAIOpen })),

  // Modals & Drawers
  isRAGChatOpen: false,
  isSynthesisModalOpen: false,
  isIngestModalOpen: false,
  setRAGChatOpen: (open) => set({ isRAGChatOpen: open }),
  setSynthesisModalOpen: (open) => set({ isSynthesisModalOpen: open }),
  setIngestModalOpen: (open) => set({ isIngestModalOpen: open }),
}));
