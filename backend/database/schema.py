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
"""
