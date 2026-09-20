"""Export formatters and persistence handlers for synthesized research documents."""

import html
import re
from pathlib import Path

from backend.domain.synthesis import SynthesisDocument


class SynthesisExporter:
    """Exports SynthesisDocument instances into Markdown, styled HTML, and JSON formats."""

    def to_markdown(self, doc: SynthesisDocument) -> str:
        """Renders document as Markdown string."""
        return doc.content_markdown

    def to_html(self, doc: SynthesisDocument) -> str:
        """Renders document as a standalone, styled HTML document with responsive typography."""
        title_escaped = html.escape(doc.title)
        body_html = self._markdown_to_html(doc.content_markdown)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_escaped}</title>
    <style>
        :root {{
            --bg: #ffffff;
            --text: #1f2937;
            --text-muted: #6b7280;
            --accent: #2563eb;
            --surface: #f8fafc;
            --border: #e2e8f0;
            --callout-bg: #eff6ff;
            --callout-border: #bfdbfe;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #0f172a;
                --text: #f8fafc;
                --text-muted: #94a3b8;
                --accent: #60a5fa;
                --surface: #1e293b;
                --border: #334155;
                --callout-bg: #1e293b;
                --callout-border: #3b82f6;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                "Helvetica Neue", Arial, sans-serif;
            line-height: 1.7;
            color: var(--text);
            background-color: var(--bg);
            max-width: 860px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem;
        }}
        h1 {{
            font-size: 2.25rem;
            font-weight: 800;
            line-height: 1.25;
            margin-bottom: 0.5rem;
            color: var(--accent);
            border-bottom: 2px solid var(--border);
            padding-bottom: 0.75rem;
        }}
        h2 {{
            font-size: 1.5rem;
            color: var(--text);
            margin-top: 2rem;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.4rem;
        }}
        h3 {{
            font-size: 1.2rem;
            color: var(--text);
            margin-top: 1.5rem;
        }}
        p {{
            margin: 1rem 0;
        }}
        ul {{
            padding-left: 1.5rem;
            margin: 1rem 0;
        }}
        li {{
            margin-bottom: 0.35rem;
        }}
        a {{
            color: var(--accent);
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        blockquote {{
            background-color: var(--callout-bg);
            border-left: 4px solid var(--callout-border);
            padding: 0.75rem 1.25rem;
            margin: 1.5rem 0;
            border-radius: 0 6px 6px 0;
        }}
        @media print {{
            body {{
                max-width: 100%;
                padding: 0;
                color: #000000;
                background: #ffffff;
            }}
            h1, h2, h3 {{
                break-after: avoid;
            }}
            ul, blockquote {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <article>
        {body_html}
    </article>
</body>
</html>
"""

    def _markdown_to_html(self, md: str) -> str:
        """Converts basic Markdown structure to semantic HTML tags."""
        lines = md.splitlines()
        html_blocks: list[str] = []
        in_list = False

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                if in_list:
                    html_blocks.append("</ul>")
                    in_list = False
                continue

            # Headers
            if line.startswith("# "):
                if in_list:
                    html_blocks.append("</ul>")
                    in_list = False
                title_text = self._format_inline(line[2:])
                html_blocks.append(f"<h1>{title_text}</h1>")
            elif line.startswith("## "):
                if in_list:
                    html_blocks.append("</ul>")
                    in_list = False
                title_text = self._format_inline(line[3:])
                html_blocks.append(f"<h2>{title_text}</h2>")
            elif line.startswith("### "):
                if in_list:
                    html_blocks.append("</ul>")
                    in_list = False
                title_text = self._format_inline(line[4:])
                html_blocks.append(f"<h3>{title_text}</h3>")
            # Unordered lists
            elif line.startswith("- ") or line.startswith("* "):
                if not in_list:
                    html_blocks.append("<ul>")
                    in_list = True
                item_text = self._format_inline(line[2:])
                html_blocks.append(f"<li>{item_text}</li>")
            elif line.startswith("> "):
                if in_list:
                    html_blocks.append("</ul>")
                    in_list = False
                quote_text = self._format_inline(line[2:])
                html_blocks.append(f"<blockquote>{quote_text}</blockquote>")
            else:
                if in_list:
                    html_blocks.append("</ul>")
                    in_list = False
                p_text = self._format_inline(line)
                html_blocks.append(f"<p>{p_text}</p>")

        if in_list:
            html_blocks.append("</ul>")

        return "\n".join(html_blocks)

    def _format_inline(self, text: str) -> str:
        """Escapes HTML and formats inline markdown like bold, italics, and links."""
        # Escape raw text first
        safe_text = html.escape(text)

        # Bold **text**
        safe_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe_text)
        # Italic *text*
        safe_text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", safe_text)
        # Links [text](url)
        safe_text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', safe_text)

        return safe_text

    def to_json(self, doc: SynthesisDocument) -> str:
        """Serializes document into indented JSON format."""
        return doc.model_dump_json(indent=2)

    def save_to_library(
        self,
        library_path: Path,
        doc: SynthesisDocument,
        format: str = "markdown",
    ) -> Path:
        """Persists synthesis document under `<LibraryRoot>/.synthesis/` directory."""
        synthesis_dir = library_path / ".synthesis"
        synthesis_dir.mkdir(parents=True, exist_ok=True)

        fmt = format.lower()
        if fmt in ("html", "text/html"):
            target_path = synthesis_dir / f"{doc.id}.html"
            target_path.write_text(self.to_html(doc), encoding="utf-8")
        elif fmt in ("json", "application/json"):
            target_path = synthesis_dir / f"{doc.id}.json"
            target_path.write_text(self.to_json(doc), encoding="utf-8")
        else:
            target_path = synthesis_dir / f"{doc.id}.md"
            target_path.write_text(self.to_markdown(doc), encoding="utf-8")

        return target_path
