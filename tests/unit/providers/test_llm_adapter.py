"""Unit tests for LiteLLMClientAdapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.config import ConfigManager
from backend.providers.llm_adapter import LiteLLMClientAdapter


def test_model_auto_detection(tmp_path, monkeypatch):
    """Verifies that Gemini is selected when API key is set, else Ollama."""
    # 1. No key -> Ollama
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cfg = ConfigManager(config_dir=tmp_path / "cfg1")
    adapter = LiteLLMClientAdapter(config_manager=cfg)
    assert adapter.model_name == "ollama/llama3.2-vision"

    # 2. Key set -> Gemini
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    cfg2 = ConfigManager(config_dir=tmp_path / "cfg2")
    adapter2 = LiteLLMClientAdapter(config_manager=cfg2)
    assert adapter2.model_name == "gemini/gemini-2.0-flash"


def test_parse_json_response():
    """Verifies parsing of raw JSON and markdown-fenced JSON responses."""
    adapter = LiteLLMClientAdapter()

    # Raw JSON
    raw = '{"title": "Snow Crash", "authors": ["Neal Stephenson"], "publication_year": 1992}'
    parsed = adapter._parse_json_response(raw)
    assert parsed is not None
    assert parsed["title"] == "Snow Crash"
    assert parsed["authors"] == ["Neal Stephenson"]

    # Markdown code fence JSON
    fenced = """```json
    {
      "title": "Hyperion",
      "authors": ["Dan Simmons"],
      "publisher": "Doubleday",
      "publication_year": 1989
    }
    ```"""
    parsed2 = adapter._parse_json_response(fenced)
    assert parsed2 is not None
    assert parsed2["title"] == "Hyperion"
    assert parsed2["publisher"] == "Doubleday"


@pytest.mark.asyncio
async def test_extract_from_images_mocked():
    """Verifies multimodal image processing with mocked litellm completion."""
    adapter = LiteLLMClientAdapter(model_name="gemini/gemini-2.0-flash")

    mock_choice = MagicMock()
    mock_choice.message.content = """```json
    {
      "title": "Neuromancer",
      "authors": ["William Gibson"],
      "publisher": "Ace Books",
      "publication_year": 1984,
      "isbn": "9780441569595",
      "description": "Case was the sharpest data-thief in the matrix.",
      "tags": ["Cyberpunk", "Sci-Fi"],
      "confidence": 0.95
    }
    ```"""

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    sample_image = b"\xff\xd8\xff\xe0samplejpgdata"

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
        mock_litellm.return_value = mock_response

        candidate = await adapter.extract_from_images([sample_image])

        assert candidate is not None
        assert candidate.title == "Neuromancer"
        assert candidate.authors == ["William Gibson"]
        assert candidate.publication_year == 1984
        assert candidate.publisher == "Ace Books"
        assert candidate.isbn == "9780441569595"
        assert candidate.cover is not None
        assert candidate.cover.bytes_data == sample_image
