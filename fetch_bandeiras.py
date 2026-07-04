#!/usr/bin/env python3
"""Baixa bandeiras locais usadas pelo HTML."""

from __future__ import annotations

from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "bandeiras"

FLAG_ISO = {
    "ALG": "dz", "ARG": "ar", "AUS": "au", "AUT": "at", "BEL": "be",
    "BIH": "ba", "BRA": "br", "CAN": "ca", "CIV": "ci", "COD": "cd",
    "COL": "co", "CPV": "cv", "CRO": "hr", "CUW": "cw", "CZE": "cz",
    "ECU": "ec", "EGY": "eg", "ENG": "gb-eng", "ESP": "es", "FRA": "fr",
    "GER": "de", "GHA": "gh", "HAI": "ht", "IRN": "ir", "IRQ": "iq",
    "JOR": "jo", "JPN": "jp", "KOR": "kr", "KSA": "sa", "MAR": "ma",
    "MEX": "mx", "NED": "nl", "NOR": "no", "NZL": "nz", "PAN": "pa",
    "PAR": "py", "POR": "pt", "QAT": "qa", "RSA": "za", "SCO": "gb-sct",
    "SEN": "sn", "SUI": "ch", "SWE": "se", "TUN": "tn", "TUR": "tr",
    "URU": "uy", "USA": "us", "UZB": "uz",
}


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    created = skipped = 0
    for code, iso in sorted(FLAG_ISO.items()):
        out = OUT_DIR / f"{code}.svg"
        if out.exists():
            skipped += 1
            continue
        url = f"https://flagcdn.com/{iso}.svg"
        response = requests.get(url, timeout=30, headers={"User-Agent": "NovoMundoAlbum/1.0"})
        response.raise_for_status()
        out.write_bytes(response.content)
        created += 1
    print(f"Bandeiras baixadas: {created}")
    print(f"Bandeiras existentes: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
