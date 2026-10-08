# Aula 5 — Laboratório de ETL, Qualidade e Data Warehouse

## Objetivo

Continuar exatamente do ponto em que o Laboratório 4 terminou e transformar os dados da **Landing** em dados confiáveis para análise.

Ao final deste laboratório, o aluno terá construído:

```text
SeaweedFS
├── landing/       dados capturados na Aula 4
├── bronze/        cópia bruta em Parquet + linhagem
├── silver/        dados aprovados, tipados e padronizados
└── quarantine/    registros reprovados + motivos

data/warehouse/
└── aurora.duckdb
    └── gold
        ├── dimensões
        ├── fatos
        └── marts
```

O laboratório está dividido em cinco fases:

```text
Fase 0 — Retomar o ambiente da Aula 4
Fase 1 — Landing → Bronze
Fase 2 — Bronze → Silver + Quarentena
Fase 3 — Silver → Gold no Data Warehouse
Fase 4 — Validar o pipeline completo
```

> Nesta aula, o Python coordena a execução. As transformações e regras de negócio são executadas em SQL pelo DuckDB.

---

# Fase 0 — Retomar o ambiente da Aula 4

## 1. Confirmar o ponto de partida

O Laboratório 4 terminou com os dados armazenados no bucket `curso-bigdata`, dentro do prefixo `landing/`:

```text
curso-bigdata/
└── landing/
    ├── sqlite/
    ├── csv/
    ├── json/
    ├── events/
    └── api/
```

Nesta aula não executaremos novamente os cinco ELs. Usaremos a cópia que já está preservada no SeaweedFS.

Confira se o ambiente virtual criado na aula anterior existe:

```powershell
Test-Path ..\.venv\Scripts\python.exe
```

Resultado esperado:

```text
True
```

Se o resultado for `False`, execute no VS Code:

1. pressione `Ctrl+Shift+P`;
2. escolha `Tasks: Run Task`;
3. execute `00. Criar ambiente virtual`;
4. execute `03. Instalar dependências offline`.

## 2. Iniciar o SeaweedFS

No VS Code:

1. pressione `Ctrl+Shift+P`;
2. escolha `Tasks: Run Task`;
3. execute `50. Iniciar SeaweedFS`;
4. mantenha o terminal aberto durante toda a aula.

Abra o Filer no navegador:

<http://127.0.0.1:8888/buckets/curso-bigdata/>

Confirme que o prefixo `landing/` contém os dados da aula anterior.

> A porta `8888` é usada para navegar. A porta `8333` é o endpoint S3 usado pelo boto3 e pelo DuckDB.

## 3. Testar a entrada da plataforma

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.pipeline --check
```

Ou execute a tarefa:

```text
80. Verificar pré-requisitos da Aula 5
```

Resultado esperado:

```json
{
  "landing": "data/lake/landing",
  "landing_files": 44,
  "duckdb": "1.5.6",
  "status": "ok"
}
```

O número de objetos pode ser maior caso lotes incrementais tenham sido produzidos ao final da Aula 4. O importante é que:

- a Landing produzida na Aula 4 esteja disponível;
- haja arquivos em `data/lake/landing`;
- o DuckDB esteja instalado.

### Se o DuckDB não estiver disponível

Execute a instalação das dependências da aula:

```powershell
& ..\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Para a aula offline, o pacote `duckdb` deve estar previamente incluído no `wheelhouse`.

O comando de inspeção também precisa do pacote `pytz` para exibir as colunas
`TIMESTAMPTZ`. Se aparecer `Required module 'pytz' failed to import`, execute:

```powershell
python -m pip install pytz
```

Depois, repita o comando de inspeção. Não é necessário reconstruir a Bronze.

---

# Fase 1 — Landing → Bronze

## 4. Construir a camada Bronze

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.pipeline --stage bronze
```

Ou execute a tarefa:

```text
81. Construir Bronze
```

Resultado esperado para o estado inicial preparado:

```json
{
  "stage": "bronze",
  "source_files": 44,
  "written_files": 44,
  "rows": 164642,
  "target": "data/lake/bronze",
  "status": "success"
}
```

Cada objeto da Landing gera um objeto Parquet de mesmo nome lógico na Bronze:

```text
landing/events/events_2026-09-01.jsonl
                ↓
