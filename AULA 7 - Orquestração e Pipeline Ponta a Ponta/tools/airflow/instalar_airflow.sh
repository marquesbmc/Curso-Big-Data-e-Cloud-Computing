#!/usr/bin/env bash
# Instala o Apache Airflow no Ubuntu (WSL) para a Aula 7.
#
# Uso, no terminal do VS Code (PowerShell), dentro da pasta da aula:
#
#     wsl -d Ubuntu-24.04 -- bash tools/airflow/instalar_airflow.sh
#
# Pode ser executado de novo sem problema: o que já estiver instalado é mantido.
set -euo pipefail

AIRFLOW_VERSION="3.1.8"
VENV="$HOME/airflow-venv"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Projeto: $PROJECT_DIR"

echo "[1/5] Ambiente virtual Python ($VENV)"
if ! python3 -m venv /tmp/_teste_venv >/dev/null 2>&1; then
    echo "      Instalando o python3-venv. O Ubuntu vai pedir a senha que você criou para o Linux."
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-venv
fi
rm -rf /tmp/_teste_venv
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
PY="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

echo "[2/5] Apache Airflow $AIRFLOW_VERSION e as integrações com S3 e HTTP (alguns minutos na primeira vez)"
pip install -q --upgrade pip
# Providers: pacotes que ensinam o Airflow a falar com outros sistemas.
#   amazon -> S3Hook e a Connection do tipo "Amazon Web Services" (SeaweedFS)
#   http   -> HttpSensor e a Connection do tipo "HTTP" (API da transportadora)
pip install -q "apache-airflow==$AIRFLOW_VERSION" \
    apache-airflow-providers-amazon \
    apache-airflow-providers-http \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-$AIRFLOW_VERSION/constraints-$PY.txt"

echo "[3/5] Bibliotecas usadas pelas tarefas do pipeline"
# Mesmas versões do wheelhouse do Windows: o aurora.duckdb gravado pelo Airflow
# precisa ser lido pelo DuckDB do .venv, e o modelo precisa dar os mesmos números.
pip install -q "duckdb==1.5.6" "pandas==2.3.3" "scikit-learn==1.9.1" boto3 pytz

echo "[4/5] Configuração (~/airflow-aula7.sh)"
cat > "$HOME/airflow-aula7.sh" <<EOF
# Ambiente do Airflow da Aula 7. Gerado por tools/airflow/instalar_airflow.sh
source "$VENV/bin/activate"
export AIRFLOW_HOME="\$HOME/airflow"
export AURORA_PROJECT_DIR="$PROJECT_DIR"
export AIRFLOW__CORE__DAGS_FOLDER="\$AURORA_PROJECT_DIR/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
# Laboratório local: a interface abre sem tela de login.
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=True
EOF
source "$HOME/airflow-aula7.sh"
airflow db migrate >/dev/null 2>&1
airflow pools set capture_state 1 "ELs compartilham capture_state.json" >/dev/null 2>&1

echo "[5/5] Conferindo o DAG"
airflow dags reserialize >/dev/null 2>&1
if ! airflow dags list -o plain 2>/dev/null | grep -q aurora_shop_pipeline; then
    echo "ERRO: o DAG aurora_shop_pipeline não foi carregado:"
    airflow dags list-import-errors 2>/dev/null
    exit 1
fi

if command -v wslinfo >/dev/null 2>&1 && [ "$(wslinfo --networking-mode 2>/dev/null)" != "mirrored" ]; then
    echo "ATENÇÃO: a rede do WSL não está no modo espelhado (mirrored)."
    echo "         As tarefas não vão alcançar o SeaweedFS e a API. Refaça o passo do .wslconfig."
fi

echo
echo "INSTALAÇÃO CONCLUÍDA: Airflow $AIRFLOW_VERSION com o DAG aurora_shop_pipeline."
