#!/usr/bin/env bash
# Cria (ou recria) as duas Connections usadas pelo DAG aurora_shop_pipeline.
#
# O roteiro cadastra as conexões pela interface (Admin → Connections).
# Este script faz o mesmo, para quem preferir ou precisar recuperar o ambiente.
#
# Uso, no terminal do VS Code (PowerShell), dentro da pasta da aula:
#
#     wsl -d Ubuntu-24.04 -- bash tools/airflow/criar_conexoes.sh
set -euo pipefail

source "$HOME/airflow-aula7.sh"

airflow connections delete seaweedfs >/dev/null 2>&1 || true
airflow connections add seaweedfs --conn-json '{
    "conn_type": "aws",
    "description": "Data Lake local (SeaweedFS, API compatível com S3)",
    "login": "admin",
    "password": "bigdata-secret",
    "extra": {"endpoint_url": "http://127.0.0.1:8333", "region_name": "us-east-1"}
}'

airflow connections delete api_transportadora >/dev/null 2>&1 || true
airflow connections add api_transportadora --conn-json '{
    "conn_type": "http",
    "description": "API de entregas da transportadora",
    "schema": "http",
    "host": "127.0.0.1",
    "port": 8001
}'

echo
airflow connections list -o table 2>/dev/null | grep -E "conn_id|seaweedfs|api_transportadora" || true
