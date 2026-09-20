"""Universal LiteLLM Multimodal Vision Adapter for bibliographic metadata extraction."""

import json
import re
from typing import List, Optional

import litellm

from backend.config import ConfigManager
from backend.domain.enrichment import CandidateMetadata, CoverCandidate
from backend.services.vision_extractor import VisionExtractor


class LiteLLMClientAdapter:
    """Extracts bibliographic metadata from book page images using LiteLLM (Gemini / Ollama)."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        model_name: Optional[str] = None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self.model_name = model_name or self._resolve_default_model()

    def _resolve_default_model(self) -> str:
        """Auto-detects Gemini 2.0 Flash if API key is present,
        otherwise falls back to local Ollama.
        """
        gemini_key = self.config_manager.get_gemini_api_key()
        if gemini_key:
            return "gemini/gemini-2.0-flash"
        return "ollama/llama3.2-vision"

    async def extract_from_images(
        self,
        image_bytes_list: List[bytes],
        fallback_title: Optional[str] = None,
    ) -> Optional[CandidateMetadata]:
        """Sends images to multimodal LLM and extracts structured bibliographic metadata."""
        if not image_bytes_list:
            return None

        data_urls = VisionExtractor.to_base64_data_urls(image_bytes_list)
        content_items = [
            {
                "type": "text",
                "text": (
                    "You are an expert librarian and bibliographic cataloger. "
                    "Carefully inspect the provided book cover and initial page images. "
                    "Extract the book's bibliographic metadata into pure JSON with "
                    "the exact fields:\n"
                    "- title: (string, clean main title and subtitle)\n"
                    "- authors: (list of strings, author full names)\n"
                    "- publisher: (string or null, publishing house or university press)\n"
                    "- publication_year: (integer or null, 4-digit year)\n"
                    "- isbn: (string or null, 10 or 13 digit ISBN if found)\n"
                    "- description: (string or null, short synopsis or back cover blurb)\n"
                    "- tags: (list of strings, 3 to 6 genres or academic subject areas)\n"
                    "- confidence: (float between 0.0 and 1.0)\n\n"
                    "Output ONLY raw, valid JSON with no markdown formatting or commentary."
                ),
            }
        ]

        for url in data_urls:
            content_items.append({"type": "image_url", "image_url": {"url": url}})

        messages = [{"role": "user", "content": content_items}]

        kwargs = {}
        if self.model_name.startswith("gemini/"):
            kwargs["api_key"] = self.config_manager.get_gemini_api_key()
        elif self.model_name.startswith("ollama/"):
            kwargs["api_base"] = self.config_manager.get_ollama_endpoint()

        try:
            response = await litellm.acompletion(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                **kwargs,
            )

            raw_text = response.choices[0].message.content or ""
            parsed = self._parse_json_response(raw_text)
            if not parsed or not parsed.get("title"):
                return None

            cover = None
            if image_bytes_list:
                cover = CoverCandidate(
                    bytes_data=image_bytes_list[0],
                    source="litellm_vision",
                )

            return CandidateMetadata(
                source="litellm_vision",
                isbn=parsed.get("isbn"),
                title=parsed.get("title") or fallback_title,
                authors=parsed.get("authors", []),
                publisher=parsed.get("publisher"),
                publication_year=parsed.get("publication_year"),
                description=parsed.get("description"),
                tags=parsed.get("tags", [])[:10],
                cover=cover,
                raw_payload=parsed,
            )
        except Exception:
            return None

    def _parse_json_response(self, text: str) -> Optional[dict]:
        """Cleans markdown fences and parses raw JSON."""
        clean = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean).strip()

        try:
            return json.loads(clean)
        except Exception:
            # Fallback regex extraction for { ... } block
            m = re.search(r"(\{.*\})", clean, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
            return None
