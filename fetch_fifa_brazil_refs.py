#!/usr/bin/env python3
"""
Baixa fotos do elenco do Brasil a partir da API publica usada pela pagina FIFA /squad.

As fotos sao casadas pelo nome do jogador no HTML/CSV. Quando o jogador do checklist
nao aparece no elenco atual da FIFA, a referencia existente e preservada.
"""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from pathlib import Path

import requests
from PIL import Image


ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "album_copa_2026_premium_imagens_externas.html"
CSV_FILE = ROOT / "referencias" / "referencias_jogadores.csv"
REF_DIR = ROOT / "referencias"
FIFA_SQUAD_URL = "https://api.fifa.com/api/v3/teams/43924/squad?idCompetition=17&idSeason=285023&language=pt"
FIFA_PAGE_URL = "https://www.fifa.com/pt/tournaments/mens/worldcup/canadamexicousa2026/teams/brazil/squad"


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("jr.", "junior").replace("jr", "junior")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def description(values: list[dict] | None) -> str:
    if not values:
        return ""
    for locale in ("pt-BR", "en-GB"):
        for item in values:
            if item.get("Locale") == locale and item.get("Description"):
                return item["Description"]
    return values[0].get("Description", "")


def read_teams() -> list[dict]:
    text = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"const\s+TEAMS\s*=\s*(\[.*?\]);\s*const\s+IMAGE_FOLDER", text, re.S)
    if not match:
        raise RuntimeError("Nao encontrei TEAMS no HTML.")
    return json.loads(match.group(1))


def read_csv() -> tuple[list[str], list[dict]]:
    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def fifa_players() -> dict[str, dict]:
    response = requests.get(FIFA_SQUAD_URL, timeout=40, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    response.raise_for_status()
    data = response.json()
    players = {}
    for player in data.get("Players", []):
        names = {description(player.get("PlayerName")), description(player.get("ShortName"))}
        picture = (player.get("PlayerPicture") or {}).get("PictureUrl")
        if not picture:
            continue
        for name in names:
            key = normalize(name)
            if key:
                players[key] = {"name": name, "url": picture, "id": player.get("IdPlayer", ""), "jersey": player.get("JerseyNum", "")}
    return players


def image_url(base_url: str) -> str:
    return f"{base_url}?&io=transform:fill,aspectratio:1x1,width:900,gravity:top&quality=90"


def download_as_jpg(url: str, out: Path) -> None:
    response = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*"})
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    image.save(out, "JPEG", quality=94, optimize=True)


def main() -> int:
    REF_DIR.mkdir(exist_ok=True)
    fields, rows = read_csv()
    players = fifa_players()
    brazil = next(team for team in read_teams() if team["code"] == "BRA")
    slot_by_number = {slot["n"]: slot for slot in brazil["slots"]}
    updated = []
    missing = []

    for row in rows:
        if row.get("code") != "BRA" or row.get("type") != "player":
            continue
        slot = slot_by_number.get(int(row["number"]))
        if not slot:
            continue
        key = normalize(slot["name"])
        player = players.get(key)
        if not player:
            missing.append(slot["name"])
            continue
        direct_url = image_url(player["url"])
        out = REF_DIR / f"BRA_{int(row['number']):02d}.jpg"
        download_as_jpg(direct_url, out)
        row["reference_path"] = str(out.relative_to(ROOT))
        row["reference_url"] = direct_url
        row["page_url"] = FIFA_PAGE_URL
        row["license"] = "FIFA source image / review usage rights"
        row["artist"] = ""
        row["credit"] = "FIFA Digital Hub"
        row["status"] = "downloaded_fifa_squad"
        updated.append(slot["name"])

    with CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Atualizados pela FIFA: {len(updated)}")
    for name in updated:
        print(f"  ok: {name}")
    print(f"Sem match na FIFA, preservados: {len(missing)}")
    for name in missing:
        print(f"  falta: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
