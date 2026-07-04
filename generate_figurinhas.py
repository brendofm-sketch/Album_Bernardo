#!/usr/bin/env python3
"""
Gera artes WebP originais para o album.

O script le a constante TEAMS do HTML, cria uma imagem para cada slot no padrao
figurinhas/COD_00.webp e pula arquivos existentes, a menos que --force seja usado.
As artes sao ilustracoes simbolicas/ficticias: nao usam escudos oficiais,
logotipos, marcas protegidas ou rostos reais.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "album_copa_2026_premium_imagens_externas.html"
OUT_DIR = ROOT / "figurinhas"
SIZE = (512, 704)

TEAM_COLORS = {
    "ALG": ("#0b8f55", "#ffffff", "#d71920"),
    "ARG": ("#74acdf", "#ffffff", "#f6b40e"),
    "AUS": ("#0b5f3a", "#ffcd00", "#ffffff"),
    "AUT": ("#ed2939", "#ffffff", "#b5121b"),
    "BEL": ("#111111", "#ffde00", "#ef3340"),
    "BIH": ("#0033a0", "#ffd100", "#ffffff"),
    "BRA": ("#009b3a", "#ffdf00", "#002776"),
    "CAN": ("#d80621", "#ffffff", "#111111"),
    "CHI": ("#d52b1e", "#0039a6", "#ffffff"),
    "COD": ("#007fff", "#f7d618", "#ce1021"),
    "COL": ("#fcd116", "#003893", "#ce1126"),
    "CRO": ("#f00000", "#ffffff", "#171796"),
    "CUW": ("#002b7f", "#f9e814", "#ffffff"),
    "CZE": ("#d7141a", "#ffffff", "#11457e"),
    "DEN": ("#c60c30", "#ffffff", "#7a0019"),
    "ECU": ("#ffdd00", "#034ea2", "#ed1c24"),
    "ENG": ("#ffffff", "#cf142b", "#1f3c88"),
    "ESP": ("#aa151b", "#f1bf00", "#111111"),
    "FRA": ("#0055a4", "#ffffff", "#ef4135"),
    "GER": ("#111111", "#dd0000", "#ffce00"),
    "GHA": ("#ce1126", "#fcd116", "#006b3f"),
    "HAI": ("#00209f", "#d21034", "#ffffff"),
    "IRQ": ("#ce1126", "#ffffff", "#000000"),
    "ITA": ("#0066cc", "#ffffff", "#009246"),
    "JOR": ("#000000", "#ffffff", "#ce1126"),
    "JPN": ("#ffffff", "#bc002d", "#1f2937"),
    "KOR": ("#ffffff", "#c60c30", "#003478"),
    "MAR": ("#c1272d", "#006233", "#ffffff"),
    "MEX": ("#006847", "#ffffff", "#ce1126"),
    "NED": ("#ff4f00", "#ffffff", "#21468b"),
    "NOR": ("#ba0c2f", "#ffffff", "#00205b"),
    "PAN": ("#005293", "#d21034", "#ffffff"),
    "PAR": ("#d52b1e", "#ffffff", "#0038a8"),
    "POL": ("#ffffff", "#dc143c", "#111111"),
    "POR": ("#006600", "#ff0000", "#ffcc00"),
    "QAT": ("#8a1538", "#ffffff", "#e6d5dc"),
    "RSA": ("#007a4d", "#ffb612", "#de3831"),
    "SCO": ("#005eb8", "#ffffff", "#111827"),
    "SEN": ("#00853f", "#fdef42", "#e31b23"),
    "SRB": ("#c6363c", "#0c4076", "#ffffff"),
    "SUI": ("#d52b1e", "#ffffff", "#7a0019"),
    "TUN": ("#e70013", "#ffffff", "#111111"),
    "TUR": ("#e30a17", "#ffffff", "#7a0019"),
    "URU": ("#75aadb", "#ffffff", "#fcd116"),
    "USA": ("#3c3b6e", "#b22234", "#ffffff"),
    "UZB": ("#0099b5", "#ffffff", "#1eb53a"),
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def shade(c: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    target = (255, 255, 255) if amount >= 0 else (0, 0, 0)
    return blend(c, target, abs(amount))


def read_teams(html_file: Path) -> list[dict]:
    text = html_file.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"const\s+TEAMS\s*=\s*(\[.*?\]);\s*const\s+IMAGE_FOLDER", text, re.S)
    if not match:
        raise RuntimeError("Nao encontrei a constante TEAMS no HTML.")
    return json.loads(match.group(1))


def colors_for(code: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    if code in TEAM_COLORS:
        return tuple(hex_to_rgb(c) for c in TEAM_COLORS[code])  # type: ignore[return-value]
    rnd = random.Random(code)
    return (
        tuple(rnd.randint(40, 230) for _ in range(3)),
        tuple(rnd.randint(40, 230) for _ in range(3)),
        tuple(rnd.randint(40, 230) for _ in range(3)),
    )


def background(draw: ImageDraw.ImageDraw, code: str, n: int, palette: tuple) -> None:
    w, h = SIZE
    c1, c2, c3 = palette
    for y in range(h):
        t = y / h
        top = blend(shade(c1, 0.45), shade(c2, 0.16), 0.35)
        bottom = blend(shade(c1, -0.10), shade(c3, -0.18), 0.55)
        draw.line([(0, y), (w, y)], fill=blend(top, bottom, t))

    rnd = random.Random(f"{code}-{n}-bg")
    for i in range(10):
        x = rnd.randint(-90, w + 50)
        y = rnd.randint(-80, h + 60)
        r = rnd.randint(24, 130)
        color = (*shade([c1, c2, c3][i % 3], rnd.uniform(0.20, 0.58)), rnd.randint(20, 48))
        draw.ellipse((x, y, x + r, y + r), fill=color)

    pitch = [(46, 250), (466, 218), (512, 704), (0, 704)]
    draw.polygon(pitch, fill=(*shade((31, 127, 72), 0.10), 118))
    for x in range(-80, w + 120, 86):
        draw.line((x, 704, x + 125, 230), fill=(255, 255, 255, 38), width=3)
    draw.arc((120, 418, 392, 690), 205, 335, fill=(255, 255, 255, 40), width=4)

    for i in range(-h, w, 104):
        draw.line((i, h, i + h, 0), fill=(*shade(c3, 0.35), 34), width=2)


def add_light(img: Image.Image) -> None:
    w, h = SIZE
    light = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(light, "RGBA")
    d.ellipse((-210, -240, w + 135, 360), fill=(255, 255, 255, 88))
    d.polygon([(0, 0), (170, 0), (0, 350)], fill=(255, 255, 255, 36))
    d.ellipse((56, 500, w - 56, h + 92), fill=(0, 0, 0, 58))
    img.alpha_composite(light.filter(ImageFilter.GaussianBlur(28)))


def add_print_finish(img: Image.Image, team: dict, slot: dict, palette: tuple) -> None:
    w, h = SIZE
    c1, c2, c3 = palette
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay, "RGBA")

    frame_mask = Image.new("L", SIZE, 0)
    md = ImageDraw.Draw(frame_mask)
    md.rounded_rectangle((18, 18, w - 18, h - 18), radius=30, fill=238)
    md.rounded_rectangle((38, 44, w - 38, h - 78), radius=18, fill=0)
    frame = Image.new("RGBA", SIZE, (255, 255, 255, 0))
    frame.putalpha(frame_mask)
    overlay.alpha_composite(frame)

    d.rounded_rectangle((38, 44, w - 38, h - 78), radius=18, fill=(0, 0, 0, 0), outline=shade(c3, 0.12) + (185,), width=5)
    d.rounded_rectangle((49, 55, w - 49, h - 89), radius=13, fill=(0, 0, 0, 0), outline=(255, 255, 255, 128), width=2)

    d.rectangle((42, 596, w - 42, 653), fill=shade(c1, -0.03) + (235,))
    d.rectangle((42, 596, w - 42, 608), fill=shade(c2, 0.10) + (245,))
    d.rectangle((42, 641, w - 42, 653), fill=shade(c3, -0.02) + (230,))
    d.rounded_rectangle((64, 616, w - 64, 634), radius=9, fill=(255, 255, 255, 80))

    d.rounded_rectangle((52, 54, 138, 92), radius=8, fill=(255, 255, 255, 210))
    d.rectangle((60, 84, 130, 88), fill=shade(c3, 0.05) + (210,))
    d.rounded_rectangle((366, 54, 460, 92), radius=8, fill=shade(c2, 0.12) + (210,))

    shine = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shine, "RGBA")
    sd.polygon([(40, 50), (132, 50), (40, 260)], fill=(255, 255, 255, 58))
    sd.polygon([(285, 44), (330, 44), (88, 626), (44, 626)], fill=(255, 255, 255, 28))
    overlay.alpha_composite(shine.filter(ImageFilter.GaussianBlur(1)))

    # Keep the decorative frame separate from official sticker layouts or marks.
    img.alpha_composite(overlay)


def draw_ball(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.ellipse(box, fill=(246, 248, 252), outline=(30, 41, 59), width=5)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    r = (x2 - x1) // 7
    pts = []
    for i in range(5):
        a = -math.pi / 2 + i * math.tau / 5
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    draw.polygon(pts, fill=(25, 34, 50))
    draw.arc((x1 + 18, y1 + 28, x2 - 18, y2 - 28), 200, 340, fill=(25, 34, 50), width=5)
    draw.arc((x1 + 28, y1 + 18, x2 - 28, y2 - 18), 20, 160, fill=(25, 34, 50), width=5)


def draw_badge(draw: ImageDraw.ImageDraw, team: dict, slot: dict, palette: tuple) -> None:
    c1, c2, c3 = palette
    shield = [(256, 112), (384, 172), (356, 404), (256, 532), (156, 404), (128, 172)]
    draw.polygon([(x + 10, y + 16) for x, y in shield], fill=(0, 0, 0, 72))
    draw.polygon(shield, fill=shade(c1, 0.05), outline=shade(c3, 0.40))
    inner = [(256, 150), (346, 192), (328, 395), (256, 496), (184, 395), (166, 192)]
    draw.polygon(inner, fill=shade(c2, 0.10))
    draw.pieslice((178, 205, 334, 361), 0, 180, fill=shade(c3, 0.10))
    draw.rectangle((184, 282, 328, 376), fill=shade(c1, -0.04))
    draw.pieslice((188, 260, 324, 462), 180, 360, fill=shade(c2, -0.02))
    draw_ball(draw, (206, 234, 306, 334))
    draw.polygon([(256, 348), (280, 413), (350, 413), (292, 452), (314, 518), (256, 477), (198, 518), (220, 452), (162, 413), (232, 413)], fill=shade(c3, 0.15))
    draw.arc((190, 98, 322, 230), 205, 335, fill=(255, 255, 255, 160), width=7)


def skin_and_hair(seed: int) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    skins = [(92, 54, 36), (130, 77, 48), (174, 108, 67), (214, 155, 103), (238, 190, 143), (102, 66, 54)]
    hairs = [(24, 24, 27), (57, 35, 24), (94, 61, 38), (139, 92, 48), (213, 160, 73)]
    return skins[seed % len(skins)], hairs[(seed // 7) % len(hairs)]


def draw_player(draw: ImageDraw.ImageDraw, team: dict, slot: dict, palette: tuple, xoff: int = 0, scale: float = 1.0) -> None:
    c1, c2, c3 = palette
    seed = sum(ord(ch) for ch in f"{team['code']}-{slot['n']}-{xoff}")
    skin, hair = skin_and_hair(seed)
    cx = 256 + xoff
    torso_y = int(470 * scale + (1 - scale) * 306)
    shoulder = int(164 * scale)
    head_r = int(82 * scale)

    draw.ellipse((cx - shoulder, torso_y + 42, cx + shoulder, torso_y + 98), fill=(0, 0, 0, 76))
    draw.pieslice((cx - shoulder, torso_y - 20, cx + shoulder, torso_y + 258), 180, 360, fill=shade(c1, -0.02))
    draw.polygon([(cx - shoulder, torso_y + 92), (cx, torso_y - 12), (cx + shoulder, torso_y + 92), (cx + int(128 * scale), torso_y + 226), (cx - int(128 * scale), torso_y + 226)], fill=shade(c1, 0.02))
    draw.polygon([(cx - int(34 * scale), torso_y - 3), (cx, torso_y + int(86 * scale)), (cx + int(34 * scale), torso_y - 3), (cx + int(76 * scale), torso_y + 212), (cx - int(76 * scale), torso_y + 212)], fill=shade(c2, 0.10))
    draw.line((cx - shoulder + 12, torso_y + 82, cx + shoulder - 12, torso_y + 82), fill=shade(c3, 0.18), width=max(4, int(10 * scale)))
    draw.line((cx - int(116 * scale), torso_y + 126, cx + int(116 * scale), torso_y + 126), fill=(255, 255, 255, 78), width=max(2, int(4 * scale)))

    neck = (cx - int(32 * scale), torso_y - int(60 * scale), cx + int(32 * scale), torso_y + int(22 * scale))
    draw.rounded_rectangle(neck, radius=18, fill=shade(skin, -0.04))
    face = (cx - head_r, torso_y - int(218 * scale), cx + head_r, torso_y - int(70 * scale))
    draw.ellipse((face[0] + 10, face[1] + 14, face[2] + 10, face[3] + 18), fill=(0, 0, 0, 58))
    draw.ellipse(face, fill=skin)

    hairline = [(cx - head_r + 8, torso_y - int(165 * scale)), (cx - head_r + 26, torso_y - int(238 * scale)), (cx + int(20 * scale), torso_y - int(245 * scale)), (cx + head_r - 4, torso_y - int(190 * scale)), (cx + head_r - 8, torso_y - int(166 * scale))]
    draw.pieslice((face[0], face[1] - int(16 * scale), face[2], face[1] + int(86 * scale)), 180, 360, fill=hair)
    draw.polygon(hairline, fill=hair)
    eye_y = torso_y - int(136 * scale)
    eye_dx = int(27 * scale)
    eye_r = max(2, int(5 * scale))
    draw.ellipse((cx - eye_dx - eye_r, eye_y - eye_r, cx - eye_dx + eye_r, eye_y + eye_r), fill=(17, 24, 39))
    draw.ellipse((cx + eye_dx - eye_r, eye_y - eye_r, cx + eye_dx + eye_r, eye_y + eye_r), fill=(17, 24, 39))
    draw.arc((cx - int(32 * scale), torso_y - int(115 * scale), cx + int(34 * scale), torso_y - int(76 * scale)), 15, 165, fill=shade(skin, -0.52), width=max(2, int(4 * scale)))
    draw.line((cx, eye_y + int(8 * scale), cx - int(8 * scale), eye_y + int(30 * scale), cx + int(8 * scale), eye_y + int(31 * scale)), fill=shade(skin, -0.20), width=max(2, int(3 * scale)))
    draw.arc((cx - int(58 * scale), torso_y - int(196 * scale), cx - int(14 * scale), torso_y - int(174 * scale)), 188, 344, fill=shade(hair, 0.20), width=max(2, int(4 * scale)))
    draw.arc((cx + int(14 * scale), torso_y - int(196 * scale), cx + int(58 * scale), torso_y - int(174 * scale)), 196, 352, fill=shade(hair, 0.20), width=max(2, int(4 * scale)))


def draw_squad(draw: ImageDraw.ImageDraw, team: dict, slot: dict, palette: tuple) -> None:
    offsets = [-128, 0, 128, -64, 64]
    scales = [0.70, 0.82, 0.70, 0.58, 0.58]
    order = [3, 4, 0, 2, 1]
    for idx in order:
        fake_slot = {"n": slot["n"] + idx * 3}
        draw_player(draw, team, fake_slot, palette, offsets[idx], scales[idx])
    draw_ball(draw, (210, 504, 302, 596))


def prompt_for(team: dict, slot: dict) -> str:
    name = slot["name"]
    country = team["name"]
    code = team["code"]
    if slot["type"] == "badge":
        return (
            f"Ilustracao original em estilo figurinha esportiva digital premium para {country} ({code}), "
            "simbolo ficticio com escudo geometrico original, bola ou trofeu, borda de figurinha colecionavel classica, cores inspiradas na selecao, "
            "sem brasao oficial, sem logotipo, sem texto, sem marca d'agua."
        )
    if slot["type"] == "squad":
        return (
            f"Ilustracao original em estilo figurinha esportiva digital premium para {country} ({code}), "
            "grupo de jogadores de futebol ficticios, uniformes com cores da selecao sem logotipos oficiais, "
            "borda branca de figurinha colecionavel, fundo esportivo abstrato, acabamento 3D cartoon editorial, sem rostos reais, sem texto."
        )
    return (
        f"Ilustracao original em estilo figurinha esportiva digital premium, jogador de futebol ficticio inspirado "
        f"na selecao {country} ({code}), figurinha {name}, uniforme com cores de {country} sem logotipos oficiais, "
        "busto frontal, expressao confiante, borda branca de figurinha colecionavel classica, fundo abstrato esportivo, luz de estudio, acabamento 3D cartoon "
        "editorial, alta qualidade, card vertical, sem texto, sem marca d'agua."
    )


def render_card(team: dict, slot: dict) -> Image.Image:
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    palette = colors_for(team["code"])
    background(draw, team["code"], slot["n"], palette)
    if slot["type"] == "badge":
        draw_badge(draw, team, slot, palette)
    elif slot["type"] == "squad":
        draw_squad(draw, team, slot, palette)
    else:
        draw_player(draw, team, slot, palette)
    add_light(img)
    add_print_finish(img, team, slot, palette)
    return img.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera figurinhas WebP originais para o album.")
    parser.add_argument("--force", action="store_true", help="Sobrescreve imagens existentes.")
    parser.add_argument("--limit", type=int, default=0, help="Gera apenas N imagens, util para teste.")
    args = parser.parse_args()

    teams = read_teams(HTML_FILE)
    OUT_DIR.mkdir(exist_ok=True)

    prompts = []
    created = skipped = 0
    for team in teams:
        for slot in team["slots"]:
            file_name = f"{team['code']}_{slot['n']:02d}.webp"
            out = OUT_DIR / file_name
            prompt = prompt_for(team, slot)
            prompts.append({"file": f"figurinhas/{file_name}", "team": team["name"], "code": team["code"], "number": slot["n"], "name": slot["name"], "type": slot["type"], "prompt": prompt})
            if out.exists() and not args.force:
                skipped += 1
                continue
            render_card(team, slot).save(out, "WEBP", quality=92, method=6)
            created += 1
            if args.limit and created >= args.limit:
                break
        if args.limit and created >= args.limit:
            break

    (OUT_DIR / "prompts_manifest.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Figurinhas criadas: {created}")
    print(f"Figurinhas puladas: {skipped}")
    print(f"Manifesto de prompts: {OUT_DIR / 'prompts_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
