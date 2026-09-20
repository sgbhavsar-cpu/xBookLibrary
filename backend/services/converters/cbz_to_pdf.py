import io
import re
import zipfile
from pathlib import Path
from typing import Any, List, Tuple
from PIL import Image


def natural_sort_key(s: str) -> List[Any]:
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


class CBZToPdfConverter:
    """
    Converts a comic archive (.cbz) into a unified PDF document.
    """

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    @classmethod
    def convert(cls, cbz_path: Path, output_pdf_path: Path) -> Path:
        if not cbz_path.exists():
            raise FileNotFoundError(f"Source CBZ file not found: {cbz_path}")

        images: List[Image.Image] = []

        with zipfile.ZipFile(cbz_path, "r") as z:
            # Sort files naturally so page 1, 2, 10 appear in order
            filenames = [
                name for name in z.namelist()
                if Path(name).suffix.lower() in cls.IMAGE_EXTENSIONS
                and not Path(name).name.startswith(".")
            ]
            filenames.sort(key=natural_sort_key)

            if not filenames:
                raise ValueError("No readable image pages found inside CBZ archive")

            for name in filenames:
                with z.open(name) as img_file:
                    img_data = img_file.read()
                    img = Image.open(io.BytesIO(img_data))
                    # Ensure image is in RGB mode for PDF output
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    images.append(img)

        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        first_image = images[0]
        rest_images = images[1:] if len(images) > 1 else []

        first_image.save(
            str(output_pdf_path),
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=rest_images,
        )

        return output_pdf_path
