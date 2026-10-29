# Plano de Curso: Big Data com Google Colab

## Visão geral

Curso organizado em **8 semanas**, com uma aula de **3 horas por semana**. Cada aula utiliza um Google Colab independente, combinando conteúdo teórico, demonstração, laboratório guiado, exercícios progressivos e desafio prático.

Os notebooks não dependerão das aulas anteriores e não exigirão instalação no computador do aluno. Será necessário apenas um navegador, acesso à internet e uma conta Google para utilizar o Colab.

## Estrutura padrão de cada aula

| Etapa | Duração | Atividade |
|---|---:|---|
| Abertura | 15 min | Retomada da aula anterior e apresentação do problema da semana |
| Fundamentação | 35 min | Exposição dos conceitos teóricos |
| Demonstração | 20 min | Exemplo executado e comentado pelo professor |
| Laboratório | 70 min | Desenvolvimento guiado no Colab |
| Exercícios | 30 min | Continuação prática do laboratório |
| Encerramento | 10 min | Discussão dos resultados, revisão e orientações |

Cada notebook deverá conter:

1. Título e contexto da aula.
2. Objetivos de aprendizagem.
3. Situação-problema.
4. Conteúdo teórico em células Markdown.
5. Preparação automática do ambiente.
6. Demonstrações curtas e explicadas.
7. Laboratório guiado.
8. Exercícios de continuação.
9. Desafio com menos orientação.
10. Perguntas de reflexão e resumo.

---

## Semana 1 — Introdução ao Big Data

### Objetivos

- Compreender o conceito de Big Data.
- Reconhecer os 5 Vs: volume, velocidade, variedade, veracidade e valor.
- Diferenciar processamento tradicional de processamento distribuído.
- Identificar problemas de qualidade em conjuntos de dados.

### Conteúdo

- O que é Big Data e por que ele surgiu.
- Os 5 Vs e exemplos de aplicação.
- Sistemas transacionais e sistemas analíticos.
- Escalabilidade vertical e horizontal.
- Processamento em lote.
- Visão geral de clusters, data lakes e processamento distribuído.

### Laboratório guiado

Explorar um conjunto de dados de mobilidade urbana. Identificar colunas, tipos, quantidade de registros, valores ausentes, duplicidades e possíveis inconsistências. Aumentar artificialmente o volume dos dados e observar o crescimento do uso de memória e do tempo de processamento.

### Exercícios de continuação

1. Relacionar características do conjunto de dados aos 5 Vs.
2. Calcular percentuais de valores ausentes por coluna.
3. Localizar registros duplicados e valores fora do padrão.
4. Criar versões maiores do conjunto de dados e comparar os tempos de execução.
5. Explicar em que momento uma solução distribuída poderia ser necessária.

### Entrega da semana

Diagnóstico do conjunto de dados e proposta simples de arquitetura para armazená-lo e processá-lo.

---

## Semana 2 — Formatos e armazenamento de dados

### Objetivos

- Conhecer as diferenças entre CSV, JSON e Parquet.
- Entender schema, compressão, armazenamento colunar e particionamento.
- Avaliar como o formato influencia tamanho e velocidade de leitura.

### Conteúdo

- Dados estruturados e semiestruturados.
- Formatos CSV, JSON e Parquet.
- Schema explícito e inferência de tipos.
- Armazenamento orientado a linhas e colunas.
- Compressão e seleção de colunas.
- Particionamento de arquivos.
- Data warehouse, data lake e lakehouse.

### Laboratório guiado

Carregar dados de vendas em CSV, convertê-los para JSON e Parquet e comparar tamanho, tempo de leitura, tipos preservados e facilidade de consulta.

### Exercícios de continuação

1. Ler somente um subconjunto de colunas.
2. Comparar o tempo da leitura completa com o da leitura seletiva.
3. Aplicar diferentes opções de compressão.
4. Particionar os dados por ano, estado ou região.
5. Executar filtros sobre os dados particionados.
6. Recomendar o formato mais adequado para três cenários propostos.

### Entrega da semana

Tabela comparativa dos formatos e recomendação técnica justificada.

---

## Semana 3 — Primeiros passos com PySpark

### Objetivos

- Compreender os componentes básicos do Apache Spark.
- Criar uma sessão Spark no Google Colab.
- Manipular DataFrames com a API do PySpark.
- Utilizar schemas, filtros, colunas calculadas e agregações.

### Conteúdo

