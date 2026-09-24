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
  sort_title?: string;
  author_sort?: string;
  publisher?: string;
  pubdate?: string;
  publication_year?: number;
  series?: string;
  series_name?: string;
  series_index?: number;
  rating?: number;
  tags: string[];
  isbn?: string;
  identifiers: Record<string, string>;
  comments?: string;
  description?: string;
  has_cover?: boolean;
  formats: BookFormat[];
  classification?: BookClassification;
  is_indexed?: boolean;
  custom_values?: Record<string, any>;
}

export type FilterState = 'include' | 'exclude';

// Category Key -> Item Key -> 'include' | 'exclude'
export type TagTreeFilter = Record<string, Record<string, FilterState>>;

export interface TagTreeNode {
  id: string;
  name: string;
  fullPath: string;
  count: number;
  category: string;
  children?: TagTreeNode[];
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
  key_points?: string[];
  key_takeaways?: string[];
  important_quotes?: string[];
}

export interface ExecutiveSnapshot {
  hook: string;
  core_thesis: string;
  target_audience: string;
  key_arguments: string[];
  estimated_reading_time_minutes: number;
}

export interface ConceptualIndex {
  frameworks?: string[];
  key_takeaways?: string[];
  quotable_moments?: Array<{ quote: string; source: string }>;
  action_items?: string[];
}

export interface BookSummary {
  id?: number;
  book_id: number;
  executive_snapshot?: ExecutiveSnapshot;
  chapters?: ChapterSummary[];
  conceptual_index?: ConceptualIndex;

