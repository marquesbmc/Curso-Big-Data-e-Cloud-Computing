from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..utils import file_sha256, read_json, write_json


@dataclass
class CaptureRun:
    source: Path
    lake: Path
    api_url: str | None = None
    started_at: datetime | None = None
    run_id: str = ""
    landing: Path | None = None
    state: dict | None = None

    def __post_init__(self) -> None:
        self.started_at = datetime.now(timezone.utc)
        self.run_id = self.started_at.strftime("%Y%m%dT%H%M%SZ")
        self.landing = self.lake / "landing"
        control = self.lake / "control"
        control.mkdir(parents=True, exist_ok=True)
        self.landing.mkdir(parents=True, exist_ok=True)
        state_path = control / "capture_state.json"
        self.state = read_json(state_path, {})
        if not isinstance(self.state, dict):
            raise SystemExit(f"Estado inválido: {state_path}")

    def finish(self, summary: dict) -> None:
        finished_at = datetime.now(timezone.utc)
        summary["run_id"] = self.run_id
        summary["started_at"] = self.started_at.isoformat()
        summary["finished_at"] = finished_at.isoformat()
        self.state["last_run"] = summary["finished_at"]
        control = self.lake / "control"
        write_json(control / "capture_state.json", self.state)
        write_json(control / f"run_{self.run_id}.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))


def capture_directory(
    source_dir: Path,
    target_dir: Path,
    state: dict,
    state_key: str,
    extensions: set[str] | None = None,
) -> dict[str, int]:
    manifest = state.setdefault(state_key, {})
    copied = 0
    skipped = 0
    bytes_copied = 0
    if not source_dir.exists():
        return {"copied": 0, "skipped": 0, "bytes": 0}

    for source_path in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        if extensions is not None and source_path.suffix.lower() not in extensions:
            continue
        relative = source_path.relative_to(source_dir).as_posix()
        checksum = file_sha256(source_path)
        if manifest.get(relative) == checksum:
            skipped += 1
            continue
        destination = target_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        manifest[relative] = checksum
        copied += 1
        bytes_copied += source_path.stat().st_size
    return {"copied": copied, "skipped": skipped, "bytes": bytes_copied}


def run_single_capture(
    topic: str,
    handler,
    description: str,
    *,
    api_url_required: bool = False,
) -> None:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--source", type=Path, default=Path("data/source"))
    parser.add_argument("--lake", type=Path, default=Path("data/lake"))
    if api_url_required:
        parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    args = parser.parse_args()
    run = CaptureRun(args.source, args.lake, getattr(args, "api_url", None))
    run.finish({topic: handler(run)})