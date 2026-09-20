# Research: AI Classification & Taxonomy Sorting

**Feature**: `005-ai-classification-sorting`  
**Date**: 2026-09-20  

---

## Technical Context & Decisions

### Decision 1: Dual Taxonomy Standardization (BISAC & Dewey Decimal)
- **Problem**: Books in personal libraries arrive with disparate, messy tags (e.g. "computers", "programming", "sci-fi", "dune", "paperback"). Automated cataloging requires consistent, globally recognized classification standards.
- **Decision**: Adopt Dual Taxonomy:
  1. **BISAC (Book Industry Standards and Communications)**: 9-character code (e.g., `COM051010`) and hierarchical heading (e.g., `COMPUTERS / Programming / Software Development`).
  2. **DDC (Dewey Decimal Classification)**: 3-digit notation with decimal expansion (e.g., `005.1` or `813.54`).
- **Rationale**:
  - BISAC provides industry-standard commercial subject categorization used by major bookstores and distributors.
  - DDC provides universal academic and public library shelf placement notation.
  - Together, they offer both modern commercial genre clarity and classical cataloging rigor.
- **Alternatives Considered**:
  - *Library of Congress Classification (LCC)*: Evaluated, but LCC is predominantly used by US research universities and is less intuitive for general readers than DDC.
  - *Pure dynamic clustering / embeddings only*: Too opaque for users who want readable genres and shelf names.

---

### Decision 2: Storage Architecture & Calibre Backward Compatibility
- **Problem**: Must store BISAC, DDC, custom category trees, and virtual bookshelves without altering Calibre's native tables (`books`, `tags`, `series`).
- **Decision**: Store classifications and custom taxonomies in isolated `x_*` extension tables in the library's `metadata.db`:
  - `x_classifications`: `(id, book_id, bisac_code, bisac_heading, ddc_code, confidence, created_at)`
  - `x_taxonomies`: `(id, parent_id, name, path, description, order_index)`
  - `x_books_taxonomies_link`: `(id, book_id, taxonomy_id, confidence)`
  - `x_bookshelves`: `(id, name, description, icon, is_smart, rule_expression)`
  - `x_books_bookshelves_link`: `(id, book_id, bookshelf_id)`
  - In addition, the primary BISAC heading and DDC code are injected as standard tags in Calibre (`tags` and `books_tags_link`) and `<dc:subject>` entries in `metadata.opf` so native Calibre desktop applications immediately show them.
- **Rationale**: Completely adheres to Principle I (Self-Contained Portable Library Isolation) and preserves 100% Calibre 7.x backward compatibility.

---

### Decision 3: Classifier Engine Architecture & Offline Fallback
- **Problem**: Need high-accuracy classification using available LLMs, while remaining operational if offline or unauthenticated.
- **Decision**:
  - **Online / LLM Mode**: Utilize `LiteLLMClientAdapter` (Gemini 2.0 Flash or local Ollama `llama3.2-vision` / `llama3.2`) with structured JSON schema output specifying primary and secondary BISAC and DDC.
  - **Context Window Sampling**: For books with sparse metadata, extract TOC outline and first 3 chapter headings / introductory paragraphs (via existing parser suite).
  - **Offline Heuristic Fallback**: Embed a compact lookup dictionary of top 500 BISAC subjects and top 100 Dewey Decimal divisions. If no LLM is configured or reachable, use token frequency and keyword similarity against book title, author, and existing tags.
- **Rationale**: Guarantees zero downtime or ingestion blocking even in air-gapped or offline development environments.

---

### Decision 4: Principle III Safeguards & Staged Review Threshold
- **Problem**: Inaccurate classification could misplace books or clutter virtual bookshelves.
- **Decision**: Enforce a confidence threshold:
  - Composite Confidence >= 0.85: Auto-applied (if auto-apply enabled in user settings).
  - Composite Confidence < 0.85: Generates an ephemeral classification proposal in `.vectors/staging/<proposal_id>.json` for visual diff inspection and one-click user approval.
- **Rationale**: Fully compliant with Principle III (Human-in-the-Loop Safeguards).
