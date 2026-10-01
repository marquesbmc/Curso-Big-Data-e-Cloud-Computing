from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query


SOURCE_DIR = Path(os.getenv("BIGDATA_SOURCE_DIR", "data/source"))
DATA_FILE = SOURCE_DIR / "api" / "shipments.jsonl"
app = FastAPI(
    title="API externa simulada",
    description="Fonte paginada de entregas para o laboratório de Big Data.",
    version="1.0.0",
)


def iter_shipments():
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Dados não encontrados. Peça ao instrutor para preparar a base de demonstração.",
        )
    with DATA_FILE.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "data_file_exists": DATA_FILE.exists()}


@app.get("/shipments")
def shipments(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1_000),
    since: datetime | None = None,
    after_sequence: int = Query(0, ge=0),
) -> dict:
    start = (page - 1) * limit
    selected = []
    eligible_index = 0
    has_more = False

    for shipment in iter_shipments():
        source_sequence = int(
            shipment.get("source_sequence")
            or shipment["shipment_id"].rsplit("-", 1)[-1]
        )
        if source_sequence <= after_sequence:
            continue
        if since is not None:
            created_at = datetime.fromisoformat(shipment["created_at"])
            comparison_since = since
            if comparison_since.tzinfo is None and created_at.tzinfo is not None:
                comparison_since = comparison_since.replace(tzinfo=created_at.tzinfo)
            if created_at <= comparison_since:
                continue
        if eligible_index < start:
            eligible_index += 1
            continue
        if len(selected) < limit:
            selected.append(shipment)
            eligible_index += 1
            continue
        has_more = True
        break

    return {
        "page": page,
        "limit": limit,
        "count": len(selected),
        "has_more": has_more,
        "after_sequence": after_sequence,
        "items": selected,
    }


@app.get("/shipments/{shipment_id}")
def shipment_by_id(shipment_id: str) -> dict:
    for shipment in iter_shipments():
        if shipment["shipment_id"] == shipment_id:
            return shipment
    raise HTTPException(status_code=404, detail="Entrega não encontrada")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bigdata_pipeline.api.app:app", host="127.0.0.1", port=8001, reload=False)
