/**
 * TypeScript definitions for xBookLibrary frontend domain entities.
 */

export interface Library {
  id: string;
  name: string;
  path: string;
  is_calibre_adopted: boolean;
  book_count: number;
  created_at: string;
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
  secondary_bisac?: string;
  secondary_ddc?: string;
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
  identifiers: Record<string, string>;
  comments?: string;
  has_cover?: boolean;
  formats: BookFormat[];
  classification?: BookClassification;
  is_indexed?: boolean;
  custom_values?: Record<string, any>;
}

export interface TaxonomyNode {
  id: number;
  parent_id?: number;
  name: string;
  path: string;
  description?: string;
  order_index: number;
  book_count?: number;
  children?: TaxonomyNode[];
}

export interface ChapterSummary {
  chapter_index: number;
  chapter_title: string;
  summary: string;
  key_points: string[];
}

export interface BookSummary {
  book_id: number;
  executive_summary: string;
  detailed_summary: string;
  key_takeaways: string[];
  chapter_summaries: ChapterSummary[];
  is_stale: boolean;
  model_used: string;
  generated_at: string;
}

export interface ChatCitation {
  chunk_id: string;
  book_id: number;
  book_title: string;
  authors: string;
  chapter_title: string;
  chapter_index: number;
  content: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: ChatCitation[];
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

export interface IngestionJob {
  id: string;
  status: string;
  source_path?: string;
  book_id?: number;
  total_files: number;
  processed_files: number;
  error_log?: string;
  created_at: string;
  completed_at?: string;
}

export interface MetadataProposal {
  id: string;
  book_id: number;
  source: string;
  confidence: number;
  proposed_metadata: {
    title?: string;
    authors?: string[];
    description?: string;
    tags?: string[];
    isbn?: string;
    publisher?: string;
    pubdate?: string;
  };
  current_metadata: {
    title?: string;
    authors?: string[];
    description?: string;
    tags?: string[];
    isbn?: string;
    publisher?: string;
    pubdate?: string;
  };
  created_at: string;
}

export interface ConversionJob {
  id: string;
  book_id: number;
  library_id: string;
  source_format: string;
  target_format: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  percent_complete: number;
  engine_used?: 'calibre_cli' | 'python_native';
  output_file_path?: string;
  output_size_bytes?: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  logs: string[];
}

export interface ConversionRequest {
  book_id: number;
  source_format?: string;
  target_format: string;
  options?: Record<string, any>;
}

export type CustomColumnDatatype =
  | 'enumeration'
  | 'int'
  | 'float'
  | 'bool'
  | 'text'
  | 'comments'
  | 'rating'
  | 'series';

export interface CustomColumnDefinition {
  id: number;
  label: string;
  name: string;
  datatype: CustomColumnDatatype;
  is_multiple: boolean;
  normalized: boolean;
  display: Record<string, any>;
  editable: boolean;
}

export interface BookCustomValues {
  book_id: number;
  values: Record<string, any>;
}

export interface SeriesInfo {
  id?: number;
  name: string;
  series_index: number;
  book_count?: number;
}

export interface VirtualLibrary {
  name: string;
  query: string;
  book_count?: number;
  description?: string;
}