bronze/events/events_2026-09-01.parquet
```

O conteúdo não foi corrigido nem filtrado. A Bronze apenas:

- converteu os formatos de origem para Parquet;
- acrescentou `_source_file`;
- acrescentou `_ingested_at`;
- preservou todos os registros recebidos.

## 5. Conferir a organização da Bronze

No Explorer do VS Code, abra:

```text
data/lake/bronze/
```

Na Fase 4, essas camadas serão publicadas no SeaweedFS e também poderão ser conferidas no Filer.

Estrutura esperada:

```text
bronze/
├── sqlite/
│   ├── customers/
│   ├── suppliers/
│   ├── products/
│   ├── orders/
│   ├── order_items/
│   └── payments/
├── csv/
├── json/
├── events/
└── api/
```

Compare os formatos:

| Camada | Formatos | Papel |
| --- | --- | --- |
| Landing | JSONL, CSV e JSON | Preservar exatamente o que chegou |
| Bronze | Parquet | Criar uma cópia analítica com linhagem |

## 6. Inspecionar um arquivo Parquet

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.inspect --layer bronze --dataset events --limit 5
```

Ou execute a tarefa:

```text
82. Inspecionar Bronze de eventos
```

Além das colunas originais, localize:

| Coluna | Conteúdo |
| --- | --- |
| `_source_file` | Key do objeto que originou a linha |
| `_ingested_at` | Momento em que a linha entrou na Bronze |

Observe que valores problemáticos, como `data-invalida`, ainda aparecem. Isso é esperado.

> Pergunta para discussão: se a Bronze corrigisse a data inválida, ainda conseguiríamos provar exatamente o que a fonte enviou?

## 7. Repetir a Bronze

Execute novamente:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.pipeline --stage bronze
```

O total de arquivos na Bronze deve permanecer igual. O nome do destino é determinado pelo nome da origem; por isso a segunda execução substitui logicamente o mesmo resultado e não cria uma cópia adicional.

```text
mesma origem + mesma regra = mesmo destino
```

Essa é a idempotência da fronteira `Landing → Bronze`.

---

# Fase 2 — Bronze → Silver + Quarentena

## 8. Executar as regras de qualidade

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.pipeline --stage silver
```

Ou execute a tarefa:

```text
83. Construir Silver e Quarentena
```

Resultado resumido esperado:

```text
Fonte       Lidos     Aprovados   Quarentena   Percentual
events      100210    97968       2242          2,24%
catalog        501      497          4          0,80%
shipments    10000     9799        201          2,01%
inventory     2500     2496          4          0,16%
```

Os números podem crescer caso a turma tenha produzido lotes incrementais. A relação que não pode mudar é:

```text
lidos na Bronze = aprovados na Silver + enviados à quarentena
```

### O que aconteceu nesta execução

```text
Bronze
   │
   ├── registro aprovado ──▶ Silver
   │
   └── registro reprovado ─▶ Quarentena + motivo
```

A Silver realizou as seguintes operações:

- converteu textos em tipos adequados;
- padronizou códigos e categorias;
- converteu centavos para `DECIMAL(12,2)`;
- manteve a versão mais recente de cada registro operacional;
- verificou referências entre clientes, produtos, pedidos e fornecedores;
- removeu duplicatas da camada aprovada;
- separou os registros que não podiam ser corrigidos com segurança.

## 9. Observar uma correção segura

Inspecione o catálogo aprovado:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.inspect --layer silver --dataset catalog --limit 20
```

Procure categorias que chegaram como:

```text
beleza
BELEZA
 Jardim
```

Na Silver, elas devem aparecer com o valor oficial da tabela de domínio:

```text
Beleza
Jardim
```

Essa correção é permitida porque existe uma regra determinística e uma lista oficial de categorias.

## 10. Inspecionar a quarentena de eventos

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.inspect --layer quarantine --dataset events --limit 20
```

Ou execute a tarefa:

```text
84. Inspecionar quarentena de eventos
```

Cada linha mantém os dados originais e acrescenta:

| Coluna | Exemplo |
| --- | --- |
| `motivos` | `cliente_inexistente, dispositivo_ausente` |
| `_source_file` | `events/events_2026-09-14.jsonl` |
| `quarantined_at` | horário em que a regra foi aplicada |

Um registro pode falhar em mais de uma regra. Por isso `motivos` pode conter uma lista.

> Não usamos a coluna didática `injected_issue` para aprovar ou reprovar. Uma fonte real não informa quais linhas foram geradas com erro.

