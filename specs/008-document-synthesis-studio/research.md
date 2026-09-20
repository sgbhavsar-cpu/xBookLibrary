# Research & Architectural Decisions: 008 Multi-Book Document Synthesis & Knowledge Brief Studio

**Feature**: 008 Multi-Book Document Synthesis & Knowledge Brief Studio  
**Date**: 2026-09-20  
**Status**: Completed  

---

## 1. Synthesis Pipeline Architecture: Single-Prompt vs. Multi-Stage Pipeline

### Decision
Implement a **4-Stage Hierarchical Synthesis Pipeline**:
1. **Stage 1 (Outline Generation)**: Analyzes the topic prompt and source book metadata to produce a structured outline:
   - Section Titles
   - Specific Research Questions per section
   - Targeted Search Keywords for evidence retrieval
2. **Stage 2 (Targeted Evidence Retrieval)**: Executes parallel hybrid search queries against the library's LanceDB vector store for each section, constrained to the user's selected `book_ids` (or bookshelf).
3. **Stage 3 (Grounded Section Drafting)**: For each section, prompts the LLM with the retrieved evidence passages and writes an analytical synthesis with strict inline citations: `[Book Title, Chapter Title]`.
4. **Stage 4 (Assembly & Bibliography)**: Compiles all drafted sections, injects an Executive Overview and Table of Contents, and builds a deduplicated, verified Bibliography of all cited books and chapters.

### Rationale
- Feeding 5 whole books directly into a single LLM prompt exceeds context windows, induces attention degradation ("lost in the middle"), and produces superficial summaries.
- A multi-stage pipeline breaks the complex research task into focused, verifiable sub-tasks. Each section is drafted with dedicated, high-relevance evidence chunks, producing rich, thesis-driven synthesis.

### Alternatives Considered
- *Single-shot whole-library prompt*: Context window overflows; lacks analytical depth and frequently hallucinates citations.
- *Map-Reduce concatenation*: Simply concatenates chapter summaries without synthesizing a unified comparative argument across different authors.

---

## 2. Document Templates & Synthesis Styles

### Decision
Support 4 specialized synthesis templates:
1. **Topic Brief (`topic_brief`)**: Comprehensive deep dive on a specific subject, blending theoretical foundations, historical evolution, and modern applications across authors.
2. **Literature Review (`literature_review`)**: Structured comparative analysis examining areas of consensus, core debates/disagreements, methodological differences, and unresolved questions.
3. **Executive Summary (`executive_summary`)**: High-density strategic brief focused on decision frameworks, core principles, and actionable takeaways.
4. **Custom Research (`custom_research`)**: Fully customizable structure adhering to user-provided outline or specific prompts.

---

## 3. Storage & Calibre Folder Standards

### Decision
Implement Dual Persistence adhering to Constitution Principle I (Self-Contained Portability):
- Relational metadata in SQLite (`metadata.db`): `x_synthesis_documents` table stores title, prompt, template, word count, sources, and timestamps.
- File artifact on disk: `<LibraryRoot>/.synthesis/<doc_id>.md`.
- Export formats:
  - Markdown (`.md`): Portable GitHub-flavored markdown with footnotes/citations.
  - Styled HTML (`.html`): Self-contained document with typography (Inter/Georgia), clean print CSS, and sidebar table of contents.
  - JSON: Machine-readable structured representation including sections, outline, and bibliography.

---

## 4. Background Execution & Progress Reporting

### Decision
Execute synthesis via asynchronous background tasks with stage progression:
- Stages: `initializing` (0%) -> `generating_outline` (20%) -> `retrieving_evidence` (40%) -> `drafting_sections` (70%) -> `assembling_document` (90%) -> `completed` (100%).
- Real-time job polling allows frontend progress bars to display current actions (e.g., "Drafting Section 2 of 4: Comparative Methodologies...").
