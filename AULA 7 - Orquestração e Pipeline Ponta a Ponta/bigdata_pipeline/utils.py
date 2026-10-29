from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable


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
    shutil.move(str(path), str(backup))
    path.mkdir(parents=True, exist_ok=True)
    print(f"Backup criado em: {backup}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def batched(iterable: Iterable[tuple], size: int) -> Iterable[list[tuple]]:
    batch: list[tuple] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch

