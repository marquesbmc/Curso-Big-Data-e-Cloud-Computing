from __future__ import annotations

import argparse
import json
from pathlib import Path

from bigdata_pipeline.lake.sync import (
    DEFAULT_BUCKET,
    DEFAULT_ENDPOINT_URL,
    create_s3_client,
    object_has_hash,
)
from bigdata_pipeline.utils import file_sha256


def publish(root: Path, layers: list[str], bucket: str, endpoint_url: str) -> dict[str, int]:
    client = create_s3_client(endpoint_url)
    client.head_bucket(Bucket=bucket)
    uploaded = skipped = uploaded_bytes = 0
    for layer in layers:
        layer_root = root / layer
        if not layer_root.is_dir():
            raise SystemExit(f"Camada não encontrada: {layer_root}")
        for path in sorted(item for item in layer_root.rglob("*") if item.is_file()):
            key = f"{layer}/{path.relative_to(layer_root).as_posix()}"
            checksum = file_sha256(path)
            if object_has_hash(client, bucket, key, checksum):
                skipped += 1
                continue
            client.upload_file(
                str(path), bucket, key, ExtraArgs={"Metadata": {"sha256": checksum}}
            )
            uploaded += 1
            uploaded_bytes += path.stat().st_size
    return {"uploaded_objects": uploaded, "skipped_objects": skipped, "uploaded_bytes": uploaded_bytes}


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica as camadas analíticas no SeaweedFS.")
    parser.add_argument("--lake", type=Path, default=Path("data/lake"))
    parser.add_argument("--layers", nargs="+", default=["bronze", "silver", "quarantine"])
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--endpoint-url", default=DEFAULT_ENDPOINT_URL)
    args = parser.parse_args()
    result = publish(args.lake, args.layers, args.bucket, args.endpoint_url)
    print(json.dumps({"bucket": args.bucket, "layers": args.layers, **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
