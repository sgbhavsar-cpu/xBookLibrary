# Data Model: Multi-Resolution AI Book Summarization Engine

**Feature**: `006-book-summarization-engine`  
**Status**: Completed  
**Date**: 2026-09-20  

---

## 1. Domain Entities (`backend/domain/summary.py`)

### `ExecutiveSnapshot`
Represents the top-level 2-minute synthesis of the book.
- `hook`: `str` — Single compelling sentence capturing the essence of the work.
- `core_thesis`: `str` — Central argument, problem solved, or primary narrative premise.
- `target_audience`: `str` — Who benefits most from reading this book.
- `key_arguments`: `List[str]` — 3 to 5 core high-level takeaways or conclusions.
- `estimated_reading_time_minutes`: `int` — Estimated reading time for the full original work.

### `ChapterSummary`
Represents the analytical breakdown of an individual chapter or section.
- `chapter_index`: `int` — Sequential chapter position (1-based index).
- `chapter_title`: `str` — Heading or title of the chapter/section.
- `summary`: `str` — Narrative synthesis of the chapter's core progression.
- `key_takeaways`: `List[str]` — Specific learnings, principles, or plot milestones.
- `important_quotes`: `List[str]` — Direct or notable excerpts from the chapter.

### `ConceptualIndex`
Represents the conceptual models, mental frameworks, and actionable applications.
- `frameworks`: `List[str]` — Named theories, mental models, or structured methodologies.
- `key_takeaways`: `List[str]` — Overarching high-impact insights.
- `quotable_moments`: `List[Dict[str, str]]` — Curated quotes with chapter/section attribution (`{"quote": str, "source": str}`).
- `action_items`: `List[str]` — Practical steps, advice, or exercises extracted from the book.

### `SummaryMetadata`
Metadata tracking model execution and audit trail.
- `model_name`: `str` — e.g. `gemini/gemini-2.5-flash` or `ollama/llama3`.
- `generated_at`: `datetime` — Timestamp when summary was created.
- `duration_seconds`: `float` — Execution duration.
- `word_count`: `int` — Total word count of the summarized book text.
- `prompt_version`: `str` — Identifier for prompt template used (default: `v1.0`).
- `custom_instructions`: `Optional[str]` — User-specified prompt focus, if any.

### `BookSummary`
Aggregate root entity encompassing all tiers.
- `book_id`: `int` — ID of the book in Calibre SQLite.
- `executive_snapshot`: `ExecutiveSnapshot`
- `chapters`: `List[ChapterSummary]`
- `conceptual_index`: `ConceptualIndex`
- `metadata`: `SummaryMetadata`

---

## 2. Database Schema (`x_summaries` in `backend/database/schema.py`)

```sql
CREATE TABLE IF NOT EXISTS x_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    executive_snapshot TEXT NOT NULL,  -- JSON serialized ExecutiveSnapshot
    chapters TEXT NOT NULL,            -- JSON serialized List[ChapterSummary]
    conceptual_index TEXT NOT NULL,    -- JSON serialized ConceptualIndex
    metadata TEXT NOT NULL,            -- JSON serialized SummaryMetadata
    model_name TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    duration_seconds REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_x_summaries_book_id ON x_summaries(book_id);
```

---

## 3. Physical Storage (`summary.json`)

Stored alongside the book files in the Calibre directory:
```
<LibraryRoot>/
  <Author>/
    <Title> (<Year>)/
      ├── book.epub
      ├── cover.jpg
      ├── metadata.opf
      └── summary.json
```

Example `summary.json`:
```json
{
  "book_id": 42,
  "executive_snapshot": {
    "hook": "An essential guide to the principles of quantum computation.",
    "core_thesis": "Quantum mechanics fundamentally expands computational complexity classes.",
    "target_audience": "Computer scientists, physicists, and engineers.",
    "key_arguments": [
      "Superposition enables exponential state representation.",
      "Entanglement allows non-local quantum correlations.",
      "Quantum error correction is mathematically viable."
    ],
    "estimated_reading_time_minutes": 380
  },
  "chapters": [
    {
      "chapter_index": 1,
      "chapter_title": "Introduction to Qubits",
      "summary": "Explores the Bloch sphere representation of single-qubit states...",
      "key_takeaways": [
        "Qubits exist in linear combinations of basis states |0> and |1>.",
        "Measurement collapses the state probabilistically."
      ],
      "important_quotes": [
        "Quantum information is physical information."
      ]
    }
  ],
  "conceptual_index": {
    "frameworks": ["Bloch Sphere Representation", "Shor's Algorithm"],
    "key_takeaways": ["Quantum gates are unitary operators."],
    "quotable_moments": [
      {"quote": "Quantum computing is not just faster computing.", "source": "Chapter 1"}
    ],
    "action_items": ["Implement simulation of Hadamard gate in matrix form."]
  },
  "metadata": {
    "model_name": "gemini-2.5-flash",
    "generated_at": "2026-09-20T12:00:00Z",
    "duration_seconds": 14.2,
    "word_count": 48200,
    "prompt_version": "v1.0"
  }
}
```
