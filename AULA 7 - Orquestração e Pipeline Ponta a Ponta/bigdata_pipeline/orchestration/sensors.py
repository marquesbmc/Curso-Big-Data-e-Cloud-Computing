from __future__ import annotations

"""
Sensores: tarefas que esperam uma condição externa ficar verdadeira.

Um sensor "cutuca" (poke) o recurso em intervalos regulares. Se a condição
for satisfeita, termina com sucesso; se o tempo limite acabar, falha.

    python -m bigdata_pipeline.orchestration.sensors --s3
    python -m bigdata_pipeline.orchestration.sensors --http http://127.0.0.1:8001/health

O DAG do Airflow (dags/aurora_shop_dag.py) usa os sensores do próprio Airflow:
HttpSensor e um sensor com S3Hook, ambos lendo as Connections. Este comando é
usado só pelo runner local (plano B do professor), que não tem Connections.
"""

import argparse
import os
import sys
import time
import urllib.error
import urllib.request


def http_ready(url: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return 200 <= response.status < 300, f"HTTP {response.status}"
    except urllib.error.HTTPError as error:
        return False, f"HTTP {error.code}"
    except (urllib.error.URLError, OSError) as error:
        return False, f"sem resposta ({getattr(error, 'reason', error)})"


def s3_ready(endpoint_url: str, bucket: str) -> tuple[bool, str]:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import BotoCoreError, ClientError

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "admin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "bigdata-secret"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        # Uma tentativa curta por poke: quem repete é o próprio sensor.
        config=Config(connect_timeout=2, read_timeout=3, retries={"max_attempts": 1}),
    )
    try:
        client.head_bucket(Bucket=bucket)
        return True, f"bucket {bucket} acessível"
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "erro")
        return False, f"S3 respondeu {code}"
    except BotoCoreError as error:
        return False, type(error).__name__


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sensor de disponibilidade.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--http", metavar="URL", help="URL que deve responder 2xx.")
    target.add_argument("--s3", action="store_true", help="Endpoint S3 e bucket do SeaweedFS.")
    parser.add_argument("--endpoint-url", default=os.getenv("S3_ENDPOINT_URL", "http://127.0.0.1:8333"))
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET", "curso-bigdata"))
    parser.add_argument("--poke-interval", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()

    label = args.http or f"S3 {args.endpoint_url}/{args.bucket}"
    started = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        ok, detail = http_ready(args.http) if args.http else s3_ready(args.endpoint_url, args.bucket)
        elapsed = time.monotonic() - started
        print(f"poke {attempt}: {label} → {'disponível' if ok else 'indisponível'} ({detail})", flush=True)
        if ok:
            raise SystemExit(0)
        if elapsed >= args.timeout:
            print(f"Tempo limite de {args.timeout:.0f}s atingido. Verifique se o serviço foi iniciado.")
            raise SystemExit(1)
        time.sleep(min(args.poke_interval, args.timeout - elapsed))


if __name__ == "__main__":
    main()
