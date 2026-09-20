import html
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.domain.entities import Book


FORMAT_MIME_MAP = {
    "EPUB": "application/epub+zip",
    "PDF": "application/pdf",
    "MOBI": "application/x-mobipocket-ebook",
    "AZW3": "application/x-mobi8-ebook",
    "CBZ": "application/vnd.comicbook+zip",
    "CBR": "application/vnd.comicbook-rar",
    "TXT": "text/plain",
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class OPDSService:
    """
    Generates OPDS 1.2 (Atom XML) and OPDS 2.0 (Readium JSON) catalog feeds,
    and OpenSearch 1.1 description documents.
    """

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def build_root_feed_xml(cls, base_url: str, library_name: str = "xBookLibrary") -> str:
        """
        Builds the top-level OPDS 1.2 Navigation Feed.
        """
        now = cls._now_iso()
        clean_base = base_url.rstrip("/")

        feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>urn:xbook:opds:root</id>
  <title>{html.escape(library_name)} - Catalog</title>
  <updated>{now}</updated>
  <author>
    <name>{html.escape(library_name)}</name>
  </author>
  <link rel="self" href="{clean_base}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation" />
  <link rel="start" href="{clean_base}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation" />
  <link rel="search" href="{clean_base}/opds/opensearch.xml" type="application/opensearchdescription+xml" />

  <entry>
    <title>All Books</title>
    <id>urn:xbook:opds:all-books</id>
    <updated>{now}</updated>
    <content type="text">Browse all books in the catalog</content>
    <link rel="subsection" href="{clean_base}/opds/books" type="application/atom+xml;profile=opds-catalog;kind=acquisition" />
  </entry>

  <entry>
    <title>Recent Additions</title>
    <id>urn:xbook:opds:recent</id>
    <updated>{now}</updated>
    <content type="text">Recently imported and enriched books</content>
    <link rel="http://opds-spec.org/sort/new" href="{clean_base}/opds/recent" type="application/atom+xml;profile=opds-catalog;kind=acquisition" />
  </entry>

  <entry>
    <title>Browse by Category &amp; Taxonomy</title>
    <id>urn:xbook:opds:taxonomies</id>
    <updated>{now}</updated>
    <content type="text">Browse books grouped by BISAC and Dewey Decimal categories</content>
    <link rel="subsection" href="{clean_base}/opds/taxonomies" type="application/atom+xml;profile=opds-catalog;kind=navigation" />
  </entry>

  <entry>
    <title>Browse by Author</title>
    <id>urn:xbook:opds:authors</id>
    <updated>{now}</updated>
    <content type="text">Browse books organized by author</content>
    <link rel="subsection" href="{clean_base}/opds/authors" type="application/atom+xml;profile=opds-catalog;kind=navigation" />
  </entry>
</feed>"""
        return feed_xml

    @classmethod
    def build_books_acquisition_feed_xml(
        cls,
        books: List[Book],
        base_url: str,
        title: str = "All Books",
        feed_id: str = "urn:xbook:opds:books",
        page: int = 1,
        limit: int = 50,
        total_count: Optional[int] = None,
    ) -> str:
        """
        Builds an OPDS 1.2 Acquisition Feed for a list of books.
        """
        now = cls._now_iso()
        clean_base = base_url.rstrip("/")

        entries_xml = []
        for book in books:
            book_updated = (
                book.last_modified.strftime("%Y-%m-%dT%H:%M:%SZ")
                if book.last_modified
                else now
            )
            authors_xml = "\n".join(
                f"    <author><name>{html.escape(a)}</name></author>"
                for a in book.authors
            ) or "    <author><name>Unknown Author</name></author>"

            summary_val = getattr(book, "description", None) or getattr(book, "comments", None) or book.title
            summary_text = html.escape(summary_val)

            # Cover links
            cover_url = f"{clean_base}/covers/{book.id}.jpg"
            image_links = f"""    <link rel="http://opds-spec.org/image" href="{cover_url}" type="image/jpeg" />
    <link rel="http://opds-spec.org/image/thumbnail" href="{cover_url}" type="image/jpeg" />"""

            # Acquisition links
            acq_links = []
            for fmt in book.formats:
                mime = FORMAT_MIME_MAP.get(fmt.format.upper(), "application/octet-stream")
                download_url = f"{clean_base}/api/books/{book.id}/download?format={fmt.format}"
                acq_links.append(
                    f'    <link rel="http://opds-spec.org/acquisition" href="{download_url}" type="{mime}" title="{fmt.format}" />'
                )
            acquisition_links_xml = "\n".join(acq_links)

            # Categories / Tags
            cat_xml = "\n".join(
                f'    <category term="{html.escape(t)}" label="{html.escape(t)}" />'
                for t in book.tags
            )

            entry = f"""  <entry>
    <title>{html.escape(book.title)}</title>
    <id>urn:xbook:book:{book.id}</id>
    <dc:identifier>urn:xbook:book:{book.id}</dc:identifier>
{authors_xml}
    <updated>{book_updated}</updated>
    <summary type="text">{summary_text}</summary>
{image_links}
{acquisition_links_xml}
{cat_xml}
  </entry>"""
            entries_xml.append(entry)

        feed_body = "\n".join(entries_xml)

        feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>{feed_id}</id>
  <title>{html.escape(title)}</title>
  <updated>{now}</updated>
  <link rel="self" href="{clean_base}/opds/books" type="application/atom+xml;profile=opds-catalog;kind=acquisition" />
  <link rel="start" href="{clean_base}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation" />
  <link rel="search" href="{clean_base}/opds/opensearch.xml" type="application/opensearchdescription+xml" />
{feed_body}
</feed>"""
        return feed_xml

    @classmethod
    def build_opensearch_description_xml(cls, base_url: str) -> str:
        """
        Builds OpenSearch 1.1 description XML document.
        """
        clean_base = base_url.rstrip("/")
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
  <ShortName>xBookLibrary</ShortName>
  <Description>Search books in xBookLibrary</Description>
  <InputEncoding>UTF-8</InputEncoding>
  <OutputEncoding>UTF-8</OutputEncoding>
  <Url type="application/atom+xml;profile=opds-catalog;kind=acquisition"
       template="{clean_base}/opds/search?q={{searchTerms}}" />
</OpenSearchDescription>"""

    @classmethod
    def build_opds_2_json(cls, books: List[Book], base_url: str, title: str = "xBookLibrary Catalog") -> Dict[str, Any]:
        """
        Builds OPDS 2.0 Readium JSON catalog manifest.
        """
        clean_base = base_url.rstrip("/")
        now = cls._now_iso()

        publications = []
        for book in books:
            book_updated = (
                book.last_modified.strftime("%Y-%m-%dT%H:%M:%SZ")
                if book.last_modified
                else now
            )
            pub_links = []
            for fmt in book.formats:
                mime = FORMAT_MIME_MAP.get(fmt.format.upper(), "application/octet-stream")
                pub_links.append({
                    "rel": "http://opds-spec.org/acquisition",
                    "href": f"{clean_base}/api/books/{book.id}/download?format={fmt.format}",
                    "type": mime,
                    "title": fmt.format,
                })

            images = [
                {
                    "href": f"{clean_base}/covers/{book.id}.jpg",
                    "type": "image/jpeg",
                    "rel": "http://opds-spec.org/image"
                }
            ]

            publications.append({
                "metadata": {
                    "@type": "http://schema.org/Book",
                    "title": book.title,
                    "author": book.authors,
                    "identifier": f"urn:xbook:book:{book.id}",
                    "modified": book_updated,
                    "description": getattr(book, "description", None) or getattr(book, "comments", None),
                },
                "links": pub_links,
                "images": images,
            })

        return {
            "metadata": {
                "title": title,
                "updated": now,
            },
            "links": [
                {
                    "rel": "self",
                    "href": f"{clean_base}/api/opds/v2.0",
                    "type": "application/opds+json"
                },
                {
                    "rel": "search",
                    "href": f"{clean_base}/opds/search?q={{searchTerms}}",
                    "type": "application/atom+xml;profile=opds-catalog;kind=acquisition",
                    "templated": True
                }
            ],
            "navigation": [
                {
                    "title": "All Books",
                    "href": f"{clean_base}/opds/books",
                    "type": "application/atom+xml;profile=opds-catalog;kind=acquisition"
                },
                {
                    "title": "Recent Additions",
                    "href": f"{clean_base}/opds/recent",
                    "type": "application/atom+xml;profile=opds-catalog;kind=acquisition"
                }
            ],
            "publications": publications,
        }