## 11. Consultar o relatório de qualidade

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.quality_report
```

Ou execute a tarefa:

```text
85. Exibir relatório de qualidade
```

O relatório deve mostrar pelo menos:

- total lido por conjunto de dados;
- total aprovado;
- total em quarentena;
- percentual reprovado;
- quantidade por motivo;
- resultado da reconciliação.

Exemplo de distribuição dos motivos de eventos:

```text
data_invalida          441
cliente_inexistente    425
dispositivo_ausente    396
tipo_ausente           392
produto_inexistente    379
duplicado              210
```

A soma dos motivos pode ser maior que o total de linhas em quarentena, porque uma linha pode possuir mais de um motivo.

## 12. Verificar o particionamento

No Filer, abra o conjunto de eventos da Silver:

```text
silver/events/
```

Estrutura esperada:

```text
silver/events/
├── event_date=2026-09-01/
├── event_date=2026-09-02/
├── event_date=2026-09-03/
└── ...
```

O diretório `event_date=...` representa uma partição. Uma consulta limitada a um dia pode ignorar as outras partições.

```text
consulta de 14/09
       ↓
lê event_date=2026-09-14
       ↓
ignora os demais dias
```

Esse comportamento é chamado de **partition pruning**.

---

# Fase 3 — Silver → Gold no Data Warehouse

## 13. Construir dimensões, fatos e marts

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.pipeline --stage gold
```

Ou execute a tarefa:

```text
86. Construir Gold no DuckDB
```

Resultado esperado:

```json
{
  "stage": "gold",
  "warehouse": "data/warehouse/aurora.duckdb",
  "tables": {
    "dim_data": 31,
    "dim_cliente": 1000,
    "dim_produto": 500,
    "fato_vendas": 29891,
    "fato_eventos": 97968,
    "fato_entregas": 9799
  },
  "status": "success"
}
```

O arquivo abaixo é o Data Warehouse local da Aurora Shop:

```text
data/warehouse/aurora.duckdb
```

Estrutura lógica esperada:

```text
gold
├── dim_data
├── dim_cliente
├── dim_produto
├── fato_vendas
├── fato_eventos
├── fato_entregas
├── mart_receita_categoria_dia
├── mart_funil_origem
├── mart_entregas_transportadora
└── mart_campanhas
```

## 14. Conferir o grão da tabela fato de vendas

Execute a validação:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.validate --check fact-grain
```

Resultado esperado no estado inicial:

```text
fato_vendas.linhas          = 29891
fato_vendas.itens_distintos = 29891
resultado                   = OK
```

As duas contagens precisam ser iguais porque uma linha da `fato_vendas` representa **um item de pedido**.

Se um `JOIN` multiplicasse linhas, a contagem total ficaria maior que a quantidade de `item_id` distintos. Essa validação detecta o problema antes que ele infle a receita.

## 15. Consultar receita por categoria

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.query --name receita-categoria
```

Ou execute a tarefa:

```text
87. Consultar receita por categoria
```

A consulta usa o mart `gold.mart_receita_categoria_dia` e aplica a definição oficial:

```text
receita aprovada = soma dos itens
                   de pedidos não cancelados
                   com pagamento aprovado
```

No estado preparado, o total esperado é:

```text
R$ 77.740.683,02
```

O valor bruto de todos os itens, sem aplicar a regra de negócio, seria:

```text
R$ 90.724.701,35
```

A diferença demonstra por que a Gold não é apenas uma cópia da Silver: ela registra definições de negócio.

## 16. Consultar o funil por origem

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.query --name funil-origem
```

O resultado agrupa as sessões por origem e mostra quantas chegaram a cada etapa:

```text
page_view → view_product → add_to_cart → checkout → purchase
```

Observe se existe a origem `affiliate`. A campanha pode existir no JSON de marketing sem que os eventos tenham sido instrumentados com essa origem. Isso representa uma lacuna de rastreamento, não um valor que a Silver possa inventar.

## 17. Consultar entregas por transportadora

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.query --name entregas-transportadora
```

Compare:

- quantidade de entregas;
- percentual entregue no prazo;
- atraso médio;
- entregas ainda não concluídas.

Essa consulta usa dados aprovados da Silver e uma regra de negócio publicada na Gold.

### 17.1 Visualizar o DuckDB no navegador

O DuckDB possui uma interface web local. Ela permite explorar o Warehouse e
executar consultas SQL sem enviar os dados para um serviço externo.

Na primeira utilização, instale a extensão `ui`:

```powershell
python -c "import duckdb; c=duckdb.connect(r'data/warehouse/aurora.duckdb'); c.execute('INSTALL ui'); print('DuckDB UI instalada')"
```

