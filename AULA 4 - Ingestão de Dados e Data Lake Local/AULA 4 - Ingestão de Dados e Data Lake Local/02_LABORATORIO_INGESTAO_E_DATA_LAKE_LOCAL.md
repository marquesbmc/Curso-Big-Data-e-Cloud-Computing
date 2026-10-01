# Aula 4 — Laboratório de Ingestão e Data Lake Local

## Objetivo

Executar o pipeline completo em duas fases separadas:

```text
FASE 1
Fontes → ELs → Landing local

FASE 2
Landing local → sync.py → SeaweedFS
```

Durante a Fase 1, não execute a sincronização com o SeaweedFS. Primeiro montaremos e conferiremos toda a Landing. Somente depois iniciaremos a Fase 2 e sincronizaremos a Landing completa.

As explicações conceituais e o código comentado estão em `01_CONTEUDO_TECNICO_INGESTAO_E_DATA_LAKE_LOCAL.md`. Este arquivo é o roteiro operacional do laboratório.

---

## 1. Abrir o projeto

Abra no VS Code:

```text
D:\dev\BIGDATA\AULA 4 - Ingestão de Dados e Data Lake Local
```

No terminal integrado, confirme a pasta:

```powershell
Get-Location
```

Se necessário, entre nela:

```powershell
Set-Location 'D:\dev\BIGDATA\AULA 4 - Ingestão de Dados e Data Lake Local'
```

Confirme que o Python e as fontes existem:

```powershell
Test-Path ..\.venv\Scripts\python.exe
Test-Path .\data\source
```

Os dois resultados devem ser `True`.

### Instalação offline, somente se necessária

```powershell
& ..\.venv\Scripts\python.exe -m pip install --no-index --find-links ..\wheelhouse -r .\requirements.txt
```

---

## 2. Iniciar a API de entregas

Abra um terminal exclusivo para a API e deixe-o aberto:

```powershell
Set-Location 'D:\dev\BIGDATA\AULA 4 - Ingestão de Dados e Data Lake Local'
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.api.app
```

Teste no navegador:

