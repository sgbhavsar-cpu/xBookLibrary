"""Unit tests for SynthesisExporter covering Markdown, HTML, and JSON formatters."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.domain.synthesis import (
    SynthesisDocument,
    SynthesisSource,
)
from backend.services.synthesis_exporter import SynthesisExporter


@pytest.fixture
def sample_synthesis_document() -> SynthesisDocument:
    now = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
    md_content = """# Comparative Quantum Architecture Analysis

*Literature Review | Generated on 2026-09-20 | Synthesized across 2 source book(s)*

## Table of Contents
- [1. Introduction](#1-introduction)
- [2. Physical Architectures](#2-physical-architectures)

## Executive Summary

This brief examines the engineering tradeoffs between hardware paradigms.

## 1. Introduction

Superposition allows parallel states [Quantum Computing Explained, Chapter 1].

## 2. Physical Architectures

Superconducting circuits provide fast gates [Superconducting Qubits, Chapter 3].

## Bibliography & Cited Sources

- **Quantum Computing Explained** by David McMahon
  - Cited Chapters: "Chapter 1: Quantum States"
- **Superconducting Qubits** by John Clarke
  - Cited Chapters: "Chapter 3: Josephson Junctions"
"""
    return SynthesisDocument(
        id="syn-test-12345",
        library_id="test-lib",
        title="Comparative Quantum Architecture Analysis",
        topic_prompt="Compare superconducting qubits with trapped ions",
        template_type="literature_review",
        outline=["1. Introduction", "2. Physical Architectures"],
        content_markdown=md_content,
        sources=[
            SynthesisSource(
                book_id=1,
                book_title="Quantum Computing Explained",
                authors="David McMahon",
                chapters_cited=["Chapter 1: Quantum States"],
            ),
            SynthesisSource(
                book_id=2,
                book_title="Superconducting Qubits",
                authors="John Clarke",
                chapters_cited=["Chapter 3: Josephson Junctions"],
            ),
        ],
        word_count=len(md_content.split()),
        created_at=now,
        updated_at=now,
    )


def test_export_markdown(sample_synthesis_document):
    exporter = SynthesisExporter()
    md_output = exporter.to_markdown(sample_synthesis_document)

    assert "# Comparative Quantum Architecture Analysis" in md_output
    assert "## Executive Summary" in md_output
    assert "tradeoffs between hardware paradigms" in md_output
    assert "## Table of Contents" in md_output
    assert "## 1. Introduction" in md_output
    assert "[Quantum Computing Explained, Chapter 1]" in md_output
    assert "## Bibliography & Cited Sources" in md_output
    assert "- **Quantum Computing Explained** by David McMahon" in md_output
    assert "Chapter 1: Quantum States" in md_output


def test_export_html(sample_synthesis_document):
    exporter = SynthesisExporter()
    html_output = exporter.to_html(sample_synthesis_document)

    assert "<!DOCTYPE html>" in html_output
    assert "<title>Comparative Quantum Architecture Analysis</title>" in html_output
    assert "Executive Summary" in html_output
    assert "Comparative Quantum Architecture Analysis</h1>" in html_output
    assert "David McMahon" in html_output
    assert "@media print" in html_output


def test_export_json(sample_synthesis_document):
    exporter = SynthesisExporter()
    json_output = exporter.to_json(sample_synthesis_document)

    data = json.loads(json_output)
    assert data["id"] == "syn-test-12345"
    assert data["title"] == "Comparative Quantum Architecture Analysis"
    assert data["library_id"] == "test-lib"
    assert len(data["outline"]) == 2
    assert len(data["sources"]) == 2


def test_save_to_library(tmp_path: Path, sample_synthesis_document):
    exporter = SynthesisExporter()
    md_path = exporter.save_to_library(tmp_path, sample_synthesis_document, format="markdown")

    assert md_path.exists()
    assert md_path.parent.name == ".synthesis"
    assert md_path.name == "syn-test-12345.md"
    content = md_path.read_text(encoding="utf-8")
    assert "# Comparative Quantum Architecture Analysis" in content

    html_path = exporter.save_to_library(tmp_path, sample_synthesis_document, format="html")
    assert html_path.exists()
    assert html_path.name == "syn-test-12345.html"
    html_content = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_content
