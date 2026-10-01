from __future__ import annotations

"""
Sincroniza a Landing local com o Data Lake executado pelo SeaweedFS.

Fluxo realizado por este programa:

    data/lake/landing
            ↓
    localizar cada arquivo
            ↓
    calcular o SHA-256 local
            ↓
    consultar a mesma key no SeaweedFS
            ↓
    enviar somente se o objeto for novo ou tiver mudado

O SeaweedFS oferece uma API compatível com S3. Por isso usamos boto3,
mesmo sem utilizar uma conta ou um serviço da AWS.
"""

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

# boto3 é o cliente Python que executa operações do protocolo S3.
import boto3

# Exceções que podem ser produzidas pelo cliente S3.
from botocore.exceptions import BotoCoreError, ClientError

# Função do próprio projeto que calcula a impressão digital do arquivo.
from ..utils import file_sha256


# Endereço da API S3 exposta pelo SeaweedFS local.
DEFAULT_ENDPOINT_URL = "http://127.0.0.1:8333"

# Contêiner lógico onde os objetos serão armazenados.
DEFAULT_BUCKET = "curso-bigdata"

# Pasta que contém os arquivos brutos criados pelos ELs.
DEFAULT_LANDING = Path("data/lake/landing")


def create_s3_client(endpoint_url: str):
    """Cria o cliente que conversará com a API S3 do SeaweedFS."""

    return boto3.client(
        # Seleciona o conjunto de operações S3 do boto3.
        "s3",

        # Direciona as requisições para o SeaweedFS deste computador.
        # Esta configuração impede que o cliente use um endpoint da AWS.
        endpoint_url=endpoint_url,

        # Credenciais utilizadas somente pelo laboratório local.
        # os.getenv() permite substituir os valores por variáveis de ambiente.
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "admin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "bigdata-secret"),

        # O boto3 exige uma região na configuração do cliente.
        # Ela não significa que os dados serão enviados para essa região.
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def check_connection(client, bucket: str, endpoint_url: str) -> None:
    """Testa se a API S3 está respondendo e se o bucket está acessível."""

    # HEAD consulta o bucket sem enviar ou baixar arquivos.
    client.head_bucket(Bucket=bucket)

    # Se head_bucket() não gerou erro, exibimos o resultado positivo.
    print(json.dumps({"endpoint": endpoint_url, "bucket": bucket, "status": "ok"}, indent=2))


def inspect_bucket(client, bucket: str) -> None:
    """Conta os objetos armazenados e soma seus tamanhos."""

    # A listagem S3 pode ser dividida em várias páginas.
    # O paginador permite percorrer todas elas.
    paginator = client.get_paginator("list_objects_v2")

    # Contadores gerais do bucket.
    object_count = 0
    total_bytes = 0

    # Acumula quantidade e bytes por grupo, por exemplo:
    # landing/sqlite, landing/csv e landing/api.
    prefixes: dict[str, dict[str, int]] = defaultdict(lambda: {"objects": 0, "bytes": 0})

    # Solicita cada página da listagem ao SeaweedFS.
    for page in paginator.paginate(Bucket=bucket):
        # "Contents" contém os objetos presentes na página atual.
        for item in page.get("Contents", []):
            # Key é o nome completo do objeto dentro do bucket.
            key = item["Key"]

            # Size é o tamanho do objeto em bytes.
            size = int(item["Size"])

            # Separa a key para agrupar os objetos pelos dois
            # primeiros componentes do caminho.
            parts = key.split("/")
            prefix = "/".join(parts[:2]) if parts[0] == "landing" and len(parts) > 2 else parts[0]

            # Atualiza os contadores do grupo e do bucket inteiro.
            prefixes[prefix]["objects"] += 1
            prefixes[prefix]["bytes"] += size
            object_count += 1
            total_bytes += size

    # Exibe um resumo em JSON para facilitar a leitura em aula.
    print(
        json.dumps(
            {
                "bucket": bucket,
                "objects": object_count,
                "bytes": total_bytes,
                "prefixes": dict(sorted(prefixes.items())),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def object_has_hash(client, bucket: str, key: str, checksum: str) -> bool:
    """
    Verifica se a key já existe com o mesmo SHA-256.

    True  = o SeaweedFS já possui o mesmo conteúdo; não enviar.
    False = o objeto não existe ou seu conteúdo mudou; fazer upload.
    """

    try:
        # head_object() consulta somente informações e metadados.
        # O conteúdo completo do arquivo não é baixado.
        response = client.head_object(Bucket=bucket, Key=key)

    except ClientError as exc:
        # Recupera o código de erro devolvido pela API S3.
        code = str(exc.response.get("Error", {}).get("Code", ""))

        # Estes códigos significam que a key ainda não existe.
        # Retornamos False para que sync_landing() faça o upload.
        if code in {"404", "NoSuchKey", "NotFound"}:
            return False

        # Outros erros, como credencial inválida ou indisponibilidade,
        # não devem ser confundidos com objeto ausente.
        raise

    # Recupera o SHA-256 salvo como metadado no upload anterior.
    remote_checksum = response.get("Metadata", {}).get("sha256")

    # Compara a impressão digital remota com a do arquivo local.
    return remote_checksum == checksum


def sync_landing(client, bucket: str, source: Path) -> dict[str, int]:
    """
    Percorre a Landing e envia ao SeaweedFS arquivos novos ou alterados.

    Esta é a função central da transição Landing -> SeaweedFS.
    """

    # A sincronização só pode começar se a pasta da Landing existir.
    if not source.is_dir():
        raise SystemExit(f"Landing local não encontrada: {source}")

    # Confirma que o bucket existe e está acessível.
    # Nenhum arquivo é enviado nesta linha.
    client.head_bucket(Bucket=bucket)

    # Contadores apresentados no resultado final.
    uploaded_objects = 0
    skipped_objects = 0
    uploaded_bytes = 0

    # rglob("*") percorre a Landing e todas as suas subpastas.
    # is_file() elimina os diretórios da lista.
    # sorted() deixa a ordem previsível para a demonstração.
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        # Exemplo de path:
        # data/lake/landing/sqlite/orders/orders_001.jsonl

        # Remove a raiz da Landing e preserva somente o caminho interno.
        # as_posix() usa "/" mesmo quando o programa roda no Windows.
        relative_path = path.relative_to(source).as_posix()

        # Exemplo de relative_path:
        # sqlite/orders/orders_001.jsonl

        # Cria a key que identificará o objeto dentro do bucket.
        object_key = f"landing/{relative_path}"

        # Exemplo de object_key:
        # landing/sqlite/orders/orders_001.jsonl

        # Calcula a impressão digital do conteúdo existente na Landing.
        checksum = file_sha256(path)

        # Consulta a mesma key no SeaweedFS e compara os hashes.
        if object_has_hash(client, bucket, object_key, checksum):
            # A key existe e o conteúdo é igual.
            # Portanto, nenhum byte precisa ser reenviado.
            skipped_objects += 1

            # Passa imediatamente para o próximo arquivo.
            continue

        # ESTA É A CHAMADA QUE TRANSFERE O ARQUIVO.
        #
        # upload_file() abre o arquivo local, lê seus bytes e envia
        # uma requisição S3 por HTTP para 127.0.0.1:8333.
        client.upload_file(
            # Arquivo local que será lido.
            str(path),

            # Bucket que receberá o objeto: curso-bigdata.
            bucket,

            # Nome completo do objeto dentro do bucket.
            object_key,

            # Metadado salvo junto do objeto.
            # Na próxima execução, object_has_hash() consultará
            # este valor para decidir se um novo upload é necessário.
            ExtraArgs={"Metadata": {"sha256": checksum}},
        )

        # Se upload_file() terminou sem erro, o objeto foi enviado.
        uploaded_objects += 1

        # Soma o tamanho do arquivo ao total transferido nesta execução.
        uploaded_bytes += path.stat().st_size

    # Devolve as estatísticas para main(), que as imprimirá em JSON.
    return {
        "uploaded_objects": uploaded_objects,
        "skipped_objects": skipped_objects,
        "uploaded_bytes": uploaded_bytes,
    }


def parse_args() -> argparse.Namespace:
    """Define e lê as opções aceitas pelo comando."""

    parser = argparse.ArgumentParser(
        description="Sincroniza a Landing local com um bucket S3 compatível, como SeaweedFS."
    )

    # Permite escolher outra pasta de origem.
    # Sem essa opção, usa data/lake/landing.
    parser.add_argument("--source", type=Path, default=DEFAULT_LANDING)

    # Permite escolher outro bucket.
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET", DEFAULT_BUCKET))

    # Permite escolher outro endpoint S3.
    parser.add_argument(
        "--endpoint-url",
        default=os.getenv("S3_ENDPOINT_URL", DEFAULT_ENDPOINT_URL),
    )

    # --check e --inspect são mutuamente exclusivos:
    # somente um deles pode ser usado em cada execução.
    mode = parser.add_mutually_exclusive_group()

    # Testa a conexão sem realizar upload.
    mode.add_argument("--check", action="store_true", help="Testa acesso ao bucket configurado.")

    # Lista e resume o conteúdo sem realizar upload.
    mode.add_argument("--inspect", action="store_true", help="Lista volumes e objetos no bucket.")

    return parser.parse_args()


def main() -> None:
    """Escolhe o modo de execução e coordena o programa."""

    # Lê as opções informadas no terminal.
    args = parse_args()

    # Cria o cliente boto3 apontando para o endpoint selecionado.
    client = create_s3_client(args.endpoint_url)

    try:
        if args.check:
            # Modo: verificar a conexão.
            check_connection(client, args.bucket, args.endpoint_url)

        elif args.inspect:
            # Modo: inspecionar os objetos existentes.
            inspect_bucket(client, args.bucket)

        else:
            # Modo padrão: executar Landing -> SeaweedFS.
            summary = sync_landing(client, args.bucket, args.source)

            # Mostra quantidade de enviados, ignorados e bytes transferidos.
            print(json.dumps({"bucket": args.bucket, **summary}, ensure_ascii=False, indent=2))

    except (BotoCoreError, ClientError) as exc:
        # Falhas de comunicação não removem os arquivos locais.
        # O pipeline pode ser executado novamente depois da correção.
        raise SystemExit(
            f"Falha ao acessar s3://{args.bucket} em {args.endpoint_url}: {exc}. "
            "Os arquivos da Landing local foram mantidos."
        ) from exc


# Executa main() somente quando este módulo é iniciado pelo comando:
# python -m bigdata_pipeline.lake.sync
if __name__ == "__main__":
    main()
