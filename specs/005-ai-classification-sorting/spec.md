# Feature Specification: AI Classification & Taxonomy Sorting

**Feature Branch**: `005-ai-classification-sorting`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: User description: "AI based classification system while importing book, agentic meta data update before classification and sorting, create library wise RAG so that chat bot agent can answer questions from books of that library"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dual-Taxonomy Standard Classification (BISAC & Dewey Decimal) (Priority: P1)

As a library curator or reader, when a book is added or enriched in the library, I want the system to automatically analyze its title, description, subjects, and table of contents to assign an accurate BISAC Subject Code (and heading) and a Dewey Decimal Classification (DDC) number, so that my library adheres to universal bibliographic cataloging standards.

**Why this priority**: Universal standards (BISAC / DDC) provide a consistent, objective baseline across heterogeneous collections and enable standardized sorting across reading applications and Calibre metadata.

**Independent Test**:
- Ingest a technical book (e.g., *Designing Data-Intensive Applications*) or novel (e.g., *Dune*).
- Trigger classification.
- Assert that the book receives a verified BISAC code (e.g., `COM051010` / `FIC028000`) and a valid 3-digit/decimal DDC notation (e.g., `005.74` / `813.54`).

**Acceptance Scenarios**:
1. **Given** a book with bibliographic metadata (title, author, synopsis, TOC), **When** automated classification executes, **Then** the system outputs a primary BISAC subject heading, BISAC alphanumeric code, and a Dewey Decimal number with classification confidence score.
2. **Given** a book with ambiguous or minimal metadata, **When** classification runs, **Then** the LLM analyzer samples the first 3 chapters / TOC nodes from the book file to infer the correct subject classification.

---

### User Story 2 - User-Defined Custom Taxonomy & Virtual Bookshelves (Priority: P2)

As a power user with personalized reading interests, I want to define custom hierarchical category trees (e.g., `Technology > Systems > Distributed Computing` or `Philosophy > Stoicism`) and virtual bookshelves (e.g., `Currently Reading`, `Deep Work Reference`, `Sci-Fi Classics`), so that books are automatically sorted into my personal organization framework without altering their physical Calibre directory structure.

**Why this priority**: Real users organize libraries according to personal workflows, projects, and custom genres rather than purely rigid cataloging numbers.

**Independent Test**:
- Create a custom taxonomy tree with parent-child categories via API.
- Classify a book against the active library's custom taxonomy.
- Assert that the book is associated with the top-matching taxonomy node and assigned to relevant virtual bookshelves.

**Acceptance Scenarios**:
1. **Given** a custom taxonomy tree defined in the active library, **When** a book is classified, **Then** the system assigns the book to the most relevant leaf and ancestor taxonomy nodes with confidence ratings.
2. **Given** a virtual bookshelf rule (e.g., "All books tagged DDC 005.x or BISAC COMPUTERS"), **When** books are classified or queried, **Then** virtual bookshelves dynamically group them without moving files on disk.

---

### User Story 3 - High-Precision Tag Refinement & Staged Diff Approval (Priority: P3)

As a reader who values tidy library tags, I want the AI classifier to generate 3 to 6 high-precision, non-redundant semantic tags (filtering out generic noise like "ebook" or "general"), and present any low-confidence classification changes as a visual diff proposal for approval before applying.

**Why this priority**: Prevents tag pollution in `metadata.db` while upholding Principle III (Human-in-the-Loop Safeguards) for uncertain classifications.

**Independent Test**:
- Classify a book where confidence is below the auto-apply threshold (e.g., 0.85).
- Verify that a classification proposal is staged in `.vectors/staging/` and not applied immediately to Calibre SQLite.
- Approve the proposal and verify that Calibre tags and classification extension tables are updated.

**Acceptance Scenarios**:
1. **Given** classification confidence is >= 0.85 and auto-apply is enabled, **When** classification completes, **Then** the tags and taxonomy links are immediately committed to SQLite and `metadata.opf`.
2. **Given** classification confidence is < 0.85, **When** classification completes, **Then** a classification proposal is saved in `.vectors/staging/<proposal_id>.json` for user review.

---

### User Story 4 - REST API Endpoints for Classification & Taxonomies (Priority: P4)

As a developer or frontend client (React 3-Pane UI), I want REST API endpoints to manage taxonomy trees, create virtual bookshelves, trigger book classifications, and inspect/approve classification proposals.

**Why this priority**: Exposes all classification and taxonomy capabilities cleanly to the forthcoming React 19 UI workspace.

