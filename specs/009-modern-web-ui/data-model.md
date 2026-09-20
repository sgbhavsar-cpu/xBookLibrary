# Data Model: 009 Modern 3-Pane Calibre Web UI & Reader

## 1. Frontend Domain Entities

### 1.1 Book & Catalog Models
```ts
export interface BookAuthor {
  id: number;
  name: string;
  sort?: string;
}

export interface BookFormat {
  format: string; // "EPUB", "PDF", "MOBI", "CBZ", "DOCX"
  uncompressed_size: number;
  name: string;
}

export interface BookClassification {
  bisac_code: string;
  bisac_heading: string;
  ddc_code: string;
  confidence: number;
  reasoning?: string;
}

export interface Book {
  id: number;
  title: string;
  authors: string[];
  sort?: string;
  pubdate?: string;
  series?: string;
  series_index?: number;
  rating?: number;
  tags: string[];
  identifiers: Record<string, string>; // e.g. {"isbn": "...", "doi": "..."}
  comments?: string; // HTML description
  cover_url?: string;
  formats: BookFormat[];
  classification?: BookClassification;
  is_indexed?: boolean;
}
```

### 1.2 Taxonomy & Hierarchy Models
```ts
export interface TaxonomyNode {
  id: number;
  parent_id?: number;
  name: string;
  path: string; // e.g., "Computer Science/Artificial Intelligence"
  description?: string;
  order_index: number;
  book_count?: number;
  children?: TaxonomyNode[];
}
```

### 1.3 Multi-Resolution Summary Models
```ts
export interface ChapterSummary {
  chapter_index: number;
  chapter_title: string;
  summary: string;
  key_points: string[];
}

export interface BookSummaryData {
  executive_summary?: string;
  detailed_summary?: string;
  key_takeaways?: string[];
  chapter_summaries?: ChapterSummary[];
  generated_at?: string;
}
```

### 1.4 RAG & Chat Models
```ts
export interface ChatCitation {
  book_id: number;
  book_title: string;
  authors: string;
  chapter_title: string;
  chapter_index: number;
  snippet: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: ChatCitation[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  library_id: string;
  book_id?: number;
  title: string;
  created_at: string;
  updated_at: string;
}
```

### 1.5 Document Synthesis Models
```ts
export interface SynthesisSource {
  book_id: number;
  book_title: string;
  authors: string;
  chapters_cited: string[];
}

export interface SynthesisDocument {
  id: string;
  library_id: string;
  title: string;
  template_type: 'topic_brief' | 'literature_review' | 'executive_summary' | 'custom_research';
  topic_prompt: string;
  outline: string[];
  content_markdown: string;
  sources: SynthesisSource[];
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface SynthesisJobStatus {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  stage: string;
  percent_complete: number;
  document_id?: string;
  error?: string;
}
```

### 1.6 Reader Session State
```ts
export interface ReaderSettings {
  theme: 'light' | 'sepia' | 'dark' | 'black';
  fontFamily: 'system' | 'serif' | 'sans-serif' | 'dyslexic';
  fontSize: number; // in pt / px
  lineHeight: number;
  margin: number;
}

export interface BookReadingProgress {
  bookId: number;
  format: string;
  locationCfi?: string;
  pageNumber?: number;
  totalPages?: number;
  percentComplete: number;
  currentChapter?: string;
  lastReadAt: string;
}
```
