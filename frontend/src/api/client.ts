/**
 * Typed REST API client for xBookLibrary backend.
 */

import type {
  Book,
  BookSummary,
  ChatMessage,
  ChatSession,
  IngestionJob,
  Library,
  MetadataProposal,
  SynthesisDocument,
  SynthesisJobStatus,
  TaxonomyNode,
} from '../types';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(endpoint, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    let errMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
    } catch {
      // Use fallback error message
    }
    throw new Error(errMsg);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}

export const api = {
  // Libraries
  async getLibraries(): Promise<Library[]> {
    return request<Library[]>('/api/libraries');
  },

  async switchLibrary(libraryId: string): Promise<Library> {
    return request<Library>(`/api/libraries/${libraryId}/switch`, { method: 'POST' });
  },

  async createLibrary(path: string, name: string): Promise<Library> {
    return request<Library>('/api/libraries/create', {
      method: 'POST',
      body: JSON.stringify({ path, name, set_active: true }),
    });
  },

  async adoptLibrary(path: string, name?: string): Promise<Library> {
    return request<Library>('/api/libraries/adopt', {
      method: 'POST',
      body: JSON.stringify({ path, name, set_active: true }),
    });
  },

  // Books & Catalog
  async getBooks(params?: {
    page?: number;
    limit?: number;
    query?: string;
    library_id?: string;
  }): Promise<Book[]> {
    const sp = new URLSearchParams();
    if (params?.page) sp.set('page', params.page.toString());
    if (params?.limit) sp.set('limit', params.limit.toString());
    if (params?.query) sp.set('query', params.query);
    if (params?.library_id) sp.set('library_id', params.library_id);
    const qs = sp.toString() ? `?${sp.toString()}` : '';
    return request<Book[]>(`/api/books${qs}`);
  },

  async getBook(bookId: number): Promise<Book> {
    return request<Book>(`/api/books/${bookId}`);
  },

  async uploadBooks(files: File[]): Promise<IngestionJob[]> {
    const data = new FormData();
    for (const f of files) {
      data.append('files', f);
    }
    const res = await fetch('/api/books/upload', {
      method: 'POST',
      body: data,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
    return res.json();
  },

  getBookCoverUrl(bookId: number): string {
    return `/covers/${bookId}.jpg`;
  },

  getBookDownloadUrl(bookId: number, format: string): string {
    return `/api/books/${bookId}/download/${format.toUpperCase()}`;
  },

  // Taxonomies
  async getTaxonomyTree(): Promise<TaxonomyNode[]> {
    return request<TaxonomyNode[]>('/api/taxonomies/tree');
  },

  async assignTaxonomy(bookId: number, taxonomyPath: string): Promise<void> {
    await request(`/api/taxonomies/assign`, {
      method: 'POST',
      body: JSON.stringify({ book_id: bookId, taxonomy_path: taxonomyPath }),
    });
  },

  // Metadata Proposals
  async getProposals(bookId?: number): Promise<MetadataProposal[]> {
    const qs = bookId ? `?book_id=${bookId}` : '';
    return request<MetadataProposal[]>(`/api/proposals${qs}`);
  },

  async enrichBook(bookId: number): Promise<{ message: string; proposal_id?: string }> {
    return request(`/api/books/${bookId}/enrich`, { method: 'POST' });
  },

  async applyProposal(proposalId: string): Promise<void> {
    await request(`/api/proposals/${proposalId}/apply`, { method: 'POST' });
  },

  async rejectProposal(proposalId: string): Promise<void> {
    await request(`/api/proposals/${proposalId}/reject`, { method: 'POST' });
  },

  // Summaries
  async getSummary(bookId: number): Promise<BookSummary | null> {
    try {
      return await request<BookSummary>(`/api/books/${bookId}/summary`);
    } catch {
      return null;
    }
  },

  async generateSummary(bookId: number, templateType = 'executive'): Promise<BookSummary> {
    return request<BookSummary>(`/api/books/${bookId}/summary/generate`, {
      method: 'POST',
      body: JSON.stringify({ template_type: templateType }),
    });
  },

  // RAG & Chat
  async indexBook(bookId: number): Promise<{ book_id: number; status: string; chunks_indexed: number }> {
    return request(`/api/books/${bookId}/index`, { method: 'POST' });
  },

  async getLibraryIndexStatus(libraryId: string): Promise<{
    total_books: number;
    indexed_books: number;
    total_chunks: number;
  }> {
    return request(`/api/libraries/${libraryId}/index/status`);
  },

  async createChatSession(libraryId: string, bookId?: number, title?: string): Promise<ChatSession> {
    return request<ChatSession>('/api/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ library_id: libraryId, book_id: bookId, title }),
    });
  },

  async getChatMessages(sessionId: string): Promise<ChatMessage[]> {
    return request<ChatMessage[]>(`/api/chat/sessions/${sessionId}/messages`);
  },

  async sendChatMessage(sessionId: string, content: string): Promise<ChatMessage> {
    return request<ChatMessage>(`/api/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  },

  // Synthesis Studio
  async generateSynthesis(payload: {
    title: string;
    topic_prompt: string;
    template_type: string;
    book_ids?: number[];
    library_id?: string;
    wait?: boolean;
  }): Promise<SynthesisDocument | SynthesisJobStatus> {
    return request('/api/synthesis/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getSynthesisJob(jobId: string): Promise<SynthesisJobStatus> {
    return request<SynthesisJobStatus>(`/api/synthesis/jobs/${jobId}`);
  },

  async getSynthesisDocuments(libraryId?: string): Promise<SynthesisDocument[]> {
    const qs = libraryId ? `?library_id=${libraryId}` : '';
    return request<SynthesisDocument[]>(`/api/synthesis/documents${qs}`);
  },

  async getSynthesisDocument(docId: string): Promise<SynthesisDocument> {
    return request<SynthesisDocument>(`/api/synthesis/documents/${docId}`);
  },

  async deleteSynthesisDocument(docId: string): Promise<void> {
    await request(`/api/synthesis/documents/${docId}`, { method: 'DELETE' });
  },

  getSynthesisExportUrl(docId: string, format = 'markdown'): string {
    return `/api/synthesis/documents/${docId}/export?format=${format}`;
  },
};