**Independent Test**:
- Execute contract tests against `/api/taxonomies`, `/api/bookshelves`, and `/api/books/{id}/classify`.

**Acceptance Scenarios**:
1. **POST** `/api/books/{id}/classify` triggers classification and returns classification result (applied or staged).
2. **GET** `/api/taxonomies` returns the active library's hierarchical category tree.
3. **POST** `/api/taxonomies` creates or updates category nodes.
4. **GET** `/api/bookshelves` returns virtual bookshelves with member book counts.

---

## Edge Cases

- **Non-English Books**: The classifier prompts the LLM to identify the book language and assign universal DDC numbers and English-standard BISAC headings while preserving local language subject tags.
- **Multidisciplinary / Anthology Works**: When a book spans multiple disciplines, the classifier assigns one primary BISAC/DDC and up to two secondary subjects.
- **Novel / Unrepresented Genres in Custom Taxonomy**: If a book does not fit any user custom taxonomy category above a 0.50 confidence threshold, it is placed in an "Uncategorized" bucket and prompts the user to suggest a new category node.
- **Offline / No LLM Key Configured**: When no external API key is present and Ollama is unreachable, classification falls back to heuristic keyword matching against an offline embedded lookup table of the top 500 BISAC and top 100 DDC categories based on existing book tags and title words.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a primary BISAC subject heading and 9-character code for any ingested/enriched book.
- **FR-002**: System MUST assign a 3-digit (plus decimal expansion where appropriate) Dewey Decimal Classification (DDC) number for each book.
- **FR-003**: System MUST support a hierarchical custom taxonomy tree per library stored in isolated extension tables (`x_taxonomies`, `x_books_taxonomies_link`) that never alters native Calibre tables.
- **FR-004**: System MUST support virtual bookshelves (`x_bookshelves`, `x_books_bookshelves_link`) allowing many-to-many book grouping without touching physical file locations.
- **FR-005**: System MUST generate 3 to 6 high-specificity semantic tags and merge them into the Calibre `tags` and `books_tags_link` tables.
- **FR-006**: System MUST uphold Principle III safeguards: classifications with composite confidence < 0.85 MUST be staged in `.vectors/staging/` as diff proposals requiring user approval.
- **FR-007**: System MUST provide an offline heuristic classifier fallback when no external LLM API key or local Ollama daemon is reachable.
- **FR-008**: System MUST update `metadata.opf` with `<dc:subject>` tags and custom Calibre user metadata fields for BISAC and DDC when approved.

### Key Entities

- **ClassificationResult**: Represents the computed classification output:
  - `bisac_code`: str (e.g. `COM051010`)
  - `bisac_heading`: str (e.g. `COMPUTERS / Programming / Software Development`)
  - `ddc_code`: str (e.g. `005.1`)
  - `confidence`: float (0.0 to 1.0)
  - `suggested_tags`: List[str]
  - `custom_category_id`: Optional[int]
- **TaxonomyNode**: Represents a node in the user's category tree:
  - `id`: int
  - `parent_id`: Optional[int]
  - `name`: str
  - `description`: Optional[str]
  - `path`: str (e.g. `/Technology/Artificial Intelligence/LLMs`)
  - `order_index`: int
- **Bookshelf**: Represents a virtual shelf:
  - `id`: int
  - `name`: str
  - `description`: Optional[str]
  - `icon`: Optional[str]
  - `rule_expression`: Optional[str] (optional dynamic filter)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90%+ of cataloged books receive an accurate primary BISAC and DDC code matching standard library catalog records.
- **SC-002**: Classification execution takes under 3 seconds per book when using cached metadata or under 10 seconds when LLM content sampling is required.
- **SC-003**: 100% Calibre backward compatibility: native Calibre desktop application opens `metadata.db` without errors or missing data.
- **SC-004**: Zero silent misclassifications: all low-confidence suggestions (< 0.85) are cleanly routed to staging for human review.

---

## Assumptions

- Standard BISAC and Dewey Decimal top-level taxonomy definitions can be bundled locally as embedded reference dictionaries for fast prompt grounding and offline heuristic fallback.
- The Calibre `metadata.db` schema will be extended only with isolated `x_*` tables (`x_taxonomies`, `x_books_taxonomies_link`, `x_bookshelves`, `x_books_bookshelves_link`, `x_classifications`), leaving native tables untouched.
- Users can choose whether high-confidence classifications auto-apply or always prompt for review via library preferences.
