"""
DAG do Apache Airflow para a plataforma de dados da Aurora Shop.

Este arquivo NÃO repete a lista de tarefas: ele lê a definição única em
bigdata_pipeline/orchestration/dag.py, a mesma usada pelo orquestrador local.

Cada tarefa vira um BashOperator que executa o mesmo comando que o aluno
roda no VS Code:

    python -m bigdata_pipeline.transform.pipeline --stage silver

O Airflow coordena (ordem, agenda, novas tentativas, logs, alertas).
A lógica continua no pacote bigdata_pipeline.

Configuração (variáveis de ambiente do Airflow):

    AURORA_PROJECT_DIR  pasta do projeto (contém bigdata_pipeline/ e data/)
                        padrão: a pasta acima de dags/
    AURORA_PYTHON       Python com as dependências do projeto instaladas
                        padrão: o mesmo Python do Airflow

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

PROJECT_DIR = Path(os.getenv("AURORA_PROJECT_DIR", Path(__file__).resolve().parents[1]))
PYTHON = os.getenv("AURORA_PYTHON", sys.executable)
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bigdata_pipeline.orchestration.dag import (  # noqa: E402
    DAG_ID, DESCRIPTION, PARAMS, S3_ENV, SCHEDULE, TASKS, Task,
)

# Airflow 3 (airflow.sdk) com alternativa para Airflow 2.x.
try:
    from airflow.providers.standard.operators.bash import BashOperator
    from airflow.sdk import DAG, Param, TaskGroup
except ImportError:  # Airflow 2.x
    from airflow import DAG
    from airflow.models.param import Param
    from airflow.operators.bash import BashOperator
    from airflow.utils.task_group import TaskGroup

import pendulum  # noqa: E402  (instalado junto com o Airflow)


def to_jinja(value: str) -> str:
    """{max_quarantine_pct} → {{ params.max_quarantine_pct }} (templating do Airflow)."""

    for key in PARAMS:
        value = value.replace("{" + key + "}", "{{ params." + key + " }}")
    return value


def bash_command(task: Task) -> str:
    args = " ".join(shlex.quote(to_jinja(arg)) for arg in task.args)
    return f"{shlex.quote(PYTHON)} -m {task.module} {args}".strip()


def register_failure(context: dict) -> None:
    """Callback de falha: grava o mesmo alerta que o orquestrador local."""

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


PARAM_SPECS = {
    "max_quarantine_pct": Param(PARAMS["max_quarantine_pct"], type="number", minimum=0, maximum=100,
                                description="Percentual máximo de quarentena aceito pelo gate."),
    "min_auc": Param(PARAMS["min_auc"], type="number", minimum=0, maximum=1,
                     description="AUC mínima para promover o modelo de risco de atraso."),
    "api_url": Param(PARAMS["api_url"], type="string", description="Endereço da API de entregas."),
}

with DAG(
    dag_id=DAG_ID,
    description=DESCRIPTION,
    schedule=SCHEDULE,
    start_date=pendulum.datetime(2026, 10, 1, tz="America/Sao_Paulo"),
    catchup=False,                 # não reprocessa os dias anteriores ao ligar o DAG
    max_active_runs=1,             # o aurora.duckdb aceita um único escritor
    params=PARAM_SPECS,
    default_args={
        "owner": "equipe-dados",
        "on_failure_callback": register_failure,
    },
    tags=["aurora-shop", "aula-6"],
    doc_md=__doc__,
) as dag:
    groups: dict[str, TaskGroup] = {}
    operators: dict[str, BashOperator] = {}

    for spec in TASKS:
        if spec.group and spec.group not in groups:
            groups[spec.group] = TaskGroup(group_id=spec.group)
        operators[spec.task_id] = BashOperator(
            task_id=spec.task_id,
            task_group=groups.get(spec.group),
            bash_command=bash_command(spec),
            cwd=str(PROJECT_DIR),
            env={
                **S3_ENV,
                "PYTHONUTF8": "1",
                "AURORA_DAG_ID": DAG_ID,
                "AURORA_RUN_ID": "{{ run_id }}",
                **spec.env,
            },
            append_env=True,
            retries=spec.retries,
            retry_delay=timedelta(seconds=spec.retry_delay),
            execution_timeout=timedelta(seconds=spec.timeout),
            pool=spec.pool or "default_pool",
            doc_md=spec.doc,
        )

    for spec in TASKS:
        for parent in spec.upstream:
            operators[parent] >> operators[spec.task_id]
