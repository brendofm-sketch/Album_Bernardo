#!/usr/bin/env python3
"""
Baixa fotos de elenco da FIFA para todas as selecoes do HTML.

Fluxo:
1. abre a pagina FIFA /teams/{slug}/squad;
2. le teamId/seasonId do JSON publico da pagina;
3. chama api/v3/teams/{teamId}/squad;
4. casa jogadores pelo nome do checklist;
5. salva referencias/COD_00.jpg e atualiza o CSV.
"""

from __future__ import annotations

import argparse
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
PAGE_BASE = "https://cxm-api.fifa.com/fifaplusweb/api/pages/pt/tournaments/mens/worldcup/canadamexicousa2026/teams"
SQUAD_BASE = "https://api.fifa.com/api/v3/teams"
FIFA_WEB_BASE = "https://www.fifa.com/pt/tournaments/mens/worldcup/canadamexicousa2026/teams"

TEAM_SLUGS = {
    "ALG": "algeria",
    "ARG": "argentina",
    "AUS": "australia",
    "AUT": "austria",
    "BEL": "belgium",
    "BIH": "bosnia-herzegovina",
    "BRA": "brazil",
    "CAN": "canada",
    "CIV": "cote-d-ivoire",
    "COD": "congo-dr",
    "COL": "colombia",
    "CPV": "cabo-verde",
    "CRO": "croatia",
    "CUW": "curacao",
    "CZE": "czechia",
    "ECU": "ecuador",
    "EGY": "egypt",
    "ENG": "england",
    "ESP": "spain",
    "FRA": "france",
    "GER": "germany",
    "GHA": "ghana",
    "HAI": "haiti",
    "IRN": "ir-iran",
    "IRQ": "iraq",
    "JOR": "jordan",
    "JPN": "japan",
    "KOR": "korea-republic",
    "KSA": "saudi-arabia",
    "MAR": "morocco",
    "MEX": "mexico",
    "NED": "netherlands",
    "NOR": "norway",
    "NZL": "new-zealand",
    "PAN": "panama",
    "PAR": "paraguay",
    "POR": "portugal",
    "QAT": "qatar",
    "RSA": "south-africa",
    "SCO": "scotland",
    "SEN": "senegal",
    "SUI": "switzerland",
    "SWE": "sweden",
    "TUN": "tunisia",
    "TUR": "turkiye",
    "URU": "uruguay",
    "USA": "usa",
    "UZB": "uzbekistan",
}

NAME_ALIASES = {
    ("BRA", "vinicius junior"): ["vinicius junior", "vini junior", "vini jr"],
    ("BRA", "eder militao"): ["eder militao"],
    ("BRA", "estevao"): ["estevao", "estevao willian"],
    ("BRA", "wesley"): ["wesley", "wesley franca"],
    ("USA", "weston mckenny"): ["weston mckennie"],
}


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


def read_csv() -> tuple[list[str], dict[str, dict]]:
    fields = ["code", "number", "file", "team", "name", "type", "role", "reference_path", "reference_url", "page_url", "license", "artist", "credit", "status"]
    if not CSV_FILE.exists():
        return fields, {}
    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or fields), {f"{row['code']}{int(row['number']):02d}": row for row in reader}


def role_for(slot: dict) -> str:
    if slot["type"] == "badge":
        return "ESCUDO"
    if slot["type"] == "squad":
        return "ELENCO"
    if slot["n"] <= 3:
        return "GOLEIRO"
    if slot["n"] <= 8:
        return "DEFENSOR"
    if slot["n"] <= 12:
        return "MEIO-CAMPISTA"
    return "ATACANTE"


def base_row(team: dict, slot: dict) -> dict:
    return {
        "code": team["code"],
        "number": str(slot["n"]),
        "file": f"figurinhas/{team['code']}_{slot['n']:02d}.webp",
        "team": team["name"],
        "name": slot["name"],
        "type": slot["type"],
        "role": role_for(slot),
        "reference_path": "",
        "reference_url": "",
        "page_url": "",
        "license": "",
        "artist": "",
        "credit": "",
        "status": "skip_non_player" if slot["type"] != "player" else "not_found",
    }


