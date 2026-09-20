"""Multi-book document synthesis and research brief generation engine."""

import inspect
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from backend.domain.rag import SearchResult
from backend.domain.synthesis import (
    SynthesisDocument,
    SynthesisSection,
    SynthesisSource,
)
from backend.services.rag_search import RAGSearchService


class DocumentSynthesisService:
    """Orchestrates 4-stage multi-book research synthesis with strict citation grounding."""

    def __init__(
        self,
        search_service: RAGSearchService,
        llm_caller: Any = None,
        chunks_per_section: int = 4,
    ):
        self.search_service = search_service
        self.llm_caller = llm_caller
        self.chunks_per_section = chunks_per_section

    async def generate_outline(
        self,
        title: str,
        topic_prompt: str,
        template_type: str = "topic_brief",
    ) -> list[dict[str, str]]:
        """Generates structured section specifications and targeted search queries."""
        if template_type == "literature_review":
            return [
                {
                    "title": "Theoretical Foundations & Core Premises",
                    "query": f"{title} theoretical foundations core premises principles",
                },
                {
                    "title": "Methodological Approaches & Architectural Models",
                    "query": f"{title} methodology models approaches architecture",
                },
                {
                    "title": "Comparative Analysis & Consensus Across Literature",
                    "query": f"{title} comparison analysis consensus agreement",
                },
                {
                    "title": "Critical Debates, Contradictions & Open Questions",
                    "query": f"{title} debate controversy contradictions limitations",
                },
            ]

        if template_type == "executive_summary":
            return [
                {
                    "title": "Executive Strategic Overview",
                    "query": f"{title} strategic overview executive summary premise",
                },
                {
                    "title": "Core Frameworks & Decision Models",
                    "query": f"{title} frameworks decision models principles",
                },
                {
                    "title": "Strategic Insights & Actionable Takeaways",
                    "query": f"{title} takeaways insights conclusions recommendations",
                },
            ]

        # Default topic_brief / custom_research
        return [
            {
                "title": "Overview & Foundational Concepts",
                "query": f"{title} introduction overview foundations",
            },
            {
                "title": "Mechanisms, Models & Methodologies",
                "query": f"{title} concepts theory mechanisms models",
            },
            {
                "title": "Comparative Perspectives & Author Insights",
                "query": f"{title} comparison authors perspectives arguments",
            },
            {
                "title": "Synthesis, Synthesis Matrix & Implications",
                "query": f"{title} synthesis implications takeaways conclusions",
            },
        ]

    async def retrieve_section_evidence(
        self,
        library_path: Path,
        section_spec: dict[str, str],
        book_ids: list[int] | None = None,
    ) -> list[SearchResult]:
        """Retrieves top-ranked evidence chunks for a section, scoped to books if specified."""
        query = section_spec.get("query", "")
        if not query.strip():
            return []

        if book_ids:
            # Query each scoped book to ensure cross-book coverage
            collected: list[SearchResult] = []
            for bid in book_ids:
                res = await self.search_service.search(
                    library_path=library_path,
                    query=query,
                    book_id=bid,
                    top_k=max(2, self.chunks_per_section // len(book_ids) + 1),
                    mode="hybrid",
                )
                collected.extend(res)
            collected.sort(key=lambda x: x.score, reverse=True)
            return collected[: self.chunks_per_section * 2]

        return await self.search_service.search(
            library_path=library_path,
            query=query,
            top_k=self.chunks_per_section * 2,
            mode="hybrid",
        )

    async def draft_section(
        self,
        section_spec: dict[str, str],
        evidence: list[SearchResult],
        topic_prompt: str,
    ) -> SynthesisSection:
        """Drafts a grounded synthesis section with inline citations."""
        section_title = section_spec.get("title", "Section")

        if not evidence:
            return SynthesisSection(
                title=section_title,
                content=(
                    "No relevant passages could be located in the selected books for this topic."
                ),
                citations=[],
            )

        context_blocks = []
        for idx, r in enumerate(evidence, 1):
            block_hdr = f'[{idx}] Book: "{r.book_title}" by {r.authors} | Ch: "{r.chapter_title}"'
            context_blocks.append(f"{block_hdr}\n{r.content}\n")
        context_text = "\n---\n".join(context_blocks)

        system_instruction = (
            "You are a scholarly research specialist for xBookLibrary. "
            f"Draft the section '{section_title}' for the research topic: '{topic_prompt}'.\n"
            "Synthesize the arguments across authors rather than summarizing one book at a time.\n"
            "Every factual claim and insight MUST include an inline citation in the format: "
            "[Book Title, Chapter Title].\n"
            "Do not fabricate facts outside the provided source passages."
        )

        prompt = (
            f"Section: {section_title}\n"
            f"Research Question: {section_spec.get('query')}\n\n"
            f"SOURCE PASSAGES:\n{context_text}"
        )

        if self.llm_caller:
            content = await self.llm_caller(prompt, system_instruction)
        else:
            # Deterministic fallback synthesis using top evidence chunks
            parts = [f"### Analysis: {section_title}\n"]
            for r in evidence[:2]:
                parts.append(
                    f"According to [{r.book_title}, {r.chapter_title}], "
                    f"{r.content.splitlines()[-1] if r.content else 'principles apply'}."
                )
            content = "\n\n".join(parts)

        # Extract citations
        raw_citations = re.findall(r"\[([^[\]]+,\s*[^[\]]+)\]", content)
        citations = [f"[{c.strip()}]" for c in raw_citations]

        return SynthesisSection(
            title=section_title,
            content=content,
            citations=citations,
        )

    def assemble_document(
        self,
        doc_id: str,
        title: str,
        template_type: str,
        topic_prompt: str,
        sections: list[SynthesisSection],
        all_evidence: list[SearchResult],
        library_id: str,
    ) -> SynthesisDocument:
        """Assembles Markdown content, table of contents, and bibliography."""
        now = datetime.now(timezone.utc)

        # Build deduplicated sources
        sources_map: dict[int, dict[str, Any]] = {}
        for r in all_evidence:
            if r.book_id not in sources_map:
                sources_map[r.book_id] = {
                    "book_id": r.book_id,
                    "book_title": r.book_title,
                    "authors": r.authors,
                    "chapters": set(),
                }
            if r.chapter_title:
                sources_map[r.book_id]["chapters"].add(r.chapter_title)

        sources = [
            SynthesisSource(
                book_id=s["book_id"],
                book_title=s["book_title"],
                authors=s["authors"],
                chapters_cited=sorted(list(s["chapters"])),
            )
            for s in sources_map.values()
        ]

        # Compose Markdown
        template_label = template_type.replace("_", " ").title()
        md_lines = [
            f"# {title}",
            "",
            f"*{template_label} | Generated on {now.strftime('%Y-%m-%d')} | "
            f"Synthesized across {len(sources)} source book(s)*",
            "",
            "## Table of Contents",
        ]
        for sec in sections:
            anchor = sec.title.lower().replace(" ", "-").replace("&", "").replace(",", "")
            md_lines.append(f"- [{sec.title}](#{anchor})")

        md_lines.append("")

        for sec in sections:
            md_lines.append(f"## {sec.title}")
            md_lines.append("")
            md_lines.append(sec.content)
            md_lines.append("")

        md_lines.append("## Bibliography & Cited Sources")
        md_lines.append("")
        for src in sources:
            md_lines.append(f"- **{src.book_title}** by {src.authors}")
            if src.chapters_cited:
                ch_list = ", ".join(f'"{ch}"' for ch in src.chapters_cited)
                md_lines.append(f"  - Cited Chapters: {ch_list}")

        full_md = "\n".join(md_lines)
        word_count = len(full_md.split())

        return SynthesisDocument(
            id=doc_id,
            library_id=library_id,
            title=title,
            template_type=template_type,  # type: ignore[arg-type]
            topic_prompt=topic_prompt,
            outline=[s.title for s in sections],
            content_markdown=full_md,
            sources=sources,
            word_count=word_count,
            created_at=now,
            updated_at=now,
        )

    async def generate_document(
        self,
        db: aiosqlite.Connection,
        library_path: Path,
        library_id: str,
        title: str,
        topic_prompt: str,
        template_type: str = "topic_brief",
        book_ids: list[int] | None = None,
        progress_callback: Any = None,
    ) -> SynthesisDocument:
        """Executes the full 4-stage document synthesis pipeline and persists the result."""
        doc_id = f"syn_{uuid.uuid4().hex[:12]}"

        async def _update_progress(stage: str, pct: int):
            if progress_callback:
                if inspect.iscoroutinefunction(progress_callback):
                    await progress_callback(stage, pct)
                else:
                    res = progress_callback(stage, pct)
                    if inspect.isawaitable(res):
                        await res

        # Stage 1: Outline Generation
        await _update_progress("generating_outline", 15)
        outline_specs = await self.generate_outline(
            title=title, topic_prompt=topic_prompt, template_type=template_type
        )

        # Stage 2: Evidence Retrieval & Section Drafting
        sections: list[SynthesisSection] = []
        all_evidence: list[SearchResult] = []

        total_sections = len(outline_specs)
        for i, spec in enumerate(outline_specs):
            await _update_progress(
                f"retrieving_evidence_section_{i + 1}",
                25 + int((i / total_sections) * 20),
            )
            evidence = await self.retrieve_section_evidence(
                library_path=library_path,
                section_spec=spec,
                book_ids=book_ids,
            )
            all_evidence.extend(evidence)

            await _update_progress(
                f"drafting_section_{i + 1}",
                50 + int((i / total_sections) * 35),
            )
            sec = await self.draft_section(
                section_spec=spec,
                evidence=evidence,
                topic_prompt=topic_prompt,
            )
            sections.append(sec)

        # Stage 3: Assembly & Bibliography
        await _update_progress("assembling_document", 90)
        document = self.assemble_document(
            doc_id=doc_id,
            title=title,
            template_type=template_type,
            topic_prompt=topic_prompt,
            sections=sections,
            all_evidence=all_evidence,
            library_id=library_id,
        )

        # Stage 4: Storage Persistence
        synth_dir = library_path / ".synthesis"
        synth_dir.mkdir(parents=True, exist_ok=True)
        file_path = synth_dir / f"{doc_id}.md"
        file_path.write_text(document.content_markdown, encoding="utf-8")

        sources_json = json.dumps([s.model_dump() for s in document.sources])
        outline_json = json.dumps(document.outline)

        await db.execute(
            """INSERT INTO x_synthesis_documents
               (id, library_id, title, template_type, topic_prompt,
                outline_json, content_markdown, sources_json, word_count,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                document.id,
                document.library_id,
                document.title,
                document.template_type,
                document.topic_prompt,
                outline_json,
                document.content_markdown,
                sources_json,
                document.word_count,
                document.created_at.isoformat(),
                document.updated_at.isoformat(),
            ),
        )
        await db.commit()

        await _update_progress("completed", 100)
        return document
