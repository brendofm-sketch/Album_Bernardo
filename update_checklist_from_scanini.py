#!/usr/bin/env python3
"""
Atualiza nomes e ordem interna das figurinhas a partir do checklist publico do Scanini.

O script preserva a estrutura do HTML local e substitui os nomes genericos
("BRA 02", "FRA 10" etc.) pelos nomes publicados por time no checklist.
Ele nao baixa imagens oficiais, nao usa logos oficiais e nao altera o padrao
figurinhas/COD_00.webp.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "album_copa_2026_premium_imagens_externas.html"
OUT_JSON = ROOT / "checklist_scanini_2026.json"
HUB_URL = "https://scanini.app/albums/world-cup-2026"
BASE_URL = "https://scanini.app"


def fetch(url: str) -> str:
    response = requests.get(url, timeout=30, headers={"User-Agent": "NovoMundoAlbum/1.0"})
    response.raise_for_status()
    return response.text


def read_local_teams() -> list[dict]:
    text = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"const\s+TEAMS\s*=\s*(\[.*?\]);\s*const\s+IMAGE_FOLDER", text, re.S)
    if not match:
        raise RuntimeError("Nao encontrei a constante TEAMS no HTML.")
    return json.loads(match.group(1))


def team_links() -> dict[str, str]:
    text = fetch(HUB_URL)
    links: dict[str, str] = {}
    pattern = re.compile(r'<a[^>]+href="(/teams/[^"]+)"[^>]*>(.*?)</a>', re.S)
    for slug, body in pattern.findall(text):
        clean = html.unescape(re.sub(r"<[^>]+>", " ", body))
        clean = re.sub(r"\s+", " ", clean).strip()
        match = re.search(r"\b([A-Z]{3})\b\s+.+?\b20 stickers\b", clean)
        if match:
            links[match.group(1)] = BASE_URL + slug
    return links


def parse_team(url: str) -> list[dict]:
    text = fetch(url)
    items: list[dict] = []
    for block in re.findall(r'<a[^>]+href="/stickers/[^"]+"[^>]*>(.*?)</a>', text, re.S):
        spans = re.findall(r"<span[^>]*>(.*?)</span>", block, re.S)
        if len(spans) < 3:
            continue
        code_number = html.unescape(re.sub(r"<[^>]+>", " ", spans[0]))
        name = html.unescape(re.sub(r"<[^>]+>", " ", spans[1]))
        kind = html.unescape(re.sub(r"<[^>]+>", " ", spans[2]))
        code_number = re.sub(r"\s+", " ", code_number).strip()
        clean = re.sub(r"\s+", " ", name).strip()
        kind = re.sub(r"\s+", " ", kind).strip()
        match = re.match(r"([A-Z]{3})\s+(\d+)", code_number)
        if not match:
            continue
        code, number = match.groups()
        clean = html.unescape(re.sub(r"\s+", " ", name).strip())
        n = int(number)
        if kind.startswith("team logo"):
            typ = "badge"
            clean = "ESCUDO"
        elif kind.startswith("team photo"):
            typ = "squad"
            clean = "ELENCO"
        else:
            typ = "player"
        items.append({"code": code, "n": n, "name": clean, "type": typ})
    if len(items) != 20:
        raise RuntimeError(f"Checklist incompleto em {url}: {len(items)} itens")
    return sorted(items, key=lambda item: item["n"])


def replace_teams_in_html(teams: list[dict]) -> None:
    text = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    teams_json = json.dumps(teams, ensure_ascii=False)
    updated = re.sub(
        r"const\s+TEAMS\s*=\s*\[.*?\];\s*const\s+IMAGE_FOLDER",
        f"const TEAMS = {teams_json};\nconst IMAGE_FOLDER",
        text,
        count=1,
        flags=re.S,
    )
    if "const TEAMS =" not in updated:
        raise RuntimeError("Nao consegui substituir a constante TEAMS.")
    HTML_FILE.write_text(updated, encoding="utf-8")


def main() -> int:
    local_teams = read_local_teams()
    links = team_links()
    checklist = {}
    missing_codes = []

    for team in local_teams:
        code = team["code"]
        url = links.get(code)
        if not url:
            missing_codes.append(code)
            continue
        slots = parse_team(url)
        team["slots"] = [{"n": s["n"], "name": s["name"], "type": s["type"]} for s in slots]
        checklist[code] = {"source": url, "slots": slots}

    OUT_JSON.write_text(
        json.dumps({"source": HUB_URL, "teams": checklist, "missing_codes": missing_codes}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    replace_teams_in_html(local_teams)
    print(f"Times atualizados: {len(checklist)}")
    print(f"Codigos sem pagina no Scanini: {', '.join(missing_codes) if missing_codes else 'nenhum'}")
    print(f"Backup/checklist: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