- endereço-base da API: [http://127.0.0.1:8001](http://127.0.0.1:8001);
- documentação: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs);
- saúde: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health);
- primeiro lote: [http://127.0.0.1:8001/shipments?page=1&limit=100](http://127.0.0.1:8001/shipments?page=1&limit=100).

> Receber `{"detail":"Not Found"}` em `http://127.0.0.1:8001/` não indica falha. A API não possui uma rota na raiz.

---

# Fase 1 — Fontes → ELs → Landing

## 3. Executar os cinco ELs e conferir a Landing

Nesta fase, cada comando lê uma fonte e grava somente na Landing local. Não execute ainda o `sync.py` nem qualquer comando do SeaweedFS.

### 3.1 SQLite

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.el.sqlite --source .\data\source --lake .\data\lake
```

Resultado da primeira captura:

```json
{
  "sqlite": {
    "customers": 1000,
    "suppliers": 30,
    "products": 500,
    "orders": 10000,
    "order_items": 29891,
    "payments": 10000
  },
  "run_id": "20261001T021458Z",
  "started_at": "2026-10-01T02:14:58.655168+00:00",
  "finished_at": "2026-10-01T02:14:58.977352+00:00"
}
```

O JSON é o resumo desta execução do EL. Os números indicam quantas linhas foram capturadas **nesta execução**, e não obrigatoriamente o total histórico do banco.

| Campo | Significado |
| --- | --- |
| `customers: 1000` | 1.000 clientes foram lidos e gravados na Landing |
| `suppliers: 30` | 30 fornecedores foram capturados |
| `products: 500` | 500 produtos foram capturados |
| `orders: 10000` | 10.000 pedidos foram capturados |
| `order_items: 29891` | 29.891 itens pertencentes aos pedidos foram capturados |
| `payments: 10000` | 10.000 registros de pagamento foram capturados |
| `run_id` | Identificador único desta execução; também aparece no nome dos arquivos criados |
| `started_at` | Horário em que a execução começou |
| `finished_at` | Horário em que a execução terminou |

O `run_id` segue o formato:

```text
20261001T021458Z
│       │      └── Z: horário UTC
│       └───────── 02:14:58
└───────────────── 01/10/2026
```

Os horários terminam em `+00:00` ou `Z` porque o programa registra as execuções em **UTC**. Por isso, uma execução realizada na noite de 30 de setembro em Brasília pode aparecer como 1º de outubro no relatório.

Neste exemplo, a execução começou às `02:14:58.655168` e terminou às `02:14:58.977352`, levando aproximadamente **0,32 segundo**.

Para cada tabela com registros novos, foi criado um arquivo JSON Lines:

```text
data/lake/landing/sqlite/customers/customers_20261001T021458Z.jsonl
data/lake/landing/sqlite/suppliers/suppliers_20261001T021458Z.jsonl
data/lake/landing/sqlite/products/products_20261001T021458Z.jsonl
data/lake/landing/sqlite/orders/orders_20261001T021458Z.jsonl
data/lake/landing/sqlite/order_items/order_items_20261001T021458Z.jsonl
data/lake/landing/sqlite/payments/payments_20261001T021458Z.jsonl
```

Cada linha de um arquivo `.jsonl` representa um registro da tabela. O EL também atualiza os watermarks em `data/lake/control/capture_state.json`, permitindo que a próxima execução procure somente IDs maiores.

O bloco exibido no terminal é um **objeto JSON** que resume a execução. Já os dados capturados não formam um único objeto: neste caso, o EL criou seis arquivos na Landing, um para cada tabela. Quando a Landing for sincronizada com o SeaweedFS, cada um desses arquivos será armazenado como um **objeto separado** no bucket `curso-bigdata`.

Destino: `data/lake/landing/sqlite/`.

### 3.2 CSV

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.el.csv --source .\data\source --lake .\data\lake
```

Resultado da primeira captura:

```json
{
  "csv": {
    "copied": 6,
    "skipped": 0,
    "bytes": 90656
  },
  "run_id": "20261001T021817Z",
  "started_at": "2026-10-01T02:18:17.500509+00:00",
  "finished_at": "2026-10-01T02:18:17.517541+00:00"
}
```

O objeto JSON resume o que aconteceu com os **arquivos CSV** nesta execução:

| Campo | Significado |
| --- | --- |
| `copied: 6` | Seis arquivos CSV eram novos ou ainda não estavam registrados e foram copiados para a Landing |
| `skipped: 0` | Nenhum CSV foi ignorado; na primeira captura, todos precisavam ser copiados |
| `bytes: 90656` | Foram copiados 90.656 bytes, aproximadamente 88,5 KiB |
| `run_id` | Identificador único da execução, registrado também no relatório de controle |
| `started_at` | Horário UTC em que a captura começou |
| `finished_at` | Horário UTC em que a captura terminou |

Neste EL, `copied` e `skipped` representam **quantidades de arquivos**, não quantidades de linhas dentro dos CSVs.

Os seis arquivos copiados foram:

```text
data/lake/landing/csv/catalog.csv
data/lake/landing/csv/2026-08-31/inventory.csv
data/lake/landing/csv/2026-09-07/inventory.csv
data/lake/landing/csv/2026-09-14/inventory.csv
data/lake/landing/csv/2026-09-21/inventory.csv
data/lake/landing/csv/2026-09-28/inventory.csv
```

A execução começou às `02:18:17.500509` e terminou às `02:18:17.517541`, levando aproximadamente **0,017 segundo**, ou 17 milissegundos.

Para reconhecer os arquivos em uma próxima execução, o EL calcula o SHA-256 de cada CSV e registra esse valor no manifest existente em `data/lake/control/capture_state.json`.

Se o mesmo comando for repetido sem alterar os CSVs, o resultado esperado será semelhante a:

```json
{
  "csv": {
    "copied": 0,
    "skipped": 6,
    "bytes": 0
  }
}
```

Isso significa que os seis caminhos e seus respectivos hashes já eram conhecidos. Nenhuma cópia adicional foi criada.

O resultado apresentado no terminal é um **objeto JSON de resumo**. Na Landing, porém, temos seis arquivos CSV separados. Depois da sincronização com o SeaweedFS, cada arquivo será armazenado como um **objeto separado** no bucket `curso-bigdata`.

Destino: `data/lake/landing/csv/`.

### 3.3 JSON

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.el.json --source .\data\source --lake .\data\lake
```

Resultado da primeira captura:

```json
{
  "json": {
    "copied": 1,
    "skipped": 0,
    "bytes": 1834
  },
  "run_id": "20261001T022024Z",
  "started_at": "2026-10-01T02:20:24.431876+00:00",
  "finished_at": "2026-10-01T02:20:24.435916+00:00"
}
```

O objeto JSON apresentado no terminal resume a captura dos **arquivos JSON**:

| Campo | Significado |
| --- | --- |
| `copied: 1` | Um arquivo JSON era novo e foi copiado para a Landing |
| `skipped: 0` | Nenhum arquivo JSON foi ignorado nesta primeira captura |
| `bytes: 1834` | Foram copiados 1.834 bytes, aproximadamente 1,79 KiB |
| `run_id` | Identificador único desta execução e do relatório de controle |
| `started_at` | Horário UTC em que a captura começou |
| `finished_at` | Horário UTC em que a captura terminou |

`copied: 1` significa **um arquivo copiado**, e não um único registro de negócio. Um arquivo JSON pode conter uma lista com várias campanhas ou outras estruturas internas.

O arquivo copiado foi:

```text
Origem:
data/source/files/campaigns.json

Destino:
data/lake/landing/json/campaigns.json
```

A execução começou às `02:20:24.431876` e terminou às `02:20:24.435916`, levando aproximadamente **0,004 segundo**, ou quatro milissegundos.

O EL calcula o SHA-256 de `campaigns.json` e registra o caminho e o hash no manifest existente em `data/lake/control/capture_state.json`.

Se o comando for repetido sem alterar o arquivo:

```json
{
  "json": {
    "copied": 0,
    "skipped": 1,
    "bytes": 0
  }
}
```

Nesse caso, o caminho já é conhecido e o SHA-256 permanece igual; por isso nenhuma nova cópia é criada.

A resposta do terminal é um **objeto JSON de resumo**. O arquivo `campaigns.json` existente na Landing é o dado capturado. Depois da sincronização, esse arquivo será armazenado como um **objeto** no bucket `curso-bigdata`, com uma key semelhante a:

```text
landing/json/campaigns.json
```

Destino: `data/lake/landing/json/`.

### 3.4 Eventos

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.el.events --source .\data\source --lake .\data\lake
```

Resultado da primeira captura:

```json
{
  "events": {
    "copied": 30,
    "skipped": 0,
    "bytes": 23459114
  },
  "run_id": "20261001T022120Z",
  "started_at": "2026-10-01T02:21:20.709317+00:00",
  "finished_at": "2026-10-01T02:21:20.806960+00:00"
}
```

O objeto JSON resume a captura dos arquivos de eventos:

| Campo | Significado |
| --- | --- |
| `copied: 30` | Trinta arquivos de eventos eram novos e foram copiados para a Landing |
| `skipped: 0` | Nenhum arquivo foi ignorado na primeira captura |
| `bytes: 23459114` | Foram copiados 23.459.114 bytes, aproximadamente 23,46 MB ou 22,37 MiB |
| `run_id` | Identificador único da execução e do relatório de controle |
| `started_at` | Horário UTC em que a captura começou |
| `finished_at` | Horário UTC em que a captura terminou |

`copied: 30` representa **30 arquivos**, não 30 eventos. Cada arquivo JSONL possui muitas linhas, e cada linha representa um evento.

Os arquivos estão separados por dia:

```text
data/lake/landing/events/
├── events_2026-09-01.jsonl
├── events_2026-09-02.jsonl
├── events_2026-09-03.jsonl
├── ...
├── events_2026-09-29.jsonl
└── events_2026-09-30.jsonl
```

A extensão `.jsonl` significa **JSON Lines**:

```text
linha 1 → um evento em JSON
linha 2 → outro evento em JSON
linha 3 → outro evento em JSON
...
```

A execução começou às `02:21:20.709317` e terminou às `02:21:20.806960`, levando aproximadamente **0,098 segundo**, ou 98 milissegundos.

Para controlar a incrementalidade, o EL calcula o SHA-256 de cada arquivo e registra o resultado em `event_manifest`, dentro de `data/lake/control/capture_state.json`.

Se o comando for repetido sem alterar os arquivos:

```json
{
  "events": {
    "copied": 0,
    "skipped": 30,
    "bytes": 0
  }
}
```

Isso significa que os 30 caminhos já eram conhecidos e seus hashes permaneciam iguais.

A resposta apresentada no terminal é um **objeto JSON de resumo**. Na Landing existem 30 arquivos JSONL separados. Depois da sincronização, cada arquivo será armazenado como um **objeto separado** no bucket `curso-bigdata`, com keys semelhantes a:

```text
landing/events/events_2026-09-01.jsonl
landing/events/events_2026-09-02.jsonl
...
landing/events/events_2026-09-30.jsonl
```

Destino: `data/lake/landing/events/`.

### 3.5 API de entregas

A API iniciada no item 2 precisa continuar rodando.

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.el.api --source .\data\source --lake .\data\lake --api-url http://127.0.0.1:8001
```

Resultado da primeira captura:

```json
{
  "api": {
    "rows": 10000,
    "pages": 10
  },
  "run_id": "20261001T022153Z",
  "started_at": "2026-10-01T02:21:53.433091+00:00",
  "finished_at": "2026-10-01T02:21:53.877324+00:00"
}
```

O objeto JSON resume a captura das entregas disponibilizadas pela API:

| Campo | Significado |
| --- | --- |
| `rows: 10000` | Dez mil registros de entrega foram recebidos e gravados na Landing |
| `pages: 10` | O EL precisou fazer dez requisições paginadas à API |
| `run_id` | Identificador único da execução; também aparece no nome do arquivo criado |
| `started_at` | Horário UTC em que a captura começou |
| `finished_at` | Horário UTC em que a captura terminou |

A API permite receber no máximo 1.000 entregas por requisição. Por isso, 10.000 registros foram divididos em dez páginas:

```text
página 1  → até 1.000 entregas
página 2  → até 1.000 entregas
...
página 10 → até 1.000 entregas

Total → 10.000 entregas
```

Em cada requisição, a API devolve um objeto JSON semelhante a:

```json
{
  "page": 1,
  "limit": 1000,
  "count": 1000,
  "has_more": true,
  "after_sequence": 0,
  "items": [
    "registros de entrega"
  ]
}
```

O EL lê a lista `items` e grava cada entrega como uma linha no mesmo arquivo JSONL:

```text
data/lake/landing/api/shipments/
└── shipments_20261001T022153Z.jsonl
```

Portanto:

- a API respondeu dez objetos JSON, um por página;
- os dez objetos continham, juntos, 10.000 entregas;
- o EL reuniu as entregas em um arquivo JSONL;
- cada linha do JSONL representa uma entrega.

A execução começou às `02:21:53.433091` e terminou às `02:21:53.877324`, levando aproximadamente **0,44 segundo**.

Depois da captura, o EL registra em `data/lake/control/capture_state.json` a maior `source_sequence` recebida. Na próxima execução, esse valor é enviado como `after_sequence`, para que a API devolva somente entregas posteriores.

Se o comando for repetido sem novas entregas:

```json
{
  "api": {
    "rows": 0,
    "pages": 0
  }
}
```

Como nenhuma entrega nova foi recebida, o arquivo vazio é removido e nenhuma cópia adicional permanece na Landing.

A saída mostrada no terminal é um **objeto JSON de resumo**. As respostas recebidas da API também são objetos JSON. O dado persistido na Landing, porém, é um arquivo JSONL. Depois da sincronização, esse arquivo será armazenado como um **objeto** no bucket `curso-bigdata`, com uma key semelhante a:

```text
landing/api/shipments/shipments_20261001T022153Z.jsonl
```

Destino: `data/lake/landing/api/shipments/`.

### 3.6 Conferir o resultado na pasta Landing

Depois dos cinco ELs, abra no Explorer do VS Code:

```text
data
└── lake
    └── landing
```

A estrutura esperada é:

```text
data/lake/landing/
├── sqlite/
├── csv/
├── json/
├── events/
└── api/
```

Também é possível listar os arquivos pelo terminal:

```powershell
Get-ChildItem .\data\lake\landing -Recurse -File | Select-Object FullName, Length
```

Confira o resumo local:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.inspect --data .\data
```

O objetivo desta conferência é simples:

- verificar se as cinco pastas foram criadas;
- confirmar que cada EL produziu arquivos;
- confirmar que os dados ainda estão apenas na Landing local.

Não sincronize ainda. A atualização do SeaweedFS será feita separadamente na Fase 2.

---

# Fase 2 — Landing → SeaweedFS

## 4. Iniciar e conhecer o SeaweedFS

Abra um terminal exclusivo para o SeaweedFS e deixe-o aberto:

```powershell
Set-Location 'D:\dev\BIGDATA\AULA 4 - Ingestão de Dados e Data Lake Local'
$env:AWS_ACCESS_KEY_ID = "admin"
$env:AWS_SECRET_ACCESS_KEY = "bigdata-secret"
$env:S3_BUCKET = "curso-bigdata"
$env:S3_ENDPOINT_URL = "http://127.0.0.1:8333"
$seaweedData = (Resolve-Path ..\seaweed-data-working-copy).Path
& ..\tools\seaweedfs\weed.exe mini -dir $seaweedData
```

O modo `mini` inicia, em uma única máquina, os componentes necessários ao laboratório.

### 4.1 Endereços locais

| Endereço | Componente | Uso no laboratório |
| --- | --- | --- |
| [http://127.0.0.1:8888](http://127.0.0.1:8888) | Filer | Navegar visualmente pelas pastas e objetos |
| [http://127.0.0.1:8888/buckets/curso-bigdata/](http://127.0.0.1:8888/buckets/curso-bigdata/) | Bucket da aula | Abrir diretamente o conteúdo de `curso-bigdata` |
| [http://127.0.0.1:9333](http://127.0.0.1:9333) | Master | Consultar o serviço que coordena os volumes |
| [http://127.0.0.1:8080](http://127.0.0.1:8080) | Volume Server | Consultar o serviço que guarda os bytes |
| `http://127.0.0.1:8333` | API S3 | Endpoint usado pelo boto3 e pelo `sync.py` |

A porta `8333` não é uma interface de navegação. Abrir sua raiz no navegador pode mostrar `AccessDenied`; isso é esperado.

### 4.2 Como navegar pelo Filer

Abra:

[http://127.0.0.1:8888/buckets/curso-bigdata/](http://127.0.0.1:8888/buckets/curso-bigdata/)

Depois da sincronização, a navegação esperada será:

```text
buckets/
└── curso-bigdata/
    └── landing/
        ├── sqlite/
        ├── csv/
        ├── json/
        ├── events/
        └── api/
```

Significado:

- `buckets/`: área em que o Filer apresenta os buckets S3;
- `curso-bigdata/`: bucket utilizado pela aula;
- `landing/`: prefixo que recebe os arquivos da Landing local;
- `sqlite/`, `csv/`, `json/`, `events/` e `api/`: separação por origem.

Antes da primeira sincronização, o bucket pode estar vazio. Não copie arquivos manualmente pelo Filer: o laboratório usará `sync.py` e a API S3.

Os dados físicos do SeaweedFS ficam em `..\seaweed-data-working-copy`. Essa pasta pertence ao serviço e não deve ser editada manualmente.

---

## 5. Testar o acesso ao Data Lake

No terminal usado para os comandos do laboratório, defina as mesmas configurações:

```powershell
$env:AWS_ACCESS_KEY_ID = "admin"
$env:AWS_SECRET_ACCESS_KEY = "bigdata-secret"
$env:S3_BUCKET = "curso-bigdata"
$env:S3_ENDPOINT_URL = "http://127.0.0.1:8333"
```

Teste a conexão:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.lake.sync --check
```

Resultado esperado:

```json
{
  "endpoint": "http://127.0.0.1:8333",
  "bucket": "curso-bigdata",
  "status": "ok"
}
```

Inspecione o bucket antes da sincronização:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.lake.sync --inspect
```

---

## 6. Sincronizar toda a Landing

Execute o `sync.py` uma única vez:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.lake.sync --source .\data\lake\landing
```

Resultado da primeira sincronização:

```json
{
  "bucket": "curso-bigdata",
  "uploaded_objects": 44,
  "skipped_objects": 0,
  "uploaded_bytes": 34581470
}
```

O objeto JSON resume a transferência da Landing para o SeaweedFS:

| Campo | Significado |
| --- | --- |
| `bucket: "curso-bigdata"` | Nome do contêiner lógico que recebeu os objetos |
| `uploaded_objects: 44` | Quarenta e quatro arquivos da Landing foram enviados e armazenados como objetos |
| `skipped_objects: 0` | Nenhum arquivo foi ignorado, pois os objetos ainda não existiam com o mesmo hash |
| `uploaded_bytes: 34581470` | Foram transferidos 34.581.470 bytes, aproximadamente 34,58 MB ou 32,98 MiB |

Os 44 objetos correspondem aos arquivos produzidos pelos cinco ELs:

| Origem | Arquivos na Landing | Objetos enviados |
| --- | ---: | ---: |
| SQLite | 6 arquivos JSONL | 6 |
| CSV | 6 arquivos CSV | 6 |
| JSON | 1 arquivo JSON | 1 |
| Eventos | 30 arquivos JSONL | 30 |
| API | 1 arquivo JSONL | 1 |
| **Total** | **44 arquivos** | **44 objetos** |

O cálculo é:

```text
6 + 6 + 1 + 30 + 1 = 44 objetos
```

Somente `data/lake/landing` foi informada em `--source`. Por isso, os arquivos existentes em `data/lake/control`, como `capture_state.json` e os relatórios de execução, **não foram enviados**.

Durante o upload, cada arquivo local preserva seu caminho na forma de uma key:

```text
Arquivo local:
data/lake/landing/sqlite/orders/orders_20261001T021458Z.jsonl

Objeto no bucket:
bucket: curso-bigdata
key: landing/sqlite/orders/orders_20261001T021458Z.jsonl
```

O `sync.py` também salva o SHA-256 nos metadados de cada objeto. Esse hash permitirá que a próxima sincronização reconheça os arquivos que continuam iguais.

A resposta do terminal é um **objeto JSON de resumo**. Os 44 itens armazenados no SeaweedFS são **objetos de dados separados**, cada um identificado por sua própria key dentro do bucket `curso-bigdata`.

Uma execução do programa:

```text
localiza todos os arquivos da Landing
        ↓
processa cada arquivo
        ↓
compara o SHA-256 local com o remoto
        ↓
envia somente arquivos ausentes ou alterados
```

Não execute `sync.py` depois de cada EL. Os cinco ELs já montaram a Landing completa na Fase 1; agora uma única sincronização percorre todas as suas subpastas.

---

## 7. Conferir o SeaweedFS

Inspecione o bucket:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.lake.sync --inspect
```

Abra o Filer:

[http://127.0.0.1:8888/buckets/curso-bigdata/](http://127.0.0.1:8888/buckets/curso-bigdata/)

Estrutura esperada:

```text
curso-bigdata/
└── landing/
    ├── sqlite/
    ├── csv/
    ├── json/
    ├── events/
    └── api/
```

O resumo do terminal informa:

- `uploaded_objects`: arquivos enviados nesta execução;
- `skipped_objects`: arquivos que já estavam iguais;
- `uploaded_bytes`: bytes efetivamente transferidos.

---

## 8. Repetir a sincronização sem alterar a Landing

Execute novamente:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.lake.sync --source .\data\lake\landing
```

Resultado esperado:

```json
{
  "bucket": "curso-bigdata",
  "uploaded_objects": 0,
  "skipped_objects": 44,
  "uploaded_bytes": 0
}
```

O número de objetos ignorados pode variar conforme a Landing preparada. O comportamento importante é:

```text
nenhuma mudança na Landing
        ↓
uploaded_objects = 0
uploaded_bytes = 0
```

Essa repetição testa a idempotência da **Fase 2**.

---

## 9. Encerrar o laboratório

Nos terminais da API e do SeaweedFS, pressione:

```text
Ctrl+C
```

Isso encerra os serviços, mas mantém:

- as fontes em `data\source`;
- a Landing e os controles em `data\lake`;
- os objetos do SeaweedFS em `..\seaweed-data-working-copy`.

---

## Apêndice — Recomeçar sem histórico

Use estes comandos somente quando realmente quiser descartar o resultado atual.

### Apagar somente o Lake local

> Remove `data\lake` sem backup. As fontes e o bucket permanecem.

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.lake.reset --data .\data --no-backup
```

Confirmação:

```text
APAGAR LAKE LOCAL
```

### Apagar o Lake local e o bucket

> Ação permanente. O SeaweedFS precisa estar rodando.

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.lake.reset --data .\data --clear-seaweedfs --no-backup
```

Confirmação:

```text
APAGAR TUDO curso-bigdata
```

O conteúdo de `data\source` não é alterado.
