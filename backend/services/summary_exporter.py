"""Export formatters (Markdown, HTML) and Calibre OPF synchronization for book summaries."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

import aiosqlite

from backend.domain.summary import BookSummary
from backend.services.storage_service import StorageService


class SummaryExporter:
    """Formats multi-resolution summaries for export and syncs executive notes with Calibre."""

    def __init__(self, library_root: Optional[Path] = None):
        self.library_root = library_root
        self.db_path = (library_root / "metadata.db") if library_root else None
        self.storage = StorageService(library_root) if library_root else None

    def export_markdown(self, summary: BookSummary, book_title: str, authors: List[str]) -> str:
        """Formats the multi-resolution summary into clean, readable Markdown."""
        author_str = ", ".join(authors) if authors else "Unknown"
        es = summary.executive_snapshot
        ci = summary.conceptual_index

        lines = [
            f"# {book_title}",
            f"**Authors**: {author_str}  ",
            f"**Estimated Reading Time**: ~{es.estimated_reading_time_minutes} minutes  ",
            "",
            "## Executive Snapshot",
            f"> {es.hook}",
            "",
            f"**Core Thesis**: {es.core_thesis}  ",
            f"**Target Audience**: {es.target_audience}",
            "",
            "### Key Arguments",
        ]
        for arg in es.key_arguments:
            lines.append(f"- {arg}")

        lines.extend(["", "## Chapter-by-Chapter Synthesis", ""])
        for chap in summary.chapters:
            lines.append(f"### Chapter {chap.chapter_index}: {chap.chapter_title}")
            lines.append(f"{chap.summary}\n")
            if chap.key_takeaways:
                lines.append("**Key Takeaways**:")
                for kt in chap.key_takeaways:
                    lines.append(f"- {kt}")
                lines.append("")
            if chap.important_quotes:
                lines.append("**Notable Quotes**:")
                for q in chap.important_quotes:
                    lines.append(f'> "{q}"')
                lines.append("")

        lines.extend(["## Conceptual Index & Action Items", "", "### Frameworks & Mental Models"])
        for fw in ci.frameworks:
            lines.append(f"- **{fw}**")

        lines.extend(["", "### Key Takeaways"])
        for kt in ci.key_takeaways:
            lines.append(f"- {kt}")

        if ci.quotable_moments:
            lines.extend(["", "### Quotable Moments"])
            for qm in ci.quotable_moments:
                q_text = qm.get("quote", "")
                q_src = qm.get("source", "Unknown")
                lines.append(f'> "{q_text}" — *{q_src}*')

        if ci.action_items:
            lines.extend(["", "### Practical Action Items"])
            for ai in ci.action_items:
                lines.append(f"1. {ai}")

        lines.extend(
            [
                "",
                "---",
                (
                    f"*Generated with {summary.metadata.model_name} "
                    f"in {summary.metadata.duration_seconds}s.*"
                ),
            ]
        )
        return "\n".join(lines)

    def export_html(self, summary: BookSummary, book_title: str, authors: List[str]) -> str:
        """Formats the summary as an attractive, standalone HTML document."""
        author_str = ", ".join(authors) if authors else "Unknown"
        es = summary.executive_snapshot
        ci = summary.conceptual_index

        args_html = "".join(f"<li>{arg}</li>" for arg in es.key_arguments)
        chaps_html = "".join(
            f'<div class="chapter"><h3>Chapter {c.chapter_index}: {c.chapter_title}</h3>'
            f"<p>{c.summary}</p></div>"
            for c in summary.chapters
        )
        fw_html = "".join(f"<li><strong>{fw}</strong></li>" for fw in ci.frameworks)
        kt_html = "".join(f"<li>{kt}</li>" for kt in ci.key_takeaways)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Summary: {book_title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      line-height: 1.6;
      color: #1f2937;
      background-color: #f9fafb;
      margin: 0;
      padding: 2rem;
    }}
    .container {{
      max-width: 800px;
      margin: 0 auto;
      background: #ffffff;
      padding: 3rem;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    h1 {{ font-size: 2.25rem; margin-bottom: 0.5rem; color: #111827; }}
    h2 {{
      font-size: 1.5rem;
      margin-top: 2rem;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 0.5rem;
      color: #374151;
    }}
    h3 {{ font-size: 1.25rem; margin-top: 1.5rem; color: #4b5563; }}
    blockquote {{
      background: #f3f4f6;
      border-left: 4px solid #3b82f6;
      margin: 1.5rem 0;
      padding: 1rem 1.5rem;
      font-style: italic;
      color: #1e3a8a;
      border-radius: 0 8px 8px 0;
    }}
    ul, ol {{ padding-left: 1.5rem; }}
    li {{ margin-bottom: 0.5rem; }}
    .meta {{ color: #6b7280; font-size: 0.95rem; margin-bottom: 2rem; }}
    .footer {{
      margin-top: 3rem;
      font-size: 0.85rem;
      color: #9ca3af;
      text-align: center;
      border-top: 1px solid #e5e7eb;
      padding-top: 1rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{book_title}</h1>
    <div class="meta">
      <strong>Authors:</strong> {author_str} |
      <strong>Reading Time:</strong> ~{es.estimated_reading_time_minutes} min
    </div>

    <h2>Executive Snapshot</h2>
    <blockquote>{es.hook}</blockquote>
    <p><strong>Core Thesis:</strong> {es.core_thesis}</p>
    <p><strong>Target Audience:</strong> {es.target_audience}</p>

    <h3>Key Arguments</h3>
    <ul>
      {args_html}
    </ul>

    <h2>Chapter-by-Chapter Synthesis</h2>
    {chaps_html}

    <h2>Conceptual Index & Action Items</h2>
    <h3>Frameworks & Mental Models</h3>
    <ul>
      {fw_html}
    </ul>

    <h3>Key Takeaways</h3>
    <ul>
      {kt_html}
    </ul>

    <div class="footer">
      Generated by xBookLibrary Multi-Resolution Engine via {summary.metadata.model_name}
    </div>
  </div>
</body>
</html>"""
        return html

    async def sync_to_calibre_metadata(self, book_id: int, summary: BookSummary) -> bool:
        """Syncs the executive summary into Calibre comments table and metadata.opf."""
        if not self.library_root or not self.db_path or not self.storage:
            return False

        es = summary.executive_snapshot
        summary_html = (
            f"<p><strong>Executive Summary:</strong> {es.hook}</p>\n"
            f"<p><strong>Core Thesis:</strong> {es.core_thesis}</p>\n"
            f"<p><strong>Key Arguments:</strong></p>\n<ul>\n"
            + "".join(f"<li>{arg}</li>\n" for arg in es.key_arguments)
            + "</ul>"
        )

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # 1. Check existing comment
            async with db.execute(
                "SELECT id, text FROM comments WHERE book = ?", (book_id,)
            ) as cur:
                existing_row = await cur.fetchone()

            if existing_row:
                new_text = f"{existing_row['text']}\n<hr/>\n{summary_html}"
                await db.execute("UPDATE comments SET text = ? WHERE book = ?", (new_text, book_id))
            else:
                await db.execute(
                    "INSERT INTO comments (book, text) VALUES (?, ?)",
                    (book_id, summary_html),
                )
            await db.commit()

            # 2. Get book relative path for metadata.opf sync
            async with db.execute("SELECT path FROM books WHERE id = ?", (book_id,)) as cur:
                book_row = await cur.fetchone()
                if not book_row:
                    return False
                rel_path = book_row["path"]

        # 3. Update metadata.opf
        try:
            book_dir = self.storage.resolve_book_path(rel_path)
            opf_file = book_dir / "metadata.opf"
            if opf_file.exists():
                ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
                ET.register_namespace("opf", "http://www.idpf.org/2007/opf")
                tree = ET.parse(opf_file)
                root = tree.getroot()

                ns = {
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "opf": "http://www.idpf.org/2007/opf",
                }
                desc_el = root.find(".//dc:description", ns)
                if desc_el is None:
                    metadata_el = root.find(".//opf:metadata", ns)
                    if metadata_el is None:
                        metadata_el = root.find(".//metadata")
                    if metadata_el is not None:
                        desc_el = ET.SubElement(
                            metadata_el, "{http://purl.org/dc/elements/1.1/}description"
                        )

                if desc_el is not None:
                    desc_el.text = f"{es.hook} {es.core_thesis}"
                    tree.write(opf_file, encoding="utf-8", xml_declaration=True)
            return True
        except Exception:
            return False
