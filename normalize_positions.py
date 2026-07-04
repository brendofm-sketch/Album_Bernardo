#!/usr/bin/env python3
"""Normaliza posicoes dos jogadores no CSV de referencias.

Prioridade:
1. Posicao ja vinda da FIFA/correcao manual.
2. Inferencia pela ordem do album usando as posicoes confiaveis vizinhas.
3. Fallback conservador por blocos de numero.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "referencias" / "referencias_jogadores.csv"

ORDER = ["GOLEIRO", "DEFENSOR", "MEIO-CAMPISTA", "ATACANTE"]
TRUSTED_STATUS_PREFIXES = ("downloaded_fifa_squad", "corrected")


def fallback_role(number: int) -> str:
    if number <= 2:
        return "GOLEIRO"
    if number <= 8:
        return "DEFENSOR"
    if number <= 12:
        return "MEIO-CAMPISTA"
    return "ATACANTE"


def normalize_role(value: str) -> str:
    value = (value or "").upper().strip()
    aliases = {
        "GOALKEEPER": "GOLEIRO",
        "GOLEIRO": "GOLEIRO",
        "DEFENDER": "DEFENSOR",
        "DEFENSOR": "DEFENSOR",
        "MIDFIELDER": "MEIO-CAMPISTA",
        "MIDFIELD": "MEIO-CAMPISTA",
        "MEIO": "MEIO-CAMPISTA",
        "MEIO-CAMPISTA": "MEIO-CAMPISTA",
        "MEIO CAMPISTA": "MEIO-CAMPISTA",
        "FORWARD": "ATACANTE",
        "STRIKER": "ATACANTE",
        "ATACANTE": "ATACANTE",
    }
    return aliases.get(value, value if value in ORDER else "")


def infer_team(rows: list[dict]) -> None:
    players = [row for row in rows if row["type"] == "player"]
    trusted = {}
    for row in players:
        status = row.get("status", "")
        role = normalize_role(row.get("role", ""))
        if role in ORDER and status.startswith(TRUSTED_STATUS_PREFIXES):
            trusted[int(row["number"])] = role
            row["role"] = role

    # The Panini checklist is ordered by position groups. Fill gaps using the
    # nearest trusted group boundaries and never move backwards in the order.
    current_index = 0
    for row in players:
        n = int(row["number"])
        if n in trusted:
            current_index = max(current_index, ORDER.index(trusted[n]))
            row["role"] = ORDER[current_index]
            continue

        next_roles = [ORDER.index(role) for pos, role in sorted(trusted.items()) if pos > n]
        if next_roles:
            next_index = max(current_index, min(next_roles))
        else:
            next_index = len(ORDER) - 1
        fallback_index = ORDER.index(fallback_role(n))
        chosen = min(max(current_index, fallback_index), next_index)
        row["role"] = ORDER[chosen]


def main() -> int:
    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    by_team: dict[str, list[dict]] = {}
    for row in rows:
        by_team.setdefault(row["code"], []).append(row)
    for team_rows in by_team.values():
        infer_team(team_rows)

    with CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Selecoes normalizadas: {len(by_team)}")
    print(f"Jogadores normalizados: {sum(1 for row in rows if row['type'] == 'player')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
