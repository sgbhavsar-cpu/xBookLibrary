"""Database schema definitions for Calibre metadata.db and xBookLibrary extensions."""

CALIBRE_SCHEMA_DDL = """
-- Calibre Standard Tables
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT 'Unknown',
    sort TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    pubdate DATETIME,
    series_index REAL DEFAULT 1.0,
    author_sort TEXT,
    isbn TEXT,
    lccn TEXT,
    path TEXT NOT NULL,
    flags INTEGER DEFAULT 1,
    uuid TEXT UNIQUE,
    has_cover INTEGER DEFAULT 0,
    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS books_idx ON books (sort COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sort TEXT,
    link TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS authors_idx ON authors (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS books_authors_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER NOT NULL,
    author INTEGER NOT NULL,
    FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(author) REFERENCES authors(id) ON DELETE CASCADE,
    UNIQUE(book, author)
);
CREATE INDEX IF NOT EXISTS bal_idx ON books_authors_link (book, author);

CREATE TABLE IF NOT EXISTS data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER NOT NULL,
    format TEXT NOT NULL,
    uncompressed_size INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE(book, format)
);
CREATE INDEX IF NOT EXISTS data_idx ON data (book, format);

CREATE TABLE IF NOT EXISTS identifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER NOT NULL,
    type TEXT NOT NULL,
    val TEXT NOT NULL,
    FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE(book, type)
);
CREATE INDEX IF NOT EXISTS id_idx ON identifiers (book, type);

CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sort TEXT
);

CREATE TABLE IF NOT EXISTS books_series_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER NOT NULL,
    series INTEGER NOT NULL,
    FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(series) REFERENCES series(id) ON DELETE CASCADE,
    UNIQUE(book, series)
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS books_tags_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER NOT NULL,
    tag INTEGER NOT NULL,
    FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(tag) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(book, tag)
);

CREATE TABLE IF NOT EXISTS publishers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sort TEXT
);
CREATE INDEX IF NOT EXISTS publishers_idx ON publishers (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS books_publishers_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER NOT NULL,
    publisher INTEGER NOT NULL,
    FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(publisher) REFERENCES publishers(id) ON DELETE CASCADE,
    UNIQUE(book, publisher)
);
CREATE INDEX IF NOT EXISTS bpl_idx ON books_publishers_link (book, publisher);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER NOT NULL UNIQUE,
    text TEXT,
    FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE
);

-- xBookLibrary Isolated Extension Tables (Calibre-safe)
CREATE TABLE IF NOT EXISTS x_toc_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    parent_id INTEGER,
    title TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 0,
    page_number INTEGER,
    anchor_href TEXT,
    order_index INTEGER NOT NULL,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_id) REFERENCES x_toc_nodes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS toc_book_idx ON x_toc_nodes (book_id, order_index);

CREATE TABLE IF NOT EXISTS x_file_hashes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    format TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS hash_idx ON x_file_hashes (sha256);

CREATE TABLE IF NOT EXISTS x_ingestion_jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    source_path TEXT,
    book_id INTEGER,
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    error_log TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

CREATE TABLE IF NOT EXISTS x_library_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- AI Classification & Dual Taxonomy Extension Tables
CREATE TABLE IF NOT EXISTS x_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL UNIQUE,
    bisac_code TEXT NOT NULL,
    bisac_heading TEXT NOT NULL,
    ddc_code TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    secondary_bisac TEXT,
    secondary_ddc TEXT,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS bisac_idx ON x_classifications (bisac_code);
CREATE INDEX IF NOT EXISTS ddc_idx ON x_classifications (ddc_code);

-- User Custom Hierarchical Taxonomy Tree
CREATE TABLE IF NOT EXISTS x_taxonomies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    FOREIGN KEY(parent_id) REFERENCES x_taxonomies(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS tax_path_idx ON x_taxonomies (path);

CREATE TABLE IF NOT EXISTS x_books_taxonomies_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    taxonomy_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(taxonomy_id) REFERENCES x_taxonomies(id) ON DELETE CASCADE,
    UNIQUE(book_id, taxonomy_id)
);
CREATE INDEX IF NOT EXISTS btl_tax_idx ON x_books_taxonomies_link (book_id, taxonomy_id);

-- Virtual Bookshelves
CREATE TABLE IF NOT EXISTS x_bookshelves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    is_smart INTEGER DEFAULT 0,
    rule_expression TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS x_books_bookshelves_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    bookshelf_id INTEGER NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(bookshelf_id) REFERENCES x_bookshelves(id) ON DELETE CASCADE,
    UNIQUE(book_id, bookshelf_id)
);
CREATE INDEX IF NOT EXISTS bbl_shelf_idx ON x_books_bookshelves_link (bookshelf_id, book_id);

-- Multi-Resolution AI Book Summaries
CREATE TABLE IF NOT EXISTS x_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL UNIQUE,
    executive_snapshot TEXT NOT NULL,
    chapters TEXT NOT NULL,
    conceptual_index TEXT NOT NULL,
    metadata TEXT NOT NULL,
    model_name TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    duration_seconds REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS summaries_book_idx ON x_summaries (book_id);

-- RAG Index Status & Checksum Tracking
CREATE TABLE IF NOT EXISTS x_index_status (
    book_id INTEGER PRIMARY KEY,
    library_id TEXT NOT NULL,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    checksum TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'indexed',
    error_message TEXT,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_x_index_status_library ON x_index_status (library_id);

-- Conversational Chat Sessions
CREATE TABLE IF NOT EXISTS x_chat_sessions (
    id TEXT PRIMARY KEY,
    library_id TEXT NOT NULL,
    book_id INTEGER,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_x_chat_sessions_library ON x_chat_sessions (library_id);

-- Conversational Chat Messages with Citations
CREATE TABLE IF NOT EXISTS x_chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations_json TEXT NOT NULL DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES x_chat_sessions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_x_chat_messages_session ON x_chat_messages (session_id);

-- Synthesized Research Documents & Knowledge Briefs
CREATE TABLE IF NOT EXISTS x_synthesis_documents (
    id TEXT PRIMARY KEY,
    library_id TEXT NOT NULL,
    title TEXT NOT NULL,
    template_type TEXT NOT NULL,
    topic_prompt TEXT NOT NULL,
    outline_json TEXT NOT NULL DEFAULT '[]',
    content_markdown TEXT NOT NULL,
    sources_json TEXT NOT NULL DEFAULT '[]',
    word_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_x_synthesis_documents_library ON x_synthesis_documents (library_id);
"""
