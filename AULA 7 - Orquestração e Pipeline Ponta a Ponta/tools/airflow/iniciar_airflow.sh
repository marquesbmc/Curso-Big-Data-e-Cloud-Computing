#!/usr/bin/env bash
# Inicia o Apache Airflow (interface em http://localhost:8080).
#
# Uso, no terminal do VS Code (PowerShell), dentro da pasta da aula:
#
#     wsl -d Ubuntu-24.04 -- bash tools/airflow/iniciar_airflow.sh
#
# Ctrl+C encerra o Airflow.
set -euo pipefail

if [ ! -f "$HOME/airflow-aula7.sh" ]; then
    echo "Airflow não instalado. Execute antes: bash tools/airflow/instalar_airflow.sh"
    exit 1
fi
source "$HOME/airflow-aula7.sh"

echo "Iniciando o Airflow. Quando aparecer 'Airflow is ready', abra http://localhost:8080"
echo "Mantenha este terminal aberto. Ctrl+C encerra o Airflow."
exec airflow standalone
