from __future__ import annotations

"""
Modelo de risco de atraso de entrega — última tarefa do DAG.

Fluxo:

    Gold (fato_entregas, fato_vendas, dimensões) + Silver (prazo prometido)
            ↓
    dataset de treino versionado      data/ml/risco_atraso/dataset.parquet
            ↓
    treino temporal (passado → futuro) e comparação com um baseline
            ↓
    gate do modelo: só é promovido se for melhor que o baseline
            ↓
    data/models/risco_atraso/<run_id>/    model.joblib + metrics.json
    data/models/risco_atraso/registry.json   histórico de versões
    data/models/risco_atraso/current.json    versão em produção

Assim como o gate de qualidade protege a Gold, o gate do modelo protege
quem consome as previsões: um modelo pior que o baseline é registrado,
mas não substitui a versão em produção.
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from ..transform.pipeline import sql_path
from ..utils import file_sha256


DEFAULT_WAREHOUSE = Path("data/warehouse/aurora.duckdb")
DEFAULT_LAKE = Path("data/lake")
DEFAULT_OUTPUT = Path("data")

TARGET = "atrasou"
CATEGORICAL = ["transportadora", "canal", "uf_cliente", "categoria_principal"]
NUMERIC = ["prazo_prometido_dias", "itens", "valor_pedido", "peso_total_kg", "dia_semana"]


def build_dataset(warehouse: Path, lake: Path, target: Path) -> dict:
    """Monta uma linha por entrega concluída com as características conhecidas no envio."""

    con = duckdb.connect(str(warehouse), read_only=True)
    shipments = sql_path(lake / "silver" / "shipments" / "**" / "*.parquet")
    target.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""
        COPY (
            WITH pedidos AS (
                SELECT f.order_id,
                       any_value(f.canal)              AS canal,
                       any_value(c.uf)                 AS uf_cliente,
                       sum(f.quantidade)               AS itens,
                       sum(f.valor_bruto)              AS valor_pedido,
                       sum(f.quantidade * coalesce(p.peso_kg, 0)) AS peso_total_kg,
                       arg_max(p.categoria, f.valor_bruto)        AS categoria_principal
                FROM gold.fato_vendas f
                JOIN gold.dim_cliente c USING (sk_cliente)
                JOIN gold.dim_produto p USING (sk_produto)
                GROUP BY f.order_id
            )
            SELECT e.shipment_id,
                   e.order_id,
                   CAST(s.created_at AS DATE)                                   AS data_envio,
                   e.transportadora,
                   date_diff('day', CAST(s.created_at AS DATE), CAST(s.promised_at AS DATE))
                                                                                AS prazo_prometido_dias,
                   dayofweek(s.created_at)                                      AS dia_semana,
                   p.canal, p.uf_cliente, p.itens,
                   CAST(p.valor_pedido AS DOUBLE)                               AS valor_pedido,
                   CAST(p.peso_total_kg AS DOUBLE)                              AS peso_total_kg,
                   p.categoria_principal,
                   CAST(NOT e.entregue_no_prazo AS INTEGER)                     AS {TARGET}
            FROM gold.fato_entregas e
            JOIN read_parquet('{shipments}') s USING (shipment_id)
            JOIN pedidos p ON p.order_id = e.order_id
            WHERE e.status = 'delivered' AND s.delivered_at IS NOT NULL
            ORDER BY e.shipment_id
        ) TO '{sql_path(target)}' (FORMAT PARQUET)
    """)
    rows, rate = con.execute(
        f"SELECT count(*), avg({TARGET}) FROM read_parquet('{sql_path(target)}')"
    ).fetchone()
    con.close()
    return {"path": target.as_posix(), "rows": int(rows), "taxa_atraso": round(float(rate or 0), 4),
            "sha256": file_sha256(target)}


