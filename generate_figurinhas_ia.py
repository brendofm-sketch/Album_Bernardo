#!/usr/bin/env python3
"""
Gera figurinhas com IA usando referencias locais.

Requer OPENAI_API_KEY no ambiente. O script le o CSV criado por
fetch_referencias_abertas.py e salva os arquivos finais em figurinhas/COD_00.webp.
Por padrao, pula arquivos existentes; use --force para substituir.
"""

from __future__ import annotations

import argparse
import base64
import csv
import io
import os
from pathlib import Path

from openai import OpenAI
from PIL import Image


ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "referencias" / "referencias_jogadores.csv"
OUT_DIR = ROOT / "figurinhas"


def prompt(row: dict) -> str:
    country = row["team"]
    name = row["name"]
    role = row["role"]
    typ = row["type"]
    if typ == "player":
        return (
            f"Crie uma ilustracao original em estilo figurinha esportiva digital premium para album infantil. "
            f"Use a foto de referencia apenas para representar de forma reconhecivel o jogador {name}, sem gerar copia fotografica. "
            f"Jogador de futebol de {country}, posicao {role}, busto frontal, expressao confiante, uniforme inspirado nas cores de {country} "
            "sem escudos oficiais, sem logotipos, sem marcas, sem patrocinadores. Card vertical com fundo esportivo abstrato, "
            "luz de estudio, acabamento cartoon 3D/editorial de alta qualidade. Nao copiar layout oficial da Panini, nao usar marcas d'agua, "
            "sem texto dentro da imagem."
        )
    if typ == "squad":
        return (
            f"Crie uma ilustracao original de elenco de futebol de {country}, grupo de jogadores ficticios em estilo cartoon 3D/editorial, "
            "uniformes inspirados nas cores do pais sem logotipos oficiais, fundo esportivo abstrato, card vertical, sem texto, sem marcas."
        )
    return (
        f"Crie um simbolo original para figurinha de {country}, com bola e formas inspiradas nas cores do pais, sem escudo oficial, "
        "sem logotipo, sem texto, card vertical premium."
    )


def image_file(path: Path) -> io.BufferedReader:
    return path.open("rb")


def save_response_image(b64_json: str, out: Path) -> None:
    raw = base64.b64decode(b64_json)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = img.resize((512, 704), Image.Resampling.LANCZOS)
    out.parent.mkdir(exist_ok=True)
    img.save(out, "WEBP", quality=94, method=6)


def generate_with_reference(client: OpenAI, row: dict, ref: Path, model: str, quality: str) -> str:
    with image_file(ref) as fh:
        result = client.images.edit(
            model=model,
            image=fh,
            prompt=prompt(row),
            size="1024x1536",
            quality=quality,
            output_format="webp",
            response_format="b64_json",
        )
    return result.data[0].b64_json


def generate_without_reference(client: OpenAI, row: dict, model: str, quality: str) -> str:
    result = client.images.generate(
        model=model,
        prompt=prompt(row),
        size="1024x1536",
        quality=quality,
        output_format="webp",
        response_format="b64_json",
    )
    return result.data[0].b64_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera figurinhas com IA e referencias.")
    parser.add_argument("--team", help="Gera apenas um codigo de selecao, ex: BRA.")
    parser.add_argument("--limit", type=int, default=0, help="Limita a quantidade gerada.")
    parser.add_argument("--force", action="store_true", help="Substitui imagens existentes.")
    parser.add_argument("--include-no-reference", action="store_true", help="Gera tambem quando nao houver foto de referencia.")
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--quality", default="medium", choices=["low", "medium", "high", "auto"])
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Defina OPENAI_API_KEY antes de rodar a geracao por IA.")
    if not CSV_FILE.exists():
        raise SystemExit("CSV de referencias nao encontrado. Rode: python fetch_referencias_abertas.py")

    client = OpenAI()
    created = skipped = missing_ref = 0

    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if args.team and row["code"] != args.team.upper():
                continue
            out = ROOT / row["file"]
            if out.exists() and not args.force:
                skipped += 1
                continue

            ref = ROOT / row["reference_path"] if row["reference_path"] else None
            if ref and ref.exists():
                b64 = generate_with_reference(client, row, ref, args.model, args.quality)
            elif args.include_no_reference:
                b64 = generate_without_reference(client, row, args.model, args.quality)
            else:
                missing_ref += 1
                continue

            save_response_image(b64, out)
            created += 1
            if args.limit and created >= args.limit:
                break

    print(f"Geradas: {created}")
    print(f"Puladas: {skipped}")
    print(f"Sem referencia: {missing_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
