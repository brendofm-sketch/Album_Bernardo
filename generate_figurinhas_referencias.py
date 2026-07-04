#!/usr/bin/env python3
"""
Monta figurinhas locais usando fotos de referencia, sem API.

O resultado nao e IA generativa: e um card composto automaticamente com moldura,
foto recortada, codigo (ex: BRA03), nome e posicao. Quando nao houver foto de
referencia no CSV, gera um card de controle com fundo/cores do pais para manter
todos os arquivos existentes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "album_copa_2026_premium_imagens_externas.html"
CSV_FILE = ROOT / "referencias" / "referencias_jogadores.csv"
OUT_DIR = ROOT / "figurinhas"
SIZE = (768, 1056)

TEAM_COLORS = {
    "ARG": ("#74acdf", "#ffffff", "#f6b40e"),
    "BRA": ("#009b3a", "#ffdf00", "#002776"),
    "FRA": ("#0055a4", "#ffffff", "#ef4135"),
    "GER": ("#111111", "#dd0000", "#ffce00"),
    "MEX": ("#006847", "#ffffff", "#ce1126"),
    "POR": ("#006600", "#ff0000", "#ffcc00"),
    "USA": ("#3c3b6e", "#b22234", "#ffffff"),
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def read_teams() -> list[dict]:
    text = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"const\s+TEAMS\s*=\s*(\[.*?\]);\s*const\s+IMAGE_FOLDER", text, re.S)
    if not match:
        raise RuntimeError("Nao encontrei TEAMS no HTML.")
    return json.loads(match.group(1))


def read_refs() -> dict[str, dict]:
    if not CSV_FILE.exists():
        return {}
    refs = {}
    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            refs[f"{row['code']}{int(row['number']):02d}"] = row
    return refs


def colors(code: str) -> tuple[str, str, str]:
    return TEAM_COLORS.get(code, ("#1d4ed8", "#ffffff", "#facc15"))


def rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.strip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def role(slot: dict) -> str:
    if slot["type"] == "badge":
        return "ESCUDO"
    if slot["type"] == "squad":
        return "ELENCO"
    n = slot["n"]
    if n <= 3:
        return "GOLEIRO"
    if n <= 8:
        return "DEFENSOR"
    if n <= 12:
        return "MEIO-CAMPISTA"
    return "ATACANTE"


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    size = start
    while size > 14:
        f = font(size, bold)
        box = draw.textbbox((0, 0), text, font=f)
        if box[2] - box[0] <= max_width:
            return f
        size -= 2
    return font(size, bold)


def cover_crop(img: Image.Image, box_size: tuple[int, int], face_bias: float = 0.24, zoom: float = 1.35) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("RGB")
    target_w, target_h = box_size
    scale = max(target_w / img.width, target_h / img.height) * zoom
    new = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (new.width - target_w) // 2)
    top = max(0, min(new.height - target_h, round((new.height - target_h) * face_bias)))
    return new.crop((left, top, left + target_w, top + target_h))


def paste_contain(base: Image.Image, source: Image.Image, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    source = ImageOps.exif_transpose(source).convert("RGBA")
    source.thumbnail((x2 - x1, y2 - y1), Image.Resampling.LANCZOS)
    x = x1 + ((x2 - x1) - source.width) // 2
    y = y1 + ((y2 - y1) - source.height) // 2
    base.paste(source, (x, y), source)


def circular_portrait(path: Path | None, size: int, fill: tuple[int, int, int], accent: tuple[int, int, int]) -> Image.Image:
    portrait = Image.new("RGBA", (size, size), fill + (255,))
    if path and path.exists():
        try:
            crop = cover_crop(Image.open(path), (size, size), face_bias=0.20, zoom=1.18).convert("RGBA")
            portrait = crop
        except Exception:
            pass
    else:
        pd = ImageDraw.Draw(portrait)
        pd.ellipse((size * 0.30, size * 0.16, size * 0.70, size * 0.56), fill=(232, 216, 190))
        pd.pieslice((size * 0.18, size * 0.50, size * 0.82, size * 1.08), 180, 360, fill=accent)

    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(portrait, (0, 0), mask)
    ring = ImageDraw.Draw(out)
    ring.ellipse((2, 2, size - 3, size - 3), outline=(255, 255, 255, 235), width=5)
    return out


def draw_base(team: dict) -> Image.Image:
    w, h = SIZE
    c1, c2, c3 = [rgb(c) for c in colors(team["code"])]
    img = Image.new("RGB", SIZE, (245, 239, 224))
    draw = ImageDraw.Draw(img)

    for y in range(h):
        t = y / h
        base = tuple(round(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        draw.line((0, y, w, y), fill=base)
    draw.rectangle((0, int(h * 0.58), w, h), fill=tuple(round(c1[i] * 0.45 + c3[i] * 0.55) for i in range(3)))
    return img


def decorate_card(img: Image.Image, team: dict, slot: dict, role_override: str | None = None) -> Image.Image:
    w, h = SIZE
    c1, c2, c3 = [rgb(c) for c in colors(team["code"])]
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((30, 28, w - 30, h - 28), radius=34, outline=(255, 255, 255, 245), width=34)
    od.rounded_rectangle((62, 72, w - 62, h - 132), radius=18, outline=c3 + (230,), width=8)
    od.polygon([(74, 126), (220, 126), (74, 480)], fill=(255, 255, 255, 46))
    od.rectangle((74, 818, w - 74, 966), fill=c3 + (238,))
    od.rectangle((74, 818, w - 74, 844), fill=c2 + (245,))
    od.rounded_rectangle((94, 88, 234, 136), radius=10, fill=(255, 255, 255, 235))
    od.rounded_rectangle((512, 88, 674, 136), radius=10, fill=c2 + (235,))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    code = f"{team['code']}{slot['n']:02d}"
    name = slot["name"].upper()
    r = (role_override or role(slot)).upper()
    code_font = font(34, True)
    draw.text((104, 94), code, font=code_font, fill=(20, 24, 35))
    name_font = fit_text(draw, name, 560, 46, True)
    role_font = font(24, False)
    name_box = draw.textbbox((0, 0), name, font=name_font)
    draw.text(((w - (name_box[2] - name_box[0])) / 2, 852), name, font=name_font, fill=(255, 255, 255))
    role_box = draw.textbbox((0, 0), r, font=role_font)
    draw.text(((w - (role_box[2] - role_box[0])) / 2, 914), r, font=role_font, fill=(232, 240, 255))
    return img


def draw_badge_card(team: dict, slot: dict, ref_path: Path | None) -> Image.Image:
    c1, c2, c3 = [rgb(c) for c in colors(team["code"])]
    img = draw_base(team).convert("RGBA")
    panel = Image.new("RGBA", (620, 700), tuple(round(c1[i] * 0.55 + c2[i] * 0.45) for i in range(3)) + (255,))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((36, 36, 584, 664), radius=32, fill=(255, 255, 255, 235), outline=c3 + (255,), width=10)
    pd.ellipse((210, 402, 410, 602), fill=c2 + (255,), outline=c3 + (255,), width=6)
    pd.arc((210, 402, 410, 602), 0, 360, fill=c3 + (255,), width=5)
    pd.line((310, 404, 310, 602), fill=c3 + (180,), width=4)
    pd.line((212, 502, 408, 502), fill=c3 + (180,), width=4)
    if ref_path and ref_path.exists():
        try:
            paste_contain(panel, Image.open(ref_path), (126, 92, 494, 420))
        except Exception:
            pd.polygon((310, 92, 458, 170, 420, 374, 310, 462, 200, 374, 162, 170), fill=c1 + (255,), outline=c3 + (255,))
    else:
        pd.polygon((310, 92, 458, 170, 420, 374, 310, 462, 200, 374, 162, 170), fill=c1 + (255,), outline=c3 + (255,))
    img.paste(panel, (74, 126), panel)
    return decorate_card(img.convert("RGB"), team, slot)


def draw_squad_card(team: dict, slot: dict, refs: dict[str, dict]) -> Image.Image:
    c1, c2, c3 = [rgb(c) for c in colors(team["code"])]
    img = draw_base(team).convert("RGBA")
    pitch = Image.new("RGBA", (620, 700), tuple(round(c1[i] * 0.72 + c3[i] * 0.28) for i in range(3)) + (255,))
    pd = ImageDraw.Draw(pitch)
    for x in range(0, 620, 78):
        shade = (255, 255, 255, 18) if (x // 78) % 2 else (0, 0, 0, 18)
        pd.rectangle((x, 0, x + 78, 700), fill=shade)
    pd.rectangle((34, 34, 586, 666), outline=(255, 255, 255, 210), width=5)
    pd.line((34, 350, 586, 350), fill=(255, 255, 255, 180), width=4)
    pd.ellipse((236, 276, 384, 424), outline=(255, 255, 255, 180), width=4)
    pd.rectangle((154, 34, 466, 138), outline=(255, 255, 255, 165), width=4)
    pd.rectangle((154, 562, 466, 666), outline=(255, 255, 255, 165), width=4)

    players = []
    for row in refs.values():
        if row.get("code") == team["code"] and row.get("type") == "player" and row.get("reference_path"):
            try:
                players.append((int(row["number"]), ROOT / row["reference_path"]))
            except Exception:
                pass
    players = [path for _, path in sorted(players)[:11]]
    formation = [
        (310, 598),
        (170, 488), (310, 504), (450, 488),
        (116, 368), (244, 388), (376, 388), (504, 368),
        (170, 228), (310, 206), (450, 228),
    ]
    for i, (x, y) in enumerate(formation):
        p = players[i] if i < len(players) else None
        badge = circular_portrait(p, 88, tuple(round(c1[j] * 0.55 + c2[j] * 0.45) for j in range(3)), c3)
        pitch.alpha_composite(badge, (x - 44, y - 44))
        pd.rounded_rectangle((x - 34, y + 48, x + 34, y + 72), radius=6, fill=c3 + (230,))
        label = str(i + 1)
        lf = font(18, True)
        lb = pd.textbbox((0, 0), label, font=lf)
        pd.text((x - (lb[2] - lb[0]) / 2, y + 49), label, font=lf, fill=(255, 255, 255, 240))

    img.paste(pitch, (74, 126), pitch)
    return decorate_card(img.convert("RGB"), team, slot)


def draw_player_card(team: dict, slot: dict, ref_path: Path | None, role_override: str | None = None) -> Image.Image:
    c1, c2, c3 = [rgb(c) for c in colors(team["code"])]
    img = draw_base(team)

    if ref_path and ref_path.exists():
        try:
            photo = cover_crop(Image.open(ref_path), (620, 700))
            photo = photo.filter(ImageFilter.SHARPEN)
        except Exception:
            photo = None
    else:
        photo = None

    if photo:
        img.paste(photo, (74, 126))
    else:
        panel = Image.new("RGB", (620, 700), tuple(round(c1[i] * 0.7 + c2[i] * 0.3) for i in range(3)))
        pd = ImageDraw.Draw(panel)
        pd.ellipse((190, 120, 430, 360), fill=(230, 220, 198), outline=c3, width=8)
        pd.pieslice((120, 330, 500, 720), 180, 360, fill=c1)
        pd.polygon((250, 350, 310, 520, 370, 350), fill=c2)
        img.paste(panel, (74, 126))

    return decorate_card(img, team, slot, role_override)


def draw_card(team: dict, slot: dict, ref_path: Path | None, refs: dict[str, dict], row: dict | None = None) -> Image.Image:
    if slot["type"] == "badge":
        return draw_badge_card(team, slot, ref_path)
    if slot["type"] == "squad":
        return draw_squad_card(team, slot, refs)
    return draw_player_card(team, slot, ref_path, (row or {}).get("role"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Monta figurinhas com referencias locais.")
    parser.add_argument("--team", help="Codigo da selecao, ex: BRA.")
    parser.add_argument("--format", choices=["webp", "jpg", "both"], default="webp")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    refs = read_refs()
    created = skipped = 0
    for team in read_teams():
        if args.team and team["code"] != args.team.upper():
            continue
        for slot in team["slots"]:
            code = f"{team['code']}{slot['n']:02d}"
            row = refs.get(code, {})
            ref = ROOT / row["reference_path"] if row.get("reference_path") else None
            card = None
            for ext in (["webp", "jpg"] if args.format == "both" else [args.format]):
                out = OUT_DIR / f"{team['code']}_{slot['n']:02d}.{ext}"
                if out.exists() and not args.force:
                    skipped += 1
                    continue
                if card is None:
                    card = draw_card(team, slot, ref, refs, row)
                if ext == "webp":
                    card.save(out, "WEBP", quality=94, method=6)
                else:
                    card.save(out, "JPEG", quality=94, optimize=True)
                created += 1
    print(f"Criadas: {created}")
    print(f"Puladas: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