  executive_summary?: string;
  detailed_summary?: string;
  key_takeaways?: string[];
  chapter_summaries?: ChapterSummary[];
  is_stale?: boolean;
  model_used?: string;
  generated_at?: string;
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

export interface ReadingProgress {
  id?: number;
  book_id: number;
  format: string;
  location: string;
  progress_percent: number;
  total_seconds: number;
  last_read_at?: string;
}

export interface ReadingProgressCreateRequest {
  format: string;
  location: string;
  progress_percent: number;
  seconds_increment?: number;
}

export interface Annotation {
  id: string;
  book_id: number;
  format: string;
  location: string;
  selected_text: string;
  color: string;
  note_text?: string;
  chapter_title?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AnnotationCreateRequest {
  format: string;
  location: string;
  selected_text: string;
  color?: string;
  note_text?: string;
  chapter_title?: string;
}

export interface Bookmark {
  id: string;
  book_id: number;
  format: string;
  location: string;
  title: string;
  created_at?: string;
}

export interface BookmarkCreateRequest {
  format: string;
  location: string;
  title: string;
}

export interface ComicPageInfo {
  index: number;
  filename: string;
  url: string;
}

export interface ComicManifest {
  book_id: number;
  total_pages: number;
  pages: ComicPageInfo[];
  series_name?: string;
  issue_number?: number;
}

export type DeviceType = 'kindle' | 'kobo' | 'koreader' | 'usb';
export type DeviceSyncStatus = 'pending' | 'in_flight' | 'completed' | 'failed';

export interface Device {
  id: string;
  name: string;
  device_type: DeviceType;
  target_address?: string;
  auth_token?: string;
  created_at: string;
  last_sync_at?: string;
}

export interface DeviceCreateRequest {
  name: string;
  device_type: DeviceType;
  target_address?: string;
}

export interface DeviceSyncLog {
  id: string;
  book_id: number;
  book_title: string;
  device_id?: string;
  device_type: DeviceType;
  format_sent: string;
  status: DeviceSyncStatus;
  error_message?: string;
  created_at: string;
}

export interface SendToDeviceRequest {
  device_id?: string;
  custom_recipient?: string;
  preferred_format?: string;
}

export interface ExportToDirectoryRequest {
  target_directory: string;
  format?: string;
}

export interface SMTPSettings {
  host: string;
  port: number;
  username: string;
  password?: string;
  use_tls: boolean;
  use_ssl: boolean;
  sender_email: string;
}

export interface AudioChapter {
  index: number;
  title: string;
  start_time: number;
  end_time: number;
  duration: number;
}

export interface AudiobookMetadata {
  book_id: number;
  format: string;
  duration_seconds: number;
  bitrate?: number;
  sample_rate?: number;
  channels?: number;
  narrator?: string;
  chapters: AudioChapter[];
}

export interface AudioListeningProgress {
  book_id: number;
  format: string;
  current_time: number;
  current_chapter_index: number;
  progress_percent: number;
  playback_speed: number;
  is_finished: boolean;
  last_listened_at?: string;
}

export interface AudioListeningProgressUpdateRequest {
  current_time: number;
  current_chapter_index?: number;
  progress_percent?: number;
  playback_speed?: number;
}

export interface AudioTranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export interface AudioChapterTranscript {
  id: string;
  book_id: number;
  chapter_index: number;
  chapter_title: string;
  start_time: number;
  end_time: number;
  transcript_text: string;
  segments: AudioTranscriptSegment[];
  model_used: string;
  status: string;
  created_at?: string;
}

export interface AudioPlaybackState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  playbackSpeed: number;
  volume: number;
  currentChapterIndex: number;
}

export interface BookMetadataUpdateRequest {
  title?: string;
  sort_title?: string;
  authors?: string[];
  author_sort?: string;
  publisher?: string;
  pubdate?: string;
  rating?: number;
  tags?: string[];
  series_name?: string;
  series_index?: number;
  isbn?: string;
  identifiers?: Record<string, string>;
  comments?: string;
  custom_values?: Record<string, any>;
}

export interface OnlineMetadataCandidate {
  source: string; // "google_books" | "openlibrary"
  title: string;
  authors: string[];
  publisher?: string;
  published_date?: string;
  description?: string;
  isbn?: string;
  identifiers: Record<string, string>;
  cover_url?: string;
  rating?: number;
  tags: string[];
  confidence_score: number;
}

export interface OnlineMetadataSearchRequest {
  title?: string;
  author?: string;
  isbn?: string;
}

export interface BulkMetadataUpdateRequest {
  book_ids: number[];
  add_tags?: string[];
  remove_tags?: string[];
  set_author?: string;
  set_publisher?: string;
  set_rating?: number;
  set_series?: string;
  auto_increment_series?: boolean;
  series_start_index?: number;
}

export interface BulkMetadataUpdateResult {
  total_requested: number;
  updated_count: number;
  failed_ids: number[];
  errors: string[];
}

export interface FormatAddResponse {
  book_id: number;
  format: string;
  file_path: string;
  uncompressed_size: number;
  formats: string[];
}

export interface FormatDeleteResponse {
  book_id: number;
  deleted_format: string;
  remaining_formats: string[];
}

export interface UserPreferences {
  theme: string;
  default_page_size: number;
  default_format: string;
  view_mode: string;
  active_ai_provider: 'gemini' | 'openai' | 'ollama';
  gemini_api_key?: string;
  openai_api_key?: string;
  ollama_endpoint?: string;
  ollama_model?: string;
  embedding_model?: string;
  auto_import_folder?: string;
  auto_import_enabled: boolean;
  auto_import_action: 'skip' | 'create_new' | 'merge';
  delete_source_after_import?: boolean;
  auto_download_metadata?: boolean;
  auto_index_rag?: boolean;
  auto_generate_summary?: boolean;
  opds_enabled: boolean;
  opds_port: number;
  smtp_settings?: {
    host: string;
    port: number;
    username?: string;
    password?: string;
    use_tls: boolean;
    use_ssl: boolean;
    sender_email?: string;
  };
}

export interface TestAIConnectionResponse {
  success: boolean;
  provider: string;
  message: string;
  available_models: string[];
}

export interface ScanDropFolderResponse {
  success: boolean;
  folder_scanned: string;
  jobs_count: number;
  files_processed: string[];
  message: string;
}


