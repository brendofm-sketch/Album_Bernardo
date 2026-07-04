#!/usr/bin/env python3
"""Extrai figurinhas do PDF fornecido e casa por nome com o HTML.

O PDF e renderizado em alta resolucao, recortado em grade 4x4 e lido por OCR.
Somente recortes com match confiavel de nome sao salvos em figurinhas/COD_00.webp.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import easyocr
import fitz
import numpy as np
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
PDF_FILE = next(ROOT.glob("*101 paginas completo.pdf"), ROOT / "TODAS LAS FIGURITAS EN PDF (4).pdf")
HTML_FILE = ROOT / "album_copa_2026_premium_imagens_externas.html"
CSV_FILE = ROOT / "referencias" / "referencias_jogadores.csv"
OUT_DIR = ROOT / "figurinhas"
CROP_DIR = ROOT / ("pdf_101_recortes" if "101" in PDF_FILE.name else "pdf_recortes")
REPORT_FILE = ROOT / ("pdf_101_recortes_manifest.csv" if "101" in PDF_FILE.name else "pdf_recortes_manifest.csv")
SIZE = (768, 1056)

RENDER_SCALE = 3
CARD_ASPECT = 180 / 140

BADGE_ALIASES = {
    "ARG": ["AFA", "ARGENTINA"],
    "BRA": ["CBF", "BRASIL", "BRAZIL"],
    "GER": ["DEUTSCHER", "FUSSBALL BUND", "DFB"],
    "KSA": ["SAFF", "SAUDI"],
    "USA": ["USMNT", "U S SOCCER"],
    "MEX": ["FMF", "MEXICO"],
    "CAN": ["CANADA SOCCER", "CANADA"],
    "ENG": ["ENGLAND", "THREE LIONS"],
    "FRA": ["FFF", "FRANCE"],
    "ESP": ["RFEF", "ESPANA", "SPAIN"],
    "POR": ["FPF", "PORTUGAL"],
    "ITA": ["FIGC", "ITALIA"],
}

TEAM_ALIASES = {
    "MEX": ["MEXICO", "MEX"],
    "RSA": ["SOUTH AFRICA", "AFRICA DO SUL", "SOUTHAFRICA", "RSA"],
    "KOR": ["KOREA REPUBLIC", "SOUTH KOREA", "KOREA", "COREIA DO SUL", "KOR"],
    "CZE": ["CZECH REPUBLIC", "CZECHIA", "REPUBLICA TCHECA", "CZE"],
    "CAN": ["CANADA", "CAN"],
    "BIH": ["BOSNIA", "BOSNIA AND HERZEGOVINA", "BOSNIA E HERZEGOVINA", "BIH"],
    "QAT": ["QATAR", "CATAR", "QAT"],
    "SUI": ["SWITZERLAND", "SUICA", "SUISSE", "SUI"],
    "BRA": ["BRAZIL", "BRASIL", "BRA"],
    "MAR": ["MOROCCO", "MARROCOS", "MAR"],
    "HAI": ["HAITI", "HAI"],
    "SCO": ["SCOTLAND", "ESCOCIA", "SCO"],
    "USA": ["UNITED STATES", "ESTADOS UNIDOS", "USMNT", "USA"],
    "PAR": ["PARAGUAY", "PARAGUAI", "PAR"],
    "AUS": ["AUSTRALIA", "AUS"],
    "TUR": ["TURKIYE", "TURKEY", "TURQUIA", "TUR"],
    "GER": ["GERMANY", "ALEMANHA", "DEUTSCHLAND", "DFB", "GER"],
    "CUW": ["CURACAO", "CURACAO", "CUW"],
    "CIV": ["COTE D IVOIRE", "IVORY COAST", "COSTA DO MARFIM", "CIV"],
    "ECU": ["ECUADOR", "EQUADOR", "ECU"],
    "NED": ["NETHERLANDS", "HOLANDA", "NEDERLAND", "NED"],
    "JPN": ["JAPAN", "JAPAO", "JPN"],
    "SWE": ["SWEDEN", "SUECIA", "SVERIGE", "SWE"],
    "TUN": ["TUNISIA", "TUNISIE", "TUNISIA", "TUN"],
    "BEL": ["BELGIUM", "BELGICA", "BEL"],
    "EGY": ["EGYPT", "EGITO", "EGY"],
    "IRN": ["IRAN", "IRN"],
    "NZL": ["NEW ZEALAND", "NOVA ZELANDIA", "NZL"],
    "ESP": ["SPAIN", "ESPANA", "ESP"],
    "CPV": ["CABO VERDE", "CAPE VERDE", "CPV"],
    "KSA": ["SAUDI ARABIA", "ARABIA SAUDITA", "SAUDI", "KSA"],
    "URU": ["URUGUAY", "URUGUAI", "URU"],
    "FRA": ["FRANCE", "FRANCA", "FRA"],
    "SEN": ["SENEGAL", "SEN"],
    "IRQ": ["IRAQ", "IRAQUE", "IRQ"],
    "NOR": ["NORWAY", "NORUEGA", "NOR"],
    "ARG": ["ARGENTINA", "AFA", "ARG"],
    "ALG": ["ALGERIA", "ARGELIA", "ALGERIE", "ALG"],
    "AUT": ["AUSTRIA", "AUT"],
    "JOR": ["JORDAN", "JORDANIA", "JOR"],
    "POR": ["PORTUGAL", "POR"],
    "COD": ["CONGO DR", "RD CONGO", "CONGO", "COD"],
    "UZB": ["UZBEKISTAN", "UZBEQUISTAO", "UZB"],
    "COL": ["COLOMBIA", "COL"],
    "ENG": ["ENGLAND", "INGLATERRA", "ENG"],
    "CRO": ["CROATIA", "CROACIA", "CRO"],
    "GHA": ["GHANA", "GHA"],
    "PAN": ["PANAMA", "PAN"],
}

PLAYER_ALIASES = {
    ("RSA", 10): ["Sipho Sibisi"],
    ("RSA", 15): ["Yaya Sithole", "Vava Sithole"],
}

# Posicoes conferidas visualmente no PDF. O OCR nem sempre le escudos cromados
# e cards de elenco, entao estes slots entram por coordenada de pagina/grade.
LEGACY_POSITION_OVERRIDES = {
    (1, 1, 1): ("GER", 1),
    (3, 1, 1): ("ALG", 1),
    (4, 1, 1): ("ARG", 1),
    (5, 2, 1): ("ARG", 13),
    (7, 1, 1): ("AUT", 1),
    (8, 1, 1): ("BEL", 1),
    (9, 1, 1): ("BIH", 1),
    (10, 1, 3): ("BRA", 13),
    (10, 2, 1): ("BRA", 1),
    (11, 1, 4): ("BRA", 8),
    (13, 1, 1): ("CAN", 1),
    (16, 1, 1): ("KOR", 1),
    (17, 1, 1): ("CIV", 1),
    (19, 1, 1): ("CUW", 1),
    (20, 1, 1): ("ECU", 1),
    (21, 1, 1): ("EGY", 1),
    (22, 1, 1): ("SCO", 1),
    (23, 1, 1): ("ESP", 1),
    (25, 1, 1): ("USA", 1),
    (27, 1, 1): ("GHA", 1),
    (28, 1, 1): ("HAI", 1),
    (29, 1, 1): ("ENG", 1),
    (31, 1, 1): ("IRQ", 1),
    (32, 1, 1): ("JPN", 1),
    (33, 1, 1): ("JOR", 1),
    (37, 1, 1): ("NOR", 1),
    (38, 1, 1): ("NZL", 1),
    (39, 1, 1): ("NED", 1),
    (42, 1, 1): ("POR", 1),
    (45, 1, 1): ("COD", 1),
    (46, 1, 1): ("CZE", 1),
    (49, 1, 1): ("SWE", 1),
    (50, 1, 1): ("SUI", 1),
    (51, 1, 1): ("TUN", 1),
    (52, 1, 1): ("TUR", 1),
    (52, 1, 2): ("TUR", 2),
    (53, 1, 1): ("URU", 1),
    (54, 1, 1): ("UZB", 1),
}

# Ordem conferida visualmente no PDF "album 101 paginas completo".
# Os cards 01 (escudo/cromada) e 13 (elenco) sao muito propensos a falso
# positivo por OCR, entao ficam fixos por pagina/linha/coluna.
ORDERED_101_POSITION_OVERRIDES = {
    (1, 1, 1): ("MEX", 1), (1, 1, 2): ("MEX", 13),
    (3, 1, 1): ("RSA", 1), (3, 3, 4): ("RSA", 13),
    (5, 1, 1): ("KOR", 1), (5, 3, 4): ("KOR", 13),
    (7, 1, 1): ("CZE", 1), (8, 1, 4): ("CZE", 13),
    (9, 1, 1): ("CAN", 1), (10, 1, 4): ("CAN", 13),
    (11, 1, 1): ("BIH", 1), (12, 1, 4): ("BIH", 13),
    (14, 1, 3): ("QAT", 1), (14, 1, 4): ("QAT", 13),
    (15, 1, 1): ("SUI", 1), (16, 1, 1): ("SUI", 13),
    (18, 2, 1): ("BRA", 1), (18, 1, 3): ("BRA", 13),
    (19, 1, 1): ("MAR", 1), (19, 4, 4): ("MAR", 13),
    (21, 1, 1): ("HAI", 1), (22, 1, 4): ("HAI", 13),
    (23, 1, 1): ("SCO", 1), (24, 1, 4): ("SCO", 13),
    (25, 1, 1): ("USA", 1), (26, 1, 4): ("USA", 13),
    (27, 1, 1): ("PAR", 1), (27, 4, 4): ("PAR", 13),
    (30, 1, 4): ("AUS", 1), (29, 4, 2): ("AUS", 13),
    (31, 1, 2): ("TUR", 1), (31, 1, 3): ("TUR", 13),
    (33, 1, 1): ("GER", 1), (34, 1, 4): ("GER", 13),
    (35, 1, 1): ("CUW", 1), (36, 1, 2): ("CUW", 13),
    (37, 1, 1): ("CIV", 1), (37, 1, 2): ("CIV", 13),
    (39, 1, 1): ("ECU", 1), (39, 1, 2): ("ECU", 13),
    (41, 1, 1): ("NED", 1), (41, 1, 2): ("NED", 13),
    (43, 3, 3): ("JPN", 1), (43, 1, 3): ("JPN", 13),
    (45, 1, 1): ("SWE", 1), (45, 4, 4): ("SWE", 13),
    (47, 1, 1): ("TUN", 1), (48, 1, 4): ("TUN", 13),
    (49, 1, 1): ("BEL", 1), (50, 1, 4): ("BEL", 13),
    (51, 1, 1): ("EGY", 1), (52, 1, 1): ("EGY", 13),
    (53, 1, 1): ("IRN", 1), (53, 4, 4): ("IRN", 13),
    (55, 1, 1): ("NZL", 1), (55, 1, 2): ("NZL", 13),
    (57, 1, 1): ("ESP", 1), (57, 1, 2): ("ESP", 13),
    (59, 3, 1): ("CPV", 1), (60, 1, 2): ("CPV", 13),
    (61, 1, 1): ("KSA", 1), (62, 1, 1): ("KSA", 13),
    (63, 1, 3): ("URU", 1), (63, 1, 4): ("URU", 13),
    (65, 1, 1): ("FRA", 1), (65, 1, 2): ("FRA", 13),
    (67, 1, 1): ("SEN", 1), (67, 4, 2): ("SEN", 13),
    (69, 1, 1): ("IRQ", 1), (70, 1, 4): ("IRQ", 13),
    (71, 1, 1): ("NOR", 1), (71, 1, 2): ("NOR", 13),
    (73, 1, 1): ("ARG", 1), (73, 1, 2): ("ARG", 13),
    (75, 1, 1): ("ALG", 1), (76, 1, 4): ("ALG", 13),
    (77, 1, 1): ("AUT", 1), (78, 1, 2): ("AUT", 13),
    (79, 1, 1): ("JOR", 1), (80, 1, 1): ("JOR", 13),
    (81, 1, 1): ("POR", 1), (81, 1, 2): ("POR", 13),
    (83, 1, 1): ("COD", 1), (84, 1, 4): ("COD", 13),
    (85, 1, 1): ("UZB", 1), (86, 1, 3): ("UZB", 13),
    (87, 1, 1): ("COL", 1), (87, 1, 2): ("COL", 13),
    (89, 1, 3): ("ENG", 1), (89, 1, 4): ("ENG", 13),
    (91, 4, 2): ("CRO", 1), (91, 4, 1): ("CRO", 13),
    (93, 1, 1): ("GHA", 1), (93, 3, 1): ("GHA", 13),
    (95, 1, 1): ("PAN", 1), (95, 4, 4): ("PAN", 13),
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("JR.", "JUNIOR").replace("JR", "JUNIOR")
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def compact(value: str) -> str:
    return normalize(value).replace(" ", "")


def read_teams() -> list[dict]:
    text = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"const\s+TEAMS\s*=\s*(\[.*?\]);\s*const\s+IMAGE_FOLDER", text, re.S)
    if not match:
        raise RuntimeError("Nao encontrei TEAMS no HTML.")
    return json.loads(match.group(1))


def sticker_targets() -> list[dict]:
    targets = []
    for team in read_teams():
        for slot in team["slots"]:
            if slot["type"] == "player":
                aliases = [slot["name"], *PLAYER_ALIASES.get((team["code"], slot["n"]), [])]
            elif slot["type"] == "badge":
                aliases = [*BADGE_ALIASES.get(team["code"], []), *TEAM_ALIASES.get(team["code"], [])]
            elif slot["type"] == "squad":
                team_aliases = TEAM_ALIASES.get(team["code"], [team["name"]])
                aliases = [f"WE ARE {alias}" for alias in team_aliases] + [f"{alias} TEAM" for alias in team_aliases]
            else:
                aliases = [slot["name"]]
            targets.append({
                "code": team["code"],
                "number": slot["n"],
                "team": team["name"],
                "name": slot["name"],
                "type": slot["type"],
                "aliases": [normalize(alias) for alias in aliases if normalize(alias)],
                "norm": normalize(slot["name"] if slot["type"] == "player" else team["name"]),
            })
    return targets


def target_map(targets: list[dict]) -> dict[str, dict]:
    return {f"{target['code']}{target['number']:02d}": target for target in targets}


def crop_to_card(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("RGB")
    return img.resize(SIZE, Image.Resampling.LANCZOS)


def is_blank_crop(img: Image.Image) -> bool:
    arr = np.array(img.convert("RGB").resize((80, 104)))
    non_white = np.any(arr < 245, axis=2).mean()
    return non_white < 0.035


def page_grid_boxes(page_img: Image.Image) -> list[tuple[int, int, int, int]]:
    arr = np.array(page_img)
    # Ignore page watermarks/signatures and derive the 4x4 sticker grid.
    work_h = int(arr.shape[0] * 0.94)
    work = arr[:work_h]
    mask = np.any(work < 245, axis=2)
    row_counts = mask.sum(axis=1)
    segments = []
    start = None
    threshold = max(80, int(arr.shape[1] * 0.05))
    for idx, count in enumerate(row_counts):
        if count > threshold and start is None:
            start = idx
        elif start is not None and count <= threshold:
            segments.append((start, idx))
            start = None
    if start is not None:
        segments.append((start, len(row_counts)))
    if segments:
        tall_segments = [item for item in segments if item[1] - item[0] > int(80 * RENDER_SCALE)]
        useful_segments = tall_segments or segments
        top = min(item[0] for item in useful_segments)
        bottom = max(item[1] for item in useful_segments)
        mask = mask[top:bottom]
        ys, xs = np.where(mask)
        ys = ys + top
    else:
        ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        raise RuntimeError("Nao encontrei conteudo colorido na pagina.")
    left, right = int(xs.min()), int(xs.max()) + 1
    top, bottom = int(ys.min()), int(ys.max()) + 1

    # Trim small accidental edges, then split the detected sheet into 4x4 cells.
    pad = max(2, int(2 * RENDER_SCALE))
    left = max(0, left - pad)
    right = min(arr.shape[1], right + pad)
    top = max(0, top - pad)
    bottom = min(work_h, bottom + pad)

    cell_w = (right - left) / 4
    expected_cell_h = cell_w * CARD_ASPECT
    row_count = max(1, min(4, round((bottom - top) / expected_cell_h)))
    cell_h = expected_cell_h
    boxes = []
    for row in range(row_count):
        for col in range(4):
            x1 = round(left + col * cell_w)
            y1 = round(top + row * cell_h)
            x2 = round(left + (col + 1) * cell_w)
            y2 = round(top + (row + 1) * cell_h)
            boxes.append((x1, y1, x2, y2))
    return boxes


def looks_like_player_card(norm_text: str) -> bool:
    player_markers = ("KG", " FC", "FC ", " CF", "CF ", " SC", "SC ", " AC", "AC ", " RC", "RC ", " UD", "UD ",
                      "CITY", "UNITED", "CLUB", "CALCIO", "MADRID", "ARSENAL", "CHELSEA", "LIVERPOOL")
    return any(marker in f" {norm_text} " for marker in player_markers)


def looks_like_squad_card(norm_text: str) -> bool:
    compact_text = norm_text.replace(" ", "")
    return "WEARE" in compact_text or len(compact_text) <= 10


def best_match(text: str, targets: list[dict], used: set[str]) -> tuple[dict | None, float]:
    norm_text = normalize(text)
    compact_text = compact(text)
    text_tokens = [token for token in norm_text.split() if len(token) > 1]
    best = None
    score = 0.0
    for target in targets:
        key = f"{target['code']}{target['number']:02d}"
        if key in used:
            continue
        if target["type"] == "badge" and looks_like_player_card(norm_text):
            continue
        candidates = target["aliases"] or [target["norm"]]
        ratio = 0.0
        for name in candidates:
            if not name:
                continue
            candidate_ratio = SequenceMatcher(None, name, norm_text).ratio()
            compact_name = name.replace(" ", "")
            if compact_name and compact_text:
                compact_ratio = SequenceMatcher(None, compact_name, compact_text).ratio()
                if compact_name in compact_text:
                    compact_ratio = max(compact_ratio, 0.98)
                candidate_ratio = max(candidate_ratio, compact_ratio)
            if name in norm_text:
                candidate_ratio = max(candidate_ratio, 0.98)
            elif all(part in norm_text for part in name.split() if len(part) > 2):
                candidate_ratio = max(candidate_ratio, 0.92)
            else:
                name_tokens = [token for token in name.split() if len(token) > 1]
                if name_tokens and text_tokens:
                    token_scores = []
                    for name_token in name_tokens:
                        token_scores.append(max(SequenceMatcher(None, name_token, text_token).ratio() for text_token in text_tokens))
                    token_ratio = sum(token_scores) / len(token_scores)
                    if len(name_tokens) > 1 and token_ratio > 0.82:
                        candidate_ratio = max(candidate_ratio, token_ratio)
            ratio = max(ratio, candidate_ratio)
        if ratio > score:
            best = target
            score = ratio
    return best, score


def write_source_to_csv(matches: list[dict]) -> None:
    if not CSV_FILE.exists():
        return
    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    by_key = {f"{row['code']}{int(row['number']):02d}": row for row in rows}
    for item in matches:
        if item["status"] != "matched":
            continue
        row = by_key.get(item["matched_key"])
        if not row:
            continue
        row["reference_path"] = f"pdf_recortes\\{item['crop_file']}"
        row["reference_url"] = str(PDF_FILE.name)
        row["page_url"] = str(PDF_FILE.name)
        row["license"] = "PDF fornecido pelo usuario / revisar direitos de uso"
        row["credit"] = "PDF local"
        row["status"] = "extracted_pdf"
    with CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    global PDF_FILE, CROP_DIR, REPORT_FILE
    parser = argparse.ArgumentParser(description="Recorta figurinhas do PDF e salva por match de nome.")
    parser.add_argument("--pdf", type=Path, default=PDF_FILE)
    parser.add_argument("--threshold", type=float, default=0.86)
    parser.add_argument("--limit-pages", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    PDF_FILE = args.pdf if args.pdf.is_absolute() else ROOT / args.pdf
    is_ordered_101 = "101" in PDF_FILE.name
    CROP_DIR = ROOT / ("pdf_101_recortes" if is_ordered_101 else "pdf_recortes")
    REPORT_FILE = ROOT / ("pdf_101_recortes_manifest.csv" if is_ordered_101 else "pdf_recortes_manifest.csv")
    position_overrides = ORDERED_101_POSITION_OVERRIDES if is_ordered_101 else LEGACY_POSITION_OVERRIDES

    CROP_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    targets = sticker_targets()
    targets_by_key = target_map(targets)
    teams = read_teams()
    code_order = [item["code"] for item in teams]
    used: set[str] = set()
    rows = []
    current_code = ""

    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    doc = fitz.open(PDF_FILE)
    pages = min(doc.page_count, args.limit_pages) if args.limit_pages else doc.page_count

    for page_index in range(pages):
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE), alpha=False)
        page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        boxes = page_grid_boxes(page_img)
        for idx, box in enumerate(boxes):
            row_index = idx // 4
            col_index = idx % 4
            crop = page_img.crop(box)
            if is_blank_crop(crop):
                continue
            crop_name = f"p{page_index+1:03d}_r{row_index+1}c{col_index+1}.jpg"
            crop_path = CROP_DIR / crop_name
            crop.save(crop_path, "JPEG", quality=95)

            # The player name is usually in the lower half. OCR there first,
            # with the full crop as backup for foil/special layouts.
            w, h = crop.size
            lower = crop.crop((0, int(h * 0.52), w, h))
            text_parts = reader.readtext(np.array(lower), detail=0, paragraph=False)
            if len(" ".join(text_parts)) < 4:
                text_parts = reader.readtext(np.array(crop), detail=0, paragraph=False)
            ocr_text = " ".join(text_parts)
            override = position_overrides.get((page_index + 1, row_index + 1, col_index + 1))
            target = None
            score = 0.0
            if override:
                override_key = f"{override[0]}{override[1]:02d}"
                if override_key not in used:
                    target = targets_by_key.get(override_key)
                    score = 1.0 if target else 0.0
            if not target:
                target, score = best_match(ocr_text, targets, used)
            if is_ordered_101 and (not target or score < args.threshold):
                norm_text = normalize(ocr_text)
                if current_code and looks_like_player_card(norm_text):
                    local_targets = [item for item in targets if item["code"] == current_code and item["type"] == "player"]
                    local_target, local_score = best_match(ocr_text, local_targets, used)
                    if local_target and local_score >= 0.78:
                        target = local_target
                        score = local_score

                next_code = ""
                if current_code and current_code in code_order:
                    idx_code = code_order.index(current_code)
                    if idx_code + 1 < len(code_order):
                        next_code = code_order[idx_code + 1]
                elif code_order:
                    next_code = code_order[0]

                if next_code and f"{next_code}01" not in used and col_index == 0 and ("FIFA" in norm_text or "WORLD" in norm_text or "CUP" in norm_text):
                    target = targets_by_key.get(f"{next_code}01")
                    score = 1.0 if target else score
                    current_code = next_code
                elif current_code and f"{current_code}13" not in used and looks_like_squad_card(norm_text):
                    target = targets_by_key.get(f"{current_code}13")
                    score = 1.0 if target else score
            status = "unmatched"
            key = ""
            out_file = ""
            if target and score >= args.threshold:
                key = f"{target['code']}{target['number']:02d}"
                used.add(key)
                current_code = target["code"]
                out_file = f"{target['code']}_{target['number']:02d}.webp"
                status = "matched"
                if not args.dry_run:
                    crop_to_card(crop).save(OUT_DIR / out_file, "WEBP", quality=95, method=6)
            rows.append({
                "page": page_index + 1,
                "row": row_index + 1,
                "col": col_index + 1,
                "crop_file": crop_name,
                "ocr_text": ocr_text,
                "matched_key": key,
                "matched_name": target["name"] if target else "",
                "score": f"{score:.3f}",
                "out_file": out_file,
                "status": status,
            })
        print(f"Pagina {page_index+1}/{pages} processada")

    with REPORT_FILE.open("w", newline="", encoding="utf-8") as fh:
        fields = ["page", "row", "col", "crop_file", "ocr_text", "matched_key", "matched_name", "score", "out_file", "status"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    if not args.dry_run:
        write_source_to_csv(rows)
    print(f"Matches: {sum(1 for row in rows if row['status'] == 'matched')}")
    print(f"Relatorio: {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
