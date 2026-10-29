from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ..utils import write_json


DEFAULT_ENDPOINT_URL = "http://127.0.0.1:8333"
DEFAULT_BUCKET = "curso-bigdata"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_local_endpoint(endpoint_url: str) -> None:
    parsed = urlparse(endpoint_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOCAL_HOSTS:
        raise SystemExit(
            f"Endpoint recusado: {endpoint_url}. Este script só permite SeaweedFS local."
        )


def create_s3_client(endpoint_url: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "admin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "bigdata-secret"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def backup_and_clear_bucket(client, bucket: str, backup_dir: Path) -> dict[str, int]:
    client.head_bucket(Bucket=bucket)
    paginator = client.get_paginator("list_objects_v2")
    objects = [item for page in paginator.paginate(Bucket=bucket) for item in page.get("Contents", [])]
    if not objects:
        return {"objects_backed_up": 0, "objects_deleted": 0, "bytes_backed_up": 0}

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_root = backup_dir.resolve()
    bytes_backed_up = 0
    manifest = []

    for item in objects:
        key = item["Key"]
        relative_path = PurePosixPath(key)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise SystemExit(f"Chave S3 insegura; limpeza cancelada: {key}")
        destination = (backup_root / Path(*relative_path.parts)).resolve()
        if backup_root not in destination.parents:
            raise SystemExit(f"Chave S3 fora do backup; limpeza cancelada: {key}")

        size = int(item["Size"])
        if key.endswith("/") and size == 0:
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(bucket, key, str(destination))
            bytes_backed_up += size
        manifest.append({"key": key, "size": size, "etag": item.get("ETag")})

    write_json(backup_dir / "seaweed_manifest.json", manifest)
    deleted = 0
    for offset in range(0, len(objects), 1_000):
        batch = objects[offset : offset + 1_000]
        response = client.delete_objects(
            Bucket=bucket,
            Delete={"Objects": [{"Key": item["Key"]} for item in batch], "Quiet": True},
        )
        errors = response.get("Errors", [])
        if errors:
            raise RuntimeError(f"Falha removendo objetos S3; backup mantido: {errors[:3]}")
        deleted += len(batch)

    return {
        "objects_backed_up": len(objects),
        "objects_deleted": deleted,
        "bytes_backed_up": bytes_backed_up,
    }


def clear_bucket_without_backup(client, bucket: str) -> dict[str, int]:
    client.head_bucket(Bucket=bucket)
    paginator = client.get_paginator("list_objects_v2")
    objects = [item for page in paginator.paginate(Bucket=bucket) for item in page.get("Contents", [])]
    deleted = 0
    bytes_deleted = 0
    for offset in range(0, len(objects), 1_000):
        batch = objects[offset : offset + 1_000]
        response = client.delete_objects(
            Bucket=bucket,
            Delete={"Objects": [{"Key": item["Key"]} for item in batch], "Quiet": True},
        )
        errors = response.get("Errors", [])
        if errors:
            raise RuntimeError(f"Falha removendo objetos do bucket: {errors[:3]}")
        deleted += len(batch)
        bytes_deleted += sum(int(item["Size"]) for item in batch)
    return {"objects_deleted": deleted, "bytes_deleted": bytes_deleted}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reinicia o lake local; o backup é opcional e SeaweedFS só é limpo quando solicitado."
    )
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--clear-seaweedfs", action="store_true")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Apaga o lake sem backup; combinado com --clear-seaweedfs também esvazia o bucket sem backup.",
    )
    parser.add_argument(
        "--endpoint-url",
        default=os.getenv("S3_ENDPOINT_URL", DEFAULT_ENDPOINT_URL),
    )
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET", DEFAULT_BUCKET))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = None
    if args.no_backup:
        confirmation = (
            f"APAGAR TUDO {args.bucket}"
            if args.clear_seaweedfs
            else "APAGAR LAKE LOCAL"
        )
        entered = input(
            f"Este reset NÃO cria backup. data/source será preservada. "
            f"Digite '{confirmation}' para continuar: "
        )
        if entered != confirmation:
            raise SystemExit("Confirmação não corresponde; nada foi alterado.")

    if args.clear_seaweedfs:
        validate_local_endpoint(args.endpoint_url)
        if not args.no_backup:
            confirmation = input(
                f"Isto fará backup e removerá os objetos do bucket local '{args.bucket}'. "
                f"Digite {args.bucket} para continuar: "
            )
            if confirmation != args.bucket:
                raise SystemExit("Confirmação não corresponde; nenhuma limpeza foi executada.")
        client = create_s3_client(args.endpoint_url)

    data_dir = args.data
    lake_dir = data_dir / "lake"
    backup_root = None
    if not args.no_backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = data_dir / f"lake_reset_backup_{timestamp}"
        if backup_root.exists():
            raise SystemExit(f"Backup já existe; nada foi alterado: {backup_root}")
        backup_root.mkdir(parents=True, exist_ok=False)

    seaweed_result = None
    if client is not None:
        try:
            if args.no_backup:
                seaweed_result = clear_bucket_without_backup(client, args.bucket)
            else:
                seaweed_result = backup_and_clear_bucket(
                    client,
                    args.bucket,
                    backup_root / "seaweed_bucket",
                )
        except (BotoCoreError, ClientError, RuntimeError) as exc:
            raise SystemExit(
                f"Falha limpando SeaweedFS; lake local não foi movido. "
                f"Backup: {backup_root or 'não criado'}. Detalhe: {exc}"
            ) from exc

    local_backup = None
    if lake_dir.exists():
        if args.no_backup:
            if lake_dir.is_symlink():
                raise SystemExit(f"O caminho do lake é symlink; reset cancelado: {lake_dir}")
            shutil.rmtree(lake_dir)
        else:
            local_backup = backup_root / "local_lake"
            shutil.move(str(lake_dir), str(local_backup))

    (lake_dir / "landing").mkdir(parents=True, exist_ok=True)
    (lake_dir / "control").mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "local_lake": "reset",
                "local_backup": str(local_backup) if local_backup else None,
                "seaweedfs": seaweed_result or "não alterado",
                "backup_root": str(backup_root) if backup_root else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
