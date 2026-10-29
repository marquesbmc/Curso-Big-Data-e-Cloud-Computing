from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


def ensure_empty_or_backup(path: Path, reset: bool) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return

    if not any(path.iterdir()):
        return

    if not reset:
        raise SystemExit(
            f"A pasta '{path}' já contém dados. Use --reset para criar um backup "
            "e gerar uma nova base."
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.parent / f"{path.name}_backup_{stamp}"
    if backup.exists():
        raise SystemExit(f"O backup '{backup}' já existe; nenhum arquivo foi movido.")
    shutil.move(str(path), str(backup))
    path.mkdir(parents=True, exist_ok=True)
    print(f"Backup criado em: {backup}")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