- Visão geral da arquitetura do Spark.
- Driver, executores e sessão Spark.
- DataFrames distribuídos.
- Schemas e tipos de dados.
- Transformações e ações.
- Seleção, filtros, ordenação e agregação.

### Laboratório guiado

Analisar um conjunto de avaliações de filmes. Criar o DataFrame, inspecionar o schema, limpar registros inválidos e calcular quantidade de avaliações e nota média por filme.

### Exercícios de continuação

1. Considerar apenas filmes com uma quantidade mínima de avaliações.
2. Criar rankings separados por gênero.
3. Comparar avaliações por período.
4. Identificar usuários com padrões incomuns de avaliação.
5. Criar um indicador que combine média e popularidade.
6. Explicar por que utilizar apenas a média pode produzir resultados enganosos.

### Entrega da semana

Ranking comentado dos filmes e documentação das regras adotadas.

---

## Semana 4 — Processamento distribuído

### Objetivos

- Entender como o Spark planeja e executa operações.
- Compreender lazy evaluation, jobs, stages, tasks e partições.
- Reconhecer operações que provocam shuffle.
- Interpretar planos de execução.

### Conteúdo

- Avaliação preguiçosa.
- DAG de execução.
- Jobs, stages e tasks.
- Partições e paralelismo.
- Operações narrow e wide.
- Shuffle e movimentação de dados.
- Planos lógico e físico.
- Uso de `explain()`.

### Laboratório guiado

Processar registros de voos, calcular atrasos e observar como filtros, agrupamentos e ordenações alteram o plano de execução.

### Exercícios de continuação

1. Identificar as operações que provocam shuffle.
2. Alterar o número de partições e observar o resultado.
3. Comparar dois planos que produzem o mesmo indicador.
4. Localizar rotas e companhias com maior incidência de atrasos.
5. Calcular atrasos por aeroporto e período.
6. Explicar por que determinadas consultas apresentam maior custo.

### Entrega da semana

Análise de execução apoiada nos planos gerados pelo Spark.

---

## Semana 5 — Spark SQL e análises avançadas

### Objetivos

- Consultar DataFrames por meio de SQL.
- Combinar diferentes conjuntos de dados.
- Aplicar agregações e funções de janela.
- Traduzir perguntas de negócio em consultas.

### Conteúdo

- Views temporárias.
- Spark SQL.
- Tipos de join.
- Agregações por grupo.
- Funções de janela.
- Rankings, acumulados e médias móveis.
- Duplicidades provocadas por joins.

### Laboratório guiado

Cruzar dados de clientes, pedidos, produtos e pagamentos de um comércio eletrônico para produzir indicadores de vendas.

### Exercícios de continuação

1. Calcular ticket médio por região.
2. Identificar clientes recorrentes.
3. Criar ranking de produtos por categoria.
4. Encontrar produtos sem vendas e pedidos sem pagamento.
5. Calcular participação acumulada das categorias no faturamento.
6. Resolver uma análise em SQL e em DataFrames e comparar as abordagens.

### Entrega da semana

Conjunto de consultas acompanhado de pelo menos cinco conclusões de negócio.

---

## Semana 6 — Pipeline ETL e qualidade de dados

### Objetivos

- Construir um fluxo reproduzível de ingestão, limpeza e transformação.
- Criar regras de qualidade de dados.
- Separar registros válidos de registros rejeitados.
- Organizar dados em camadas.

### Conteúdo

- ETL e ELT.
- Camadas bruta, tratada e analítica.
- Valores ausentes, duplicidades e inconsistências.
- Padronização de datas e categorias.
- Regras de validação.
- Registros rejeitados e rastreabilidade.
- Escrita de dados tratados em Parquet.

### Laboratório guiado

Tratar dados públicos de saúde ou educação contendo datas inválidas, categorias inconsistentes, registros repetidos e campos ausentes.

### Exercícios de continuação

1. Definir regras obrigatórias e limites aceitáveis.
2. Criar uma coluna com o motivo da rejeição.
3. Separar registros válidos e inválidos.
4. Padronizar categorias e datas.
5. Remover duplicidades com uma regra de prioridade.
6. Criar indicadores a partir da camada tratada.
7. Salvar resultados e gerar um relatório de qualidade.

### Entrega da semana

Pipeline executável do início ao fim e relatório dos problemas encontrados.

---

## Semana 7 — Desempenho e otimização

### Objetivos

- Identificar causas comuns de lentidão no Spark.
- Medir o efeito de diferentes estratégias de otimização.
- Utilizar cache, particionamento e broadcast join conscientemente.
- Relacionar alterações no código ao plano de execução.

