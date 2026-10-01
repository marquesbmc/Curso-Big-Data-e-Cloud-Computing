from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


def make_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    if not slug:
        raise SystemExit("Digite um nome com pelo menos uma letra ou número.")
    return slug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Registra um nome de exibição na Landing local da turma."
    )
    parser.add_argument("--name", required=True, help="Nome de exibição; primeiro nome ou apelido basta.")
    parser.add_argument("--data", type=Path, default=Path("data"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    display_name = args.name.strip()
    if not display_name:
        raise SystemExit("O nome não pode ficar vazio.")

    output_dir = args.data / "lake" / "landing" / "classroom" / "participants"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{make_slug(display_name)}.json"
    if output_path.exists():
        raise SystemExit(
            f"Já existe um registro para '{display_name}': {output_path}. "
            "Use outro nome de exibição para evitar sobrescrever o anterior."
        )

    record = {
        "display_name": display_name,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    print(
        json.dumps(
            {"registered": True, "file": str(output_path), **record},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
