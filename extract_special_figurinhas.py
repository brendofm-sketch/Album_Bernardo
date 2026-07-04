#!/usr/bin/env python3
"""Extrai figurinhas especiais FWC e CC do PDF principal."""

from pathlib import Path

import fitz
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
PDF_FILE = next(ROOT.glob("*101 paginas completo.pdf"))
OUT_DIR = ROOT / "figurinhas"
CROP_DIR = ROOT / "pdf_101_recortes"
SIZE = (768, 1056)


def to_card(img: Image.Image) -> Image.Image:
    return ImageOps.exif_transpose(img).convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)


def save_from_crop(code: str, number: int, crop_name: str) -> None:
    img = Image.open(CROP_DIR / crop_name)
    to_card(img).save(OUT_DIR / f"{code}_{number:02d}.webp", "WEBP", quality=95, method=6)


def render_page(doc: fitz.Document, page_number: int, scale: float = 3.0) -> Image.Image:
    page = doc[page_number - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def crop_norm(page: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    w, h = page.size
    x1, y1, x2, y2 = box
    return page.crop((round(x1 * w), round(y1 * h), round(x2 * w), round(y2 * h)))


def extract_fwc() -> None:
    crops = [
        *(f"p098_r{r}c{c}.jpg" for r in range(1, 5) for c in range(1, 5)),
        *(f"p099_r1c{c}.jpg" for c in range(1, 5)),
    ]
    for number, crop_name in enumerate(crops):
        save_from_crop("FWC", number, crop_name)


def extract_cc() -> None:
    crops = [
        *(f"p097_r{r}c{c}.jpg" for r in range(1, 4) for c in range(1, 5)),
        "p097_r4c1.jpg",
        "p097_r4c2.jpg",
    ]
    for number, crop_name in enumerate(crops, start=1):
        save_from_crop("CC", number, crop_name)


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    extract_fwc()
    extract_cc()
    print("FWC: 20 imagens")
    print("CC: 14 imagens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
