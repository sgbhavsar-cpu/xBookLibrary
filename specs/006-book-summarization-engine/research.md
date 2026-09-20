# Research & Architecture Decisions: Multi-Resolution AI Book Summarization Engine

**Feature**: `006-book-summarization-engine`  
**Status**: Completed  
**Date**: 2026-09-20  

---

## 1. Summarization Pipeline Strategy (Map-Reduce vs. Long Context)

### Decision
Adopt a **Hierarchical Map-Reduce Pipeline** with Chapter-Level Processing as the primary architecture, paired with an automatic Single-Pass optimization for short works (< 3,000 words).

### Rationale
1. **Model Agnostic & Token Window Resilience**:
   - While modern cloud models like Gemini 2.5 Flash support up to 1M tokens, local models running via Ollama (e.g., Llama 3 8B, Mistral 7B) typically operate within 8k–32k token windows.
   - Chapter-level chunking ensures the engine runs flawlessly across all LLM providers configured in `LiteLLMClientAdapter`.
2. **Granular Structural Fidelity**:
   - Summarizing the whole book at once tends to blur chapter boundaries, losing specific chapter takeaways, quotes, and structural narrative progression.
   - Processing chapter-by-chapter guarantees that every single chapter receives an explicit summary and key takeaways.
3. **Synthesis / Reduce Stage**:
   - The reduce phase compiles the structured chapter summaries and prompts the model to generate the overarching `ExecutiveSnapshot` and `ConceptualIndex`.

### Alternatives Considered
- **Single-Pass Full Text Prompt**: Simple to implement for large-window models, but fails on local Ollama setups, costs significantly more tokens on re-runs, and yields shallow chapter breakdowns.
- **Pure Sliding-Window Chunking**: Ignores table of contents and chapter semantic boundaries, splitting sentences and paragraphs across arbitrary token counts. Rejected in favor of chapter-aware parsing.

---

## 2. Storage & Portability Architecture

### Decision
Store summaries using a **Dual-Persistence Pattern**:
1. **Physical JSON Artifact**: `<LibraryRoot>/<Author>/<Title> (<Year>)/summary.json`
2. **Relational Index**: SQLite table `x_summaries` in `metadata.db`

### Rationale
- **Calibre Portability (Constitution Principle I)**:
  - If a user copies their library folder to another machine, backs it up via cloud drive, or opens it on another instance of xBookLibrary, the complete summary is instantly available without needing to re-run AI inference.
- **Fast UI & API Querying**:
  - The `x_summaries` table provides instantaneous lookups (< 10ms) without needing to inspect file systems or parse JSON files on each request.
- **Calibre OPF Sync**:
  - Optionally update Calibre's native `comments` table and `<dc:description>` in `metadata.opf` with the 2-minute Executive Snapshot so classic Calibre and mobile e-readers display the executive summary natively.

### Alternatives Considered
- **Database-Only Storage**: Fails portability; moving the book folder leaves the summaries behind.
- **File-Only Storage**: Slow querying when rendering bookshelf overviews or searching across multiple book summaries.

---

## 3. Asynchronous Job Tracking & Resilience

### Decision
Integrate with the existing `JobWorker` system (`backend/services/job_worker.py`), recording progress as `progress_percent`, `current_step`, and chapter metadata.

### Rationale
- For books with 20–40 chapters, summarization can take 30–90 seconds.
- Background execution allows the client to poll `/api/jobs/{job_id}` or receive WebSocket/SSE updates without blocking HTTP connections.
- Chapter-level checkpointing allows the worker to resume or skip transient errors with exponential backoff if a rate limit is hit.

---

## 4. Summary Schema & Formats

### Decision
Define a strict Pydantic v2 domain model hierarchy:
- `BookSummary`:
  - `book_id: int`
  - `executive_snapshot: ExecutiveSnapshot` (hook, core_thesis, target_audience, key_arguments, estimated_reading_time_minutes)
  - `chapters: List[ChapterSummary]` (chapter_index, chapter_title, summary, key_takeaways, important_quotes)
  - `conceptual_index: ConceptualIndex` (frameworks, key_takeaways, quotable_moments, action_items)
  - `metadata: SummaryMetadata` (model_name, word_count, duration_seconds, generated_at, prompt_version)

Export formats:
- **JSON**: Direct serialization of `BookSummary`.
- **Markdown**: Formatted document with clean typography, bullet points, and blockquotes.
- **HTML**: Self-contained styled HTML suitable for reading or printing.