### Conteúdo

- Particionamento inadequado.
- Shuffle e custo de rede.
- Cache e persistência.
- Broadcast join.
- Data skew.
- Projeção de colunas e aplicação antecipada de filtros.
- Problema dos arquivos pequenos.
- Medição e comparação de desempenho.

### Laboratório guiado

Executar uma pipeline propositalmente ineficiente sobre dados gerados no próprio Colab. Medir o tempo inicial, analisar o plano e aplicar otimizações progressivas.

### Exercícios de continuação

1. Remover colunas e operações desnecessárias.
2. Antecipar filtros e comparar o plano.
3. Testar cache em uma operação reutilizada.
4. Comparar join comum e broadcast join.
5. Alterar o número de partições.
6. Simular uma chave com distribuição desigual.
7. Registrar tempo e plano antes e depois das alterações.

### Entrega da semana

Relatório de otimização mostrando as mudanças, o ganho observado e a explicação técnica.

---

## Semana 8 — Projeto aplicado

### Objetivos

- Integrar os conceitos trabalhados durante o curso.
- Resolver um problema novo com menor orientação.
- Justificar decisões de armazenamento, transformação e análise.
- Comunicar resultados técnicos e conclusões sobre os dados.

### Proposta

Analisar dados ambientais, financeiros ou urbanos fornecidos pelo próprio notebook. O tema será diferente dos laboratórios anteriores, mas todas as ferramentas necessárias já terão sido praticadas.

### Etapas do projeto

1. Compreender o problema e formular perguntas de análise.
2. Explorar o conjunto de dados e seu schema.
3. Identificar e tratar problemas de qualidade.
4. Criar uma camada de dados tratados.
5. Salvar os dados em Parquet.
6. Produzir indicadores com PySpark e Spark SQL.
7. Utilizar joins, agregações ou funções de janela.
8. Examinar o plano de uma operação relevante.
9. Aplicar pelo menos uma otimização.
10. Apresentar conclusões, limitações e possíveis melhorias.

### Entrega da semana

Colab completamente executado, com código organizado, respostas em Markdown, resultados interpretados e pelo menos cinco descobertas sobre os dados.

---

## Avaliação sugerida

| Componente | Peso |
|---|---:|
| Exercícios semanais | 35% |
| Desafios semanais | 25% |
| Projeto aplicado | 40% |

### Critérios de avaliação

- Execução correta do notebook.
- Qualidade e organização do código.
- Interpretação dos resultados.
- Justificativa das decisões técnicas.
- Clareza das respostas escritas.
- Capacidade de relacionar teoria e prática.

## Independência dos Colabs

Cada notebook deverá:

- instalar automaticamente as dependências necessárias;
- baixar ou gerar seu próprio conjunto de dados;
- funcionar sem resultados de aulas anteriores;
- não exigir instalação local de Python, Java, Spark ou banco de dados;
- não depender da montagem do Google Drive;
- não exigir senha, cartão, API ou serviço externo autenticado;
- fixar versões importantes das bibliotecas;
- possuir dados alternativos gerados localmente caso a fonte externa falhe;
- reconstruir todo o ambiente ao selecionar **Executar tudo**.

Uma célula inicial poderá preparar silenciosamente o ambiente do Colab:

```python
!pip install -q pyspark pyarrow
```

A instalação ocorrerá somente na máquina temporária do Colab. Nada será instalado no computador do aluno.

## Preparação do professor

Antes de cada aula:

1. Abrir uma sessão nova do Colab.
2. Executar o notebook completo usando **Executar tudo**.
3. Confirmar a instalação das dependências.
4. Verificar se os dados ainda estão acessíveis.
5. Conferir tempos de execução e consumo de memória.
6. Manter uma versão do aluno e outra com soluções.
7. Preparar exemplos de respostas esperadas para as questões abertas.
8. Definir até onde o laboratório deverá avançar durante a aula.

## Organização dos materiais

Sugestão de nomes para os notebooks:

```text
01_introducao_big_data.ipynb
02_formatos_armazenamento.ipynb
03_pyspark_dataframes.ipynb
04_processamento_distribuido.ipynb
05_spark_sql_analises.ipynb
06_etl_qualidade.ipynb
07_otimizacao_spark.ipynb
08_projeto_aplicado.ipynb
```

Para cada aula, manter:

- uma versão para os alunos, com exercícios parcialmente preenchidos;
- uma versão do professor, com soluções e observações didáticas;
- os links das fontes de dados;
- uma cópia pequena ou um gerador de dados para contingência.
