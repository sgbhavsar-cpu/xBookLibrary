from datetime import datetime, timezone

from backend.domain.synthesis import (
    SynthesisDocument,
    SynthesisJobStatus,
    SynthesisSection,
    SynthesisSource,
)


def test_synthesis_domain_models():
    now = datetime.now(timezone.utc)

    source = SynthesisSource(
        book_id=1,
        book_title="Quantum Information",
        authors="Nielsen & Chuang",
        chapters_cited=["Chapter 1: Quantum States", "Chapter 4: Circuits"],
    )
    assert source.book_id == 1
    assert len(source.chapters_cited) == 2

    section = SynthesisSection(
        title="Theoretical Foundations",
        content=(
            "Quantum superposition enables parallel computation [Quantum Information, Chapter 1]."
        ),
        citations=["[Quantum Information, Chapter 1]"],
    )
    assert section.title == "Theoretical Foundations"
    assert len(section.citations) == 1

    doc = SynthesisDocument(
        id="syn_12345",
        library_id="default_lib",
        title="Quantum Computing State of the Art",
        template_type="literature_review",
        topic_prompt="Compare fault-tolerant quantum error correction models.",
        outline=["Theoretical Foundations", "Surface Codes", "Physical Implementations"],
        content_markdown="# Quantum Computing State of the Art\n\n...",
        sources=[source],
        word_count=1500,
        created_at=now,
        updated_at=now,
    )

    assert doc.id == "syn_12345"
    assert doc.template_type == "literature_review"
    assert len(doc.outline) == 3
    assert len(doc.sources) == 1
    assert doc.word_count == 1500


def test_synthesis_job_status_model():
    job = SynthesisJobStatus(
        job_id="job_abc123",
        status="running",
        stage="drafting_sections",
        percent_complete=65,
        document_id="syn_12345",
    )
    assert job.status == "running"
    assert job.percent_complete == 65
    assert job.document_id == "syn_12345"