def get_json(url: str) -> dict | None:
    try:
        response = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None


def page_data(slug: str) -> dict | None:
    return get_json(f"{PAGE_BASE}/{slug}/squad")


def fifa_players(team_id: str, season_id: str) -> dict[str, dict]:
    data = get_json(f"{SQUAD_BASE}/{team_id}/squad?idCompetition=17&idSeason={season_id}&language=pt") or {}
    players = {}
    for player in data.get("Players", []):
        picture = (player.get("PlayerPicture") or {}).get("PictureUrl")
        position = description(player.get("PositionLocalized")) or description(player.get("RealPositionLocalized"))
        if not picture:
            continue
        names = {description(player.get("PlayerName")), description(player.get("ShortName"))}
        for name in names:
            key = normalize(name)
            if key:
                players[key] = {"name": name, "url": picture, "id": player.get("IdPlayer", ""), "jersey": player.get("JerseyNum", ""), "position": position}
    return players


def candidate_keys(team_code: str, name: str) -> list[str]:
    key = normalize(name)
    aliases = NAME_ALIASES.get((team_code, key), [])
    return [key] + [normalize(alias) for alias in aliases]


def image_url(base_url: str) -> str:
    return f"{base_url}?&io=transform:fill,aspectratio:1x1,width:900,gravity:top&quality=90"


def download_as_jpg(url: str, out: Path) -> None:
    response = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*"})
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    image.save(out, "JPEG", quality=94, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Baixa fotos FIFA por selecao.")
    parser.add_argument("--team", help="Codigo da selecao, ex: CAN.")
    parser.add_argument("--force", action="store_true", help="Sobrescreve referencias existentes.")
    args = parser.parse_args()

    REF_DIR.mkdir(exist_ok=True)
    fields, previous = read_csv()
    rows = []
    total_updated = total_missing = total_no_page = 0

    for team in read_teams():
        selected = not args.team or team["code"] == args.team.upper()
        slug = TEAM_SLUGS.get(team["code"])
        pdata = page_data(slug) if selected and slug else None
        players = {}
        web_page = f"{FIFA_WEB_BASE}/{slug}/squad" if slug else ""
        if selected and pdata:
            players = fifa_players(str(pdata.get("teamId")), str(pdata.get("seasonId", "285023")))
        elif selected:
            total_no_page += 1
            print(f"Sem pagina FIFA: {team['code']} {team['name']} slug={slug}")

        updated = missing = 0
        for slot in team["slots"]:
            key = f"{team['code']}{slot['n']:02d}"
            row = {**base_row(team, slot), **previous.get(key, {})}
            if not selected or slot["type"] != "player":
                rows.append(row)
                continue
            if row.get("reference_path") and (ROOT / row["reference_path"]).exists() and not args.force and row.get("status", "").startswith("corrected"):
                rows.append(row)
                continue
            match = None
            for candidate in candidate_keys(team["code"], slot["name"]):
                match = players.get(candidate)
                if match:
                    break
            if not match:
                missing += 1
                rows.append(row)
                continue
            direct_url = image_url(match["url"])
            out = REF_DIR / f"{team['code']}_{slot['n']:02d}.jpg"
            try:
                download_as_jpg(direct_url, out)
            except Exception as exc:
                row["status"] = f"fifa_download_error:{type(exc).__name__}"
                rows.append(row)
                continue
            row.update({
                "reference_path": str(out.relative_to(ROOT)),
                "reference_url": direct_url,
                "page_url": web_page,
                "license": "FIFA source image / review usage rights",
                "artist": "",
                "credit": "FIFA Digital Hub",
                "status": "downloaded_fifa_squad",
            })
            if match.get("position"):
                row["role"] = match["position"].upper()
            rows.append(row)
            updated += 1

        if selected:
            total_updated += updated
            total_missing += missing
            print(f"{team['code']} {team['name']}: FIFA atualizadas={updated}, sem match={missing}")

    with CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total FIFA atualizadas: {total_updated}")
    print(f"Total sem match: {total_missing}")
    print(f"Paginas FIFA nao encontradas: {total_no_page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