Essa instalação precisa de acesso à internet e pode levar alguns instantes.
Não interrompa o comando enquanto a extensão estiver sendo baixada.

Depois, inicie o servidor local da interface:

```powershell
python -c "import duckdb,time; c=duckdb.connect(r'data/warehouse/aurora.duckdb'); c.execute('LOAD ui'); c.execute('CALL start_ui_server()'); print('Abra http://localhost:4213'); time.sleep(86400)"
```

Mantenha esse terminal aberto e acesse:

<http://localhost:4213>

No painel esquerdo, a estrutura esperada é:

```text
Attached databases
└── aurora
    ├── gold
    └── main
```

| Item | Significado |
| --- | --- |
| `aurora` | Arquivo `data/warehouse/aurora.duckdb` aberto pela interface |
| `gold` | Esquema com dimensões, fatos e marts construídos nesta aula |
| `main` | Esquema padrão do DuckDB |

#### Por que somente a Gold aparece como esquema?

Isso é intencional. A interface abriu o arquivo:

```text
data/warehouse/aurora.duckdb
```

Esse arquivo representa o **Data Warehouse**. Por isso, somente a Gold foi
materializada como tabelas internas do DuckDB.

As camadas anteriores continuam no Data Lake como arquivos:

```text
Landing      data/lake/landing/       formatos recebidos das fontes
Bronze       data/lake/bronze/        arquivos Parquet brutos + linhagem
Silver       data/lake/silver/        arquivos Parquet aprovados e tratados
Quarentena   data/lake/quarantine/    arquivos Parquet reprovados + motivos
Gold         data/warehouse/aurora.duckdb   tabelas, fatos, dimensões e marts
```

Portanto, Bronze e Silver não desapareceram. Elas apenas não foram registradas
como esquemas internos do Warehouse. O DuckDB consegue consultá-las diretamente
com `read_parquet`.

Consulte a Bronze de eventos:

```sql
SELECT *
FROM read_parquet(
    'data/lake/bronze/events/**/*.parquet',
    union_by_name = true
)
LIMIT 20;
```

Consulte a Silver de eventos:

```sql
SELECT *
FROM read_parquet(
    'data/lake/silver/events/**/*.parquet',
    union_by_name = true
)
LIMIT 20;
```

Consulte os eventos reprovados e seus motivos:

```sql
SELECT event_id, motivos, _source_file, quarantined_at
FROM read_parquet(
    'data/lake/quarantine/events/**/*.parquet',
    union_by_name = true
)
LIMIT 20;
```

Não é necessário entrar no MotherDuck. Clique no `+` ao lado de **Notebooks**
para criar uma consulta SQL local.

Liste os objetos da Gold:

```sql
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'gold'
ORDER BY table_name;
```

Consulte a receita por categoria e dia:

```sql
SELECT *
FROM gold.mart_receita_categoria_dia
ORDER BY receita DESC
LIMIT 20;
```

Para encerrar a interface, volte ao terminal que mantém o servidor e pressione
`Ctrl+C`.

