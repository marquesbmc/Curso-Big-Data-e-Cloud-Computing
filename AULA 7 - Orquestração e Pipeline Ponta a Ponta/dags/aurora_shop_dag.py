"""
DAG do Apache Airflow para a plataforma de dados da Aurora Shop.

Este arquivo responde a três perguntas, nesta ordem:

    1. ONDE estão os sistemas?   Connections cadastradas no Airflow
                                 (Admin → Connections), lidas pelo id.
    2. O QUE executar?           Sensores, tarefas Python e comandos Bash.
    3. EM QUE ORDEM?             As setas >> no final do arquivo.

Nenhuma senha ou endereço de servidor está escrito aqui. O DAG só conhece os
nomes das conexões:

    seaweedfs            Data Lake (S3)        usada por S3Hook e pelas tarefas que enviam ao bucket
    api_transportadora   API de entregas       usada por HttpSensor e pelo EL da API

Se o servidor mudar de endereço, ou a senha for trocada, muda-se a Connection.
O código continua o mesmo.

Antes da primeira execução, crie o pool usado pelos ELs:

    airflow pools set capture_state 1 "ELs compartilham capture_state.json"
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pendulum
from airflow.exceptions import AirflowFailException
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, Param, TaskGroup, task
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, PartialCredentialsError

PROJECT_DIR = Path(os.getenv("AURORA_PROJECT_DIR", Path(__file__).resolve().parents[1]))
PYTHON = shlex.quote(sys.executable)   # o Python do Airflow, com as bibliotecas do pipeline
BUCKET = "curso-bigdata"


# ═════════════════════════════════════════════════════════════════════════
# 1. ONDE: as conexões
# ═════════════════════════════════════════════════════════════════════════
# {{ conn.<id>.<campo> }} é preenchido pelo Airflow na hora de executar a
# tarefa, com o que está cadastrado em Admin → Connections.

# Data Lake: tipo "Amazon Web Services". Login e senha são as chaves S3;
# o endereço do SeaweedFS fica no campo Extra: {"endpoint_url": "..."}.
SEAWEEDFS_ENV = {
    "AWS_ACCESS_KEY_ID": "{{ conn.seaweedfs.login }}",
    "AWS_SECRET_ACCESS_KEY": "{{ conn.seaweedfs.password }}",
    "S3_ENDPOINT_URL": "{{ conn.seaweedfs.extra_dejson.endpoint_url }}",
    "S3_BUCKET": BUCKET,
}

# Códigos que o S3 devolve quando login ou senha estão errados.
CREDENCIAL_RECUSADA = {"403", "AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"}

# API da transportadora: tipo "HTTP", com Schema, Host e Port.
# Schema vazio vale "http", como no HttpSensor.
API_URL = (
    "{{ conn.api_transportadora.schema or 'http' }}://"
    "{{ conn.api_transportadora.host }}:{{ conn.api_transportadora.port }}"
)

# Variáveis que toda tarefa Bash recebe.
BASE_ENV = {
    "PYTHONUTF8": "1",
    "AURORA_DAG_ID": "{{ dag.dag_id }}",
    "AURORA_RUN_ID": "{{ run_id }}",
}


def register_failure(context: dict) -> None:
    """Callback de falha: grava um alerta em data/orchestration/alerts.jsonl."""

    ti = context["task_instance"]
    alert = {
        "dag_id": ti.dag_id,
        "run_id": context["run_id"],
        "momento": datetime.now(timezone.utc).isoformat(),
        "tarefas_com_falha": [ti.task_id],
        "origem": "airflow",
    }
    path = PROJECT_DIR / "data" / "orchestration" / "alerts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(alert, ensure_ascii=False) + "\n")


with DAG(
    dag_id="aurora_shop_pipeline",
    description="Fontes → Landing → SeaweedFS → Bronze → Silver → Gate → Gold → Publicação → Modelo",
    schedule="0 6 * * *",          # cron: todo dia às 06:00
    start_date=pendulum.datetime(2026, 10, 1, tz="America/Sao_Paulo"),
    catchup=False,                 # não reprocessa os dias anteriores ao ligar o DAG
    max_active_runs=1,             # o aurora.duckdb aceita um único escritor
    params={                       # campos do formulário "Trigger"
        "max_quarantine_pct": Param(10, type="number", minimum=0, maximum=100,
                                    description="Percentual máximo de quarentena aceito pelo gate."),
        "min_auc": Param(0.60, type="number", minimum=0, maximum=1,
                         description="AUC mínima para promover o modelo de risco de atraso."),
    },
    default_args={
        "owner": "equipe-dados",
        "on_failure_callback": register_failure,
        "cwd": str(PROJECT_DIR),   # as tarefas Bash rodam na pasta do projeto
        "env": BASE_ENV,
        "append_env": True,
    },
    tags=["aurora-shop", "aula-7"],
    doc_md=__doc__,
) as dag:

    # ═════════════════════════════════════════════════════════════════════
    # 2. O QUE: as tarefas
    # ═════════════════════════════════════════════════════════════════════

    # ── Sensores: esperam a infraestrutura ficar disponível ──────────────
    with TaskGroup("sensores"):

        # Sensor pronto do Airflow: faz GET em /health usando a Connection.
        # Se a API responde com erro, ele pergunta de novo a cada poke_interval.
        # Se a API nem atende (fora do ar), a tentativa falha: por isso as retries,
        # que fazem o sensor insistir por cerca de 1 minuto antes de desistir.
        aguardar_api = HttpSensor(
            task_id="aguardar_api_entregas",
            http_conn_id="api_transportadora",
            endpoint="health",
            poke_interval=5,       # pergunta a cada 5 segundos
            timeout=60,            # desiste depois de 60 segundos numa mesma tentativa
            mode="poke",
            retries=10,
            retry_delay=timedelta(seconds=5),
            doc_md="GET /health na API da transportadora (Connection `api_transportadora`).",
        )

        # Sensor escrito em Python: o S3Hook monta o cliente S3 a partir da Connection.
        #   SeaweedFS fora do ar  → devolve False: tenta de novo no próximo poke.
        #   credencial recusada   → falha na hora: esperar não corrige uma senha errada.
        #   credencial ausente    → falha na hora, pelo mesmo motivo.
        @task.sensor(task_id="aguardar_seaweedfs", poke_interval=5, timeout=60, mode="poke")
        def aguardar_seaweedfs() -> bool:
            """Espera o bucket do SeaweedFS responder (Connection `seaweedfs`)."""

            s3 = S3Hook(aws_conn_id="seaweedfs").get_conn()   # cliente boto3 já configurado
            try:
                s3.head_bucket(Bucket=BUCKET)
                print(f"bucket {BUCKET} acessível")
                return True
            except ClientError as error:
                code = error.response.get("Error", {}).get("Code", "")
                if code in CREDENCIAL_RECUSADA:
                    raise AirflowFailException(
                        f"O SeaweedFS recusou as credenciais (HTTP {code}). "
                        "Confira login e senha em Admin → Connections → seaweedfs."
                    )
                print(f"S3 respondeu {code}: tentando de novo")
                return False
            except (NoCredentialsError, PartialCredentialsError):
                raise AirflowFailException(
                    "A Connection seaweedfs está sem login ou sem senha. "
                    "Preencha AWS Access Key ID e AWS Secret Access Key em Admin → Connections → seaweedfs."
                )
            except BotoCoreError as error:
                print(f"SeaweedFS indisponível ({type(error).__name__}): tentando de novo")
                return False

        aguardar_lake = aguardar_seaweedfs()

    # ── Ingestão: das fontes para a Landing ──────────────────────────────
    # Os cinco ELs leem e regravam data/lake/control/capture_state.json.
    # O pool capture_state tem 1 vaga: só um EL roda por vez.
    with TaskGroup("ingestao", default_args={"pool": "capture_state", "retries": 1,
                                             "retry_delay": timedelta(seconds=5)}):
        el_sqlite = BashOperator(
            task_id="el_sqlite",
            bash_command=f"{PYTHON} -m bigdata_pipeline.el.sqlite --source data/source --lake data/lake",
            doc_md="Novos registros do sistema de vendas (watermark por ID).",
        )
        el_csv = BashOperator(
            task_id="el_csv",
            bash_command=f"{PYTHON} -m bigdata_pipeline.el.csv --source data/source --lake data/lake",
            doc_md="Arquivos CSV novos ou alterados (manifest SHA-256).",
        )
        el_json = BashOperator(
            task_id="el_json",
            bash_command=f"{PYTHON} -m bigdata_pipeline.el.json --source data/source --lake data/lake",
            doc_md="Campanhas de marketing em JSON.",
        )
        el_eventos = BashOperator(
            task_id="el_eventos",
            bash_command=f"{PYTHON} -m bigdata_pipeline.el.events --source data/source --lake data/lake",
            doc_md="Eventos de navegação em JSON Lines.",
        )
        el_api = BashOperator(
            task_id="el_api_entregas",
            bash_command=(f"{PYTHON} -m bigdata_pipeline.el.api --source data/source --lake data/lake"
                          f" --api-url {API_URL}"),
            retries=2,
            retry_delay=timedelta(seconds=10),
            doc_md="Entregas paginadas da API. Rede falha: por isso 2 novas tentativas.",
        )

    # ── Data Lake: Landing para o SeaweedFS ──────────────────────────────
    with TaskGroup("lake"):
        sincronizar = BashOperator(
            task_id="sincronizar_landing",
            bash_command=f"{PYTHON} -m bigdata_pipeline.lake.sync --source data/lake/landing",
            env={**BASE_ENV, **SEAWEEDFS_ENV},
            retries=2,
            retry_delay=timedelta(seconds=10),
            doc_md="Envia ao SeaweedFS somente objetos novos ou alterados (SHA-256).",
        )

    # ── Transformação: Bronze, Silver e gate ─────────────────────────────
    with TaskGroup("transformacao"):
        bronze = BashOperator(
            task_id="construir_bronze",
            bash_command=f"{PYTHON} -m bigdata_pipeline.transform.pipeline --stage bronze",
            doc_md="Landing → Parquet com linhagem.",
        )
        silver = BashOperator(
            task_id="construir_silver",
            bash_command=f"{PYTHON} -m bigdata_pipeline.transform.pipeline --stage silver",
            doc_md="Regras de qualidade: Silver + Quarentena + relatório.",
        )
        gate = BashOperator(
            task_id="gate_qualidade",
            bash_command=(f"{PYTHON} -m bigdata_pipeline.transform.quality_gate"
                          " --max-quarantine-pct {{ params.max_quarantine_pct }}"),
            retries=0,
            doc_md="Regras bloqueantes e alertas. Sem novas tentativas: repetir não corrige dado ruim.",
        )

    # ── Warehouse: Gold e validações ─────────────────────────────────────
    with TaskGroup("warehouse"):
        gold = BashOperator(
            task_id="construir_gold",
            bash_command=f"{PYTHON} -m bigdata_pipeline.transform.pipeline --stage gold",
            doc_md="Dimensões, fatos e marts no aurora.duckdb.",
        )
        validar = BashOperator(
            task_id="validar_warehouse",
            bash_command=f"{PYTHON} -m bigdata_pipeline.transform.validate --all",
            retries=0,
            doc_md="Reconciliação, grão, chaves duplicadas e chaves órfãs.",
        )

    # ── Publicação no SeaweedFS ──────────────────────────────────────────
    with TaskGroup("publicacao", default_args={"retries": 2, "retry_delay": timedelta(seconds=10)}):
        publicar_camadas = BashOperator(
            task_id="publicar_camadas",
            bash_command=(f"{PYTHON} -m bigdata_pipeline.transform.publish"
                          " --lake data/lake --layers bronze silver quarantine"
                          ' --endpoint-url "$S3_ENDPOINT_URL" --bucket "$S3_BUCKET"'),
            env={**BASE_ENV, **SEAWEEDFS_ENV},
            doc_md="Bronze, Silver e Quarentena no SeaweedFS.",
        )
        publicar_warehouse = BashOperator(
            task_id="publicar_warehouse",
            bash_command=(f"{PYTHON} -m bigdata_pipeline.transform.publish"
                          " --lake data --layers warehouse quality"
                          ' --endpoint-url "$S3_ENDPOINT_URL" --bucket "$S3_BUCKET"'),
            env={**BASE_ENV, **SEAWEEDFS_ENV},
            doc_md="aurora.duckdb, relatório, gate e alertas no SeaweedFS.",
        )

        # Tarefa Python que conversa com o S3 pelo Hook, sem boto3 nem senha no código.
        # O valor retornado aparece na aba XCom da tarefa.
        @task(task_id="conferir_bucket")
        def conferir_bucket() -> dict[str, int]:
            """Conta os objetos do bucket por prefixo (Connection `seaweedfs`)."""

            keys = S3Hook(aws_conn_id="seaweedfs").list_keys(bucket_name=BUCKET) or []
            resumo: dict[str, int] = {}
            for key in keys:
                prefixo = key.split("/", 1)[0]
                resumo[prefixo] = resumo.get(prefixo, 0) + 1
            for prefixo, total in sorted(resumo.items()):
                print(f"{prefixo:<12} {total:>5} objetos")
            return resumo

        conferir = conferir_bucket()

    # ── Produto de dados ─────────────────────────────────────────────────
    with TaskGroup("produtos"):
        modelo = BashOperator(
            task_id="treinar_modelo_atraso",
            bash_command=(f"{PYTHON} -m bigdata_pipeline.ml.risco_atraso"
                          " --min-auc {{ params.min_auc }}"),
            doc_md="Dataset versionado, treino temporal e gate do modelo.",
        )

    # ═════════════════════════════════════════════════════════════════════
    # 3. EM QUE ORDEM: as dependências
    # ═════════════════════════════════════════════════════════════════════
    # a >> b    "b só começa depois que a terminar com sucesso"
    # [a, b]    tarefas sem seta entre si podem rodar ao mesmo tempo

    aguardar_api >> el_api
    [el_sqlite, el_csv, el_json, el_eventos, el_api, aguardar_lake] >> sincronizar
    sincronizar >> bronze >> silver >> gate >> gold >> validar
    validar >> [publicar_camadas, publicar_warehouse]
    [publicar_camadas, publicar_warehouse] >> conferir
    [publicar_camadas, publicar_warehouse] >> modelo
