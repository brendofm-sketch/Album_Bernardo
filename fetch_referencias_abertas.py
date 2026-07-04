#!/usr/bin/env python3
"""
Baixa fotos de referencia abertas para jogadores a partir de Wikimedia/Wikipedia.

Uso:
  python fetch_referencias_abertas.py --team BRA
  python fetch_referencias_abertas.py --limit 20

O script cria:
  referencias/referencias_jogadores.csv
  referencias/COD_00.jpg|png|webp

As fontes e licencas retornadas pela API ficam registradas no CSV. Revise antes de
usar em geracao de imagens, especialmente quando o uso sair do contexto familiar.
"""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "album_copa_2026_premium_imagens_externas.html"
REF_DIR = ROOT / "referencias"
CSV_FILE = REF_DIR / "referencias_jogadores.csv"
WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
EXACT_TITLE_ALIASES = {
    "bento": ["Bento (footballer)", "Bento Matheus Krepski"],
    "bruno guimaraes": ["Bruno Guimarães"],
    "lucas paqueta": ["Lucas Paquetá"],
    "vinicius junior": ["Vinícius Júnior"],
    "luiz henrique": ["Luiz Henrique (footballer, born 2001)"],
    "joao pedro": ["João Pedro (footballer, born 2001)"],
    "matheus cunha": ["Matheus Cunha"],
    "estevao": ["Estêvão Willian"],
    "wesley": ["Wesley Fran\u00e7a", "Wesley Vinicius Franca Lima"],
}


def get_json(url: str, **kwargs) -> dict:
    try:
        response = requests.get(url, timeout=25, headers={"User-Agent": "NovoMundoAlbum/1.0"}, **kwargs)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def read_teams() -> list[dict]:
    text = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"const\s+TEAMS\s*=\s*(\[.*?\]);\s*const\s+IMAGE_FOLDER", text, re.S)
    if not match:
        raise RuntimeError("Nao encontrei a constante TEAMS no HTML.")
    return json.loads(match.group(1))


def role_for(slot: dict) -> str:
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


def wiki_summary_image(name: str) -> dict | None:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(name)}"
    response = requests.get(url, timeout=25, headers={"User-Agent": "NovoMundoAlbum/1.0"})
    if response.status_code != 200:
        return None
    data = response.json()
    image = data.get("originalimage") or data.get("thumbnail")
    if not image or not image.get("source"):
        return None
    return {"page": data.get("content_urls", {}).get("desktop", {}).get("page", ""), "image_url": image["source"], "title": data.get("title", name)}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def wiki_search_image(name: str) -> dict | None:
    wanted = normalize(name)
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{name} footballer",
        "gsrlimit": 8,
        "prop": "pageimages|info",
        "piprop": "original|thumbnail",
        "pithumbsize": 1200,
        "inprop": "url",
    }
    data = get_json(WIKI_API, params=params)
    pages = list(data.get("query", {}).get("pages", {}).values())
    ranked = []
    for page in pages:
        title = page.get("title", "")
        norm_title = normalize(title)
        image = page.get("original") or page.get("thumbnail")
        if not image or not image.get("source"):
            continue
        score = 0
        if wanted and wanted in norm_title:
            score += 100
        for part in wanted.split():
            if part in norm_title:
                score += 10
        if "disambiguation" in norm_title:
            score -= 100
        ranked.append((score, page, image))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    score, page, image = ranked[0]
    if score < 10:
        return None
    return {"page": page.get("fullurl", ""), "image_url": image["source"], "title": page.get("title", name)}


def commons_search_image(name: str) -> dict | None:
    wanted = normalize(name)
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": 6,
        "gsrsearch": f"{name} footballer",
        "gsrlimit": 10,
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
    }
    data = get_json(COMMONS_API, params=params)
    ranked = []
    for page in data.get("query", {}).get("pages", {}).values():
        title = page.get("title", "")
        norm_title = normalize(title)
        info = page.get("imageinfo", [{}])[0]
        mime = info.get("mime", "")
        if not mime.startswith("image/") or not info.get("url"):
            continue
        score = 0
        if wanted and wanted in norm_title:
            score += 100
        for part in wanted.split():
            if part in norm_title:
                score += 10
        ranked.append((score, page, info))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    score, page, info = ranked[0]
    if score < 10:
        return None
    return {"page": info.get("descriptionurl", ""), "image_url": info["url"], "title": page.get("title", name)}


