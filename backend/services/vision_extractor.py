"""Extracts visual page images from PDF and EPUB files for multimodal LLM analysis."""

import base64
import io
from pathlib import Path
from typing import List

from PIL import Image


class VisionExtractor:
    """Extracts first few visual pages (cover, title page, copyright) as JPEG bytes."""

    @classmethod
    def extract_preview_images(cls, file_path: Path, max_pages: int = 3) -> List[bytes]:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return cls._extract_pdf_pages(file_path, max_pages=max_pages)
        elif ext in (".epub", ".cbz", ".cbr"):
            return cls._extract_archive_pages(file_path, max_pages=max_pages)
        else:
            return []

    @classmethod
    def _extract_pdf_pages(cls, file_path: Path, max_pages: int = 3) -> List[bytes]:
        images: List[bytes] = []
        try:
            import pypdfium2

            pdf_bytes = file_path.read_bytes()
            doc = pypdfium2.PdfDocument(pdf_bytes)
            num_pages = min(len(doc), max_pages)

            for i in range(num_pages):
                page = doc[i]
                pil_img = page.render(scale=1.5).to_pil()
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=85)
                images.append(buf.getvalue())
            doc.close()
        except Exception:
            pass

        # Fallback: create a blank placeholder thumbnail if rendering fails
        if not images:
            img = Image.new("RGB", (400, 600), color=(50, 50, 60))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            images.append(buf.getvalue())

        return images

    @classmethod
    def _extract_archive_pages(cls, file_path: Path, max_pages: int = 3) -> List[bytes]:
        images: List[bytes] = []
        try:
            import zipfile

            with zipfile.ZipFile(file_path, "r") as zf:
                image_names = [
                    n
                    for n in zf.namelist()
                    if n.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                    and not n.startswith("__MACOSX")
                ][:max_pages]

                for name in image_names:
                    data = zf.read(name)
                    with Image.open(io.BytesIO(data)) as img:
                        img = img.convert("RGB")
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=85)
                        images.append(buf.getvalue())
        except Exception:
            pass

        return images

    @classmethod
    def to_base64_data_urls(cls, images: List[bytes]) -> List[str]:
        urls = []
        for img_bytes in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            urls.append(f"data:image/jpeg;base64,{b64}")
        return urls