def train(dataset_path: Path, test_fraction: float) -> tuple[object, dict]:
    """Treina com o passado e avalia com o futuro, comparando com um baseline."""

    try:
        import pandas as pd  # noqa: F401  (o DuckDB devolve DataFrame)
        from sklearn.compose import ColumnTransformer
        from sklearn.dummy import DummyClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import precision_score, recall_score, roc_auc_score
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
    except ImportError as error:
        raise SystemExit(
            f"Dependência ausente ({error.name}). Instale o requirements.txt da Aula 7 "
            "(scikit-learn e pandas) pelo wheelhouse."
        )

    con = duckdb.connect()
    frame = con.execute(
        f"SELECT * FROM read_parquet('{sql_path(dataset_path)}') ORDER BY data_envio, shipment_id"
    ).df()
    con.close()
    if len(frame) < 100 or frame[TARGET].nunique() < 2:
        raise SystemExit("Dataset insuficiente para treinar: são necessárias as duas classes e ao menos 100 linhas.")

    # Divisão temporal: o modelo é avaliado em entregas posteriores às do treino,
    # como acontecerá em produção. Uma divisão aleatória vazaria o futuro.
    cut = int(len(frame) * (1 - test_fraction))
    train_df, test_df = frame.iloc[:cut], frame.iloc[cut:]
    x_cols = CATEGORICAL + NUMERIC

    model = Pipeline([
        ("preparo", ColumnTransformer([
            ("categorias", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("numeros", StandardScaler(), NUMERIC),
        ])),
        ("classificador", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(train_df[x_cols], train_df[TARGET])
    baseline = DummyClassifier(strategy="prior").fit(train_df[x_cols], train_df[TARGET])

    proba = model.predict_proba(test_df[x_cols])[:, 1]
    predicted = (proba >= 0.5).astype(int)
    metrics = {
        "linhas_treino": int(len(train_df)),
        "linhas_teste": int(len(test_df)),
        "periodo_treino": [str(train_df["data_envio"].min()), str(train_df["data_envio"].max())],
        "periodo_teste": [str(test_df["data_envio"].min()), str(test_df["data_envio"].max())],
        "taxa_atraso_teste": round(float(test_df[TARGET].mean()), 4),
        "auc_modelo": round(float(roc_auc_score(test_df[TARGET], proba)), 4),
        "auc_baseline": round(float(roc_auc_score(
            test_df[TARGET], baseline.predict_proba(test_df[x_cols])[:, 1])), 4),
        "precisao": round(float(precision_score(test_df[TARGET], predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(test_df[TARGET], predicted, zero_division=0)), 4),
    }
    return model, metrics


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Treina e registra o modelo de risco de atraso.")
    parser.add_argument("--warehouse", type=Path, default=DEFAULT_WAREHOUSE)
    parser.add_argument("--lake", type=Path, default=DEFAULT_LAKE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--min-auc", type=float, default=0.60,
                        help="AUC mínima para promover o modelo.")
    parser.add_argument("--min-gain", type=float, default=0.02,
                        help="Ganho mínimo de AUC sobre o baseline para promover.")
    args = parser.parse_args()

    if not args.warehouse.exists():
        raise SystemExit("Warehouse ausente. Execute a Gold antes do modelo.")

    run_id = os.getenv("AURORA_RUN_ID", datetime.now(timezone.utc).strftime("manual__%Y%m%dT%H%M%SZ"))
    # O run_id vira nome de pasta: remove fuso horário e caracteres inválidos no Windows.
    version = re.sub(r"[^0-9A-Za-z_.-]", "", run_id.split("+")[0])
    dataset = build_dataset(args.warehouse, args.lake, args.output / "ml" / "risco_atraso" / "dataset.parquet")
    model, metrics = train(Path(dataset["path"]), args.test_fraction)

    promoted = (
        metrics["auc_modelo"] >= args.min_auc
        and metrics["auc_modelo"] - metrics["auc_baseline"] >= args.min_gain
    )
    models_root = args.output / "models" / "risco_atraso"
    version_dir = models_root / version
    version_dir.mkdir(parents=True, exist_ok=True)

    import joblib
    joblib.dump(model, version_dir / "model.joblib")
    shutil.copy2(dataset["path"], version_dir / "dataset.parquet")

    entry = {
        "versao": version,
        "treinado_em": datetime.now(timezone.utc).isoformat(),
        "status": "promovido" if promoted else "rejeitado",
        "criterio": f"auc >= {args.min_auc} e ganho sobre baseline >= {args.min_gain}",
        "dataset": {k: v for k, v in dataset.items() if k != "path"},
        "metricas": metrics,
        "features": CATEGORICAL + NUMERIC,
    }
    (version_dir / "metrics.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")

    registry_path = models_root / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else []
    registry.append(entry)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    if promoted:
        (models_root / "current.json").write_text(
            json.dumps({"versao": version, "metricas": metrics}, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print("MODELO: risco de atraso de entrega")
    print(f"versão:            {version}")
    print(f"dataset:           {dataset['rows']} entregas | taxa de atraso {dataset['taxa_atraso']:.1%}")
    print(f"treino / teste:    {metrics['linhas_treino']} / {metrics['linhas_teste']} (divisão temporal)")
    print(f"AUC modelo:        {metrics['auc_modelo']}")
    print(f"AUC baseline:      {metrics['auc_baseline']}")
    print(f"precisão / recall: {metrics['precisao']} / {metrics['recall']}")
    if promoted:
        print("DECISÃO: PROMOVIDO. Esta versão passa a ser a current.json.")
    else:
        current = models_root / "current.json"
        kept = json.loads(current.read_text(encoding="utf-8"))["versao"] if current.exists() else "nenhuma"
        print("DECISÃO: REJEITADO. O modelo não supera o baseline com a margem exigida.")
        print(f"Versão em produção mantida: {kept}")


if __name__ == "__main__":
    main()