def commons_license(image_url: str) -> dict:
    file_name = image_url.rsplit("/", 1)[-1]
    params = {
        "action": "query",
        "format": "json",
        "titles": f"File:{file_name}",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime",
    }
    try:
        data = get_json(COMMONS_API, params=params)
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        info = page.get("imageinfo", [{}])[0]
        meta = info.get("extmetadata", {})
        return {
            "license": meta.get("LicenseShortName", {}).get("value", ""),
            "artist": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")),
            "credit": re.sub(r"<[^>]+>", "", meta.get("Credit", {}).get("value", "")),
            "source_url": info.get("descriptionurl", image_url),
            "mime": info.get("mime", ""),
        }
    except Exception:
        return {"license": "", "artist": "", "credit": "", "source_url": image_url, "mime": ""}


def download(url: str, out_base: Path) -> Path:
    response = None
    for attempt in range(4):
        response = requests.get(url, timeout=40, headers={"User-Agent": "NovoMundoAlbum/1.0"})
        if response.status_code != 429:
            break
        time.sleep(3 + attempt * 4)
    assert response is not None
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0]
    ext = mimetypes.guess_extension(content_type) or Path(url).suffix or ".jpg"
    if ext == ".jpe":
        ext = ".jpg"
    out = out_base.with_suffix(ext.lower())
    out.write_bytes(response.content)
    return out


def write_csv(rows: list[dict]) -> None:
    REF_DIR.mkdir(exist_ok=True)
    fields = ["code", "number", "file", "team", "name", "type", "role", "reference_path", "reference_url", "page_url", "license", "artist", "credit", "status"]
    with CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_existing_rows() -> dict[str, dict]:
    if not CSV_FILE.exists():
        return {}
    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        return {f"{row['code']}{int(row['number']):02d}": row for row in csv.DictReader(fh)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca fotos abertas para referencias de jogadores.")
    parser.add_argument("--team", help="Gera apenas um codigo de selecao, ex: BRA.")
    parser.add_argument("--limit", type=int, default=0, help="Limita a quantidade de downloads novos.")
    parser.add_argument("--force", action="store_true", help="Baixa novamente mesmo se ja existir referencia local.")
    parser.add_argument("--delay", type=float, default=0.2, help="Pausa entre consultas/downloads.")
    args = parser.parse_args()

    REF_DIR.mkdir(exist_ok=True)
    existing_rows = read_existing_rows()
    rows = []
    downloads = 0

    for team in read_teams():
        selected_team = not args.team or team["code"] == args.team.upper()
        for slot in team["slots"]:
            file_name = f"{team['code']}_{slot['n']:02d}.webp"
            row = {
                "code": team["code"],
                "number": slot["n"],
                "file": f"figurinhas/{file_name}",
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
                "status": "skip_non_player",
            }
            previous = existing_rows.get(f"{team['code']}{slot['n']:02d}")
            if not selected_team:
                rows.append(previous or row)
                continue
            if slot["type"] != "player":
                if previous and not args.force:
                    rows.append(previous)
                    continue
                rows.append(row)
                continue

            existing = list(REF_DIR.glob(f"{team['code']}_{slot['n']:02d}.*"))
            if previous and previous.get("reference_path") and (ROOT / previous["reference_path"]).exists() and not args.force:
                rows.append(previous)
                continue
            if existing and not args.force:
                row["reference_path"] = str(existing[0].relative_to(ROOT))
                row["status"] = "exists"
                rows.append(row)
                continue

            if args.limit and downloads >= args.limit:
                row["status"] = "not_fetched_limit"
                rows.append(row)
                continue

            plain_name = normalize(slot["name"])
            ascii_name = " ".join(part.capitalize() for part in plain_name.split())
            candidates = EXACT_TITLE_ALIASES.get(plain_name, []) + [
                f"{slot['name']} footballer",
                slot["name"],
                f"{ascii_name} footballer",
                ascii_name,
            ]
            found = None
            for query in candidates:
                found = wiki_summary_image(query)
                if found:
                    break
            if not found:
                found = wiki_search_image(slot["name"]) or commons_search_image(slot["name"])
            if not found:
                row["status"] = "not_found"
                rows.append(row)
                time.sleep(args.delay)
                continue

            license_data = commons_license(found["image_url"])
            try:
                out = download(found["image_url"], REF_DIR / f"{team['code']}_{slot['n']:02d}")
            except Exception as exc:
                row["reference_url"] = found["image_url"]
                row["page_url"] = found["page"]
                row["status"] = f"download_error:{type(exc).__name__}"
                rows.append(row)
                time.sleep(args.delay)
                continue
            row.update(
                {
                    "reference_path": str(out.relative_to(ROOT)),
                    "reference_url": found["image_url"],
                    "page_url": found["page"],
                    "license": license_data["license"],
                    "artist": license_data["artist"],
                    "credit": license_data["credit"],
                    "status": "downloaded",
                }
            )
            rows.append(row)
            downloads += 1
            time.sleep(args.delay)

    write_csv(rows)
    print(f"CSV: {CSV_FILE}")
    print(f"Downloads novos: {downloads}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