Referência: [DuckDB UI — documentação oficial](https://duckdb.org/docs/current/core_extensions/ui).

---

# Fase 4 — Validar o pipeline completo

## 18. Executar todas as validações

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.validate --all
```

Ou execute a tarefa:

```text
88. Validar pipeline da Aula 5
```

Resultado esperado:

```text
[OK] Bronze preservou a quantidade de registros da Landing
[OK] Bronze = Silver + Quarentena
[OK] Silver não possui event_id duplicado
[OK] fato_vendas respeita o grão de item de pedido
[OK] chaves das dimensões não possuem duplicatas
[OK] fatos não possuem chaves órfãs
[OK] receita aprovada usa somente pedidos válidos

7 verificações aprovadas; 0 falhas
```

Uma execução com falha não deve ser considerada concluída, mesmo que os arquivos tenham sido produzidos.

## 19. Reexecutar o pipeline completo

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.pipeline --all
```

Ou execute a tarefa:

```text
89. Executar Aula 5 completa
```

A tarefa executa na ordem:

```text
Bronze
   ↓
Silver + Quarentena
   ↓
Gold
   ↓
Validações
```

Depois da segunda execução:

- a quantidade de objetos lógicos deve permanecer estável;
- a Silver deve continuar sem duplicatas;
- a fato de vendas deve continuar com uma linha por item;
- a receita aprovada deve permanecer igual;
- as validações devem continuar aprovadas.

Isso demonstra a idempotência das três novas fronteiras.

## 20. Publicar as camadas no SeaweedFS

Execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.publish
```

Ou execute a tarefa:

```text
91. Publicar camadas no SeaweedFS
```

Na primeira publicação do estado preparado, o resultado esperado é:

```json
{
  "bucket": "curso-bigdata",
  "layers": ["bronze", "silver", "quarantine"],
  "uploaded_objects": 59,
  "skipped_objects": 0
}
```

Repita a publicação. O resultado deve mostrar:

```json
{
  "uploaded_objects": 0,
  "skipped_objects": 59,
  "uploaded_bytes": 0
}
```

Agora abra o Filer:

<http://127.0.0.1:8888/buckets/curso-bigdata/>

O bucket deve conter `landing/`, `bronze/`, `silver/` e `quarantine/`. O `boto3` compara o SHA-256 antes do envio, usando a mesma estratégia de idempotência da Aula 4.

## 21. Conferir o caminho completo do dado

Escolha um `item_id` exibido pela consulta de vendas e execute:

```powershell
& ..\.venv\Scripts\python.exe -m bigdata_pipeline.transform.lineage --item-id 1
```

O resultado deve mostrar o caminho:

```text
Landing
  sqlite/order_items/...
       ↓
Bronze
  sqlite/order_items/....parquet
       ↓
Silver
  order_items
       ↓
Gold
  fato_vendas.item_id = 1
       ↓
Mart
  mart_receita_categoria_dia
```

Agora podemos responder não apenas “qual é a receita?”, mas também “de onde veio esse número?”.

---

## 22. Encerrar o laboratório

Ao final da aula:

1. confirme que a tarefa `88. Validar pipeline da Aula 5` terminou sem falhas;
2. preserve `data/warehouse/aurora.duckdb` para a próxima aula;
3. mantenha Bronze, Silver e Quarentena no SeaweedFS;
4. encerre o SeaweedFS com `Ctrl+C` no terminal em que ele está rodando.

O encerramento do processo não apaga os dados. Na próxima execução, o SeaweedFS utilizará o mesmo diretório físico.

---

## Resultado final

Ao concluir o laboratório, a plataforma evoluiu de um repositório de dados brutos para uma base analítica confiável:

```text
Fontes
   ↓
Landing             captura e preservação
   ↓
Bronze              Parquet e linhagem
   ↓
Silver              qualidade, tipos e padronização
   ├── Quarentena   rejeitados com motivo
   ↓
Gold                dimensões, fatos e métricas
   ↓
Próxima aula        dashboard, IA e API analítica
```

### Evidências que o aluno deve apresentar

- print da estrutura `bronze/`, `silver/` e `quarantine/` no Filer;
- relatório de qualidade com a reconciliação aprovada;
- validação do grão da `fato_vendas`;
- resultado de receita por categoria;
- saída final com todas as verificações aprovadas.

> **Mensagem de encerramento:** a Aula 4 garantiu que o dado chegasse. A Aula 5 garante que ele possa ser usado com confiança.

---

## Apêndice A — Recomeçar somente a Aula 5

Use este procedimento apenas quando for necessário repetir a demonstração desde a Bronze. A Landing da Aula 4 deve permanecer intacta.

Execute a tarefa:

```text
90. Zerar camadas da Aula 5
```

Ela remove somente:

```text
bronze/
silver/
quarantine/
data/warehouse/aurora.duckdb
```

Ela não remove:

```text
landing/
data/lake/control/
data/source/
```

Depois, execute novamente:

```text
89. Executar Aula 5 completa
```

## Apêndice B — Diagnóstico rápido

| Sintoma | Causa provável | Ação |
| --- | --- | --- |
| `Connection refused` na porta 8333 | SeaweedFS não iniciado | Execute `50. Iniciar SeaweedFS` |
| Bucket vazio | Aula 4 não foi sincronizada | Execute a sincronização da Landing da Aula 4 |
| `httpfs` não encontrado | Extensão não preparada | Instale ou copie a extensão antes da aula offline |
| Bronze sem arquivos | Não existem objetos em `landing/` | Confira o Filer e o bucket configurado |
| Reconciliação não fecha | Alguma regra perdeu ou duplicou registros | Interrompa antes de construir a Gold |
| Receita mudou após reexecução | Pipeline não idempotente ou fontes alteradas | Compare contagens e arquivos de origem |
| Warehouse bloqueado | Outro processo está usando o DuckDB | Feche consultas e aplicações conectadas ao arquivo |
