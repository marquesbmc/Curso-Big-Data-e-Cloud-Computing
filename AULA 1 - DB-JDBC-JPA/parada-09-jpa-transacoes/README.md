# Parada 9 — Como confirmar ou desfazer uma venda JPA completa?

## 1. O problema

Uma venda cria `Venda` e `ItemVenda` e reduz o estoque de um `Livro`. O grafo em memória e as linhas do banco precisam terminar juntos em commit ou rollback.

## 2. Objetivo

Ao concluir, você deverá explicar unidade de trabalho, cascade, dirty checking, conversão de data e por que `flush` ainda permite rollback.

## 3. Arquivos principais

1. [`VendaService.java`](src/main/java/br/edu/ibmec/livraria/VendaService.java)
2. [`Venda.java`](src/main/java/br/edu/ibmec/livraria/Venda.java)
3. [`ItemVenda.java`](src/main/java/br/edu/ibmec/livraria/ItemVenda.java)
4. [`Livro.java`](src/main/java/br/edu/ibmec/livraria/Livro.java)
5. [`LocalDateTimeStringConverter.java`](src/main/java/br/edu/ibmec/livraria/LocalDateTimeStringConverter.java)
6. [`JPATransacoesTest.java`](src/test/java/br/edu/ibmec/livraria/JPATransacoesTest.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-09-jpa-transacoes`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-09-jpa-transacoes'
$Java = (Resolve-Path '.\.tools\jdk-17.0.20+8\bin\java.exe').Path
$Javac = (Resolve-Path '.\.tools\jdk-17.0.20+8\bin\javac.exe').Path
$Jpa = (Resolve-Path '.\.lib\jpa').Path + '\*'

New-Item -ItemType Directory -Force "$Modulo\target\classes" | Out-Null
& $Javac -cp $Jpa -d "$Modulo\target\classes" `
    (Get-ChildItem "$Modulo\src\main\java" -Recurse -Filter '*.java').FullName

Push-Location $Modulo
& $Java -cp "target\classes;src\main\resources;$Jpa" br.edu.ibmec.livraria.Aplicacao
Pop-Location
```

Restaure o banco antes de repetir; veja o [README principal](../README.md#restaurar-os-bancos).

## 5. O que observar

- `EntityTransaction` delimita toda a unidade de trabalho;
- `Livro` veio de `find`, já está gerenciado e protege sua regra de estoque;
- `Venda.adicionarItem` mantém venda e item coerentes nos dois lados;
- somente `Venda` recebe `persist`; cascade alcança o novo `ItemVenda`;
- dirty checking produz o `UPDATE` de estoque;
- o converter adapta `LocalDateTime` à coluna `TEXT`;
- `flush()` envia SQL, mas somente `commit()` confirma; a falha seguinte ainda executa rollback.

## 6. Experimento

Remova temporariamente o `entityManager.flush()` da demonstração de rollback e compare o SQL exibido. Depois restaure a chamada.

## 7. Resultado esperado

No commit, venda e item recebem IDs e o estoque diminui. No caminho simulado, com ou sem SQL antecipado por `flush`, venda, item e estoque permanecem como antes da tentativa.

## 8. Pergunta de verificação

<details>
<summary>Por que `Livro` não recebe `persist` e mesmo assim gera `UPDATE`?</summary>

Porque veio de `find` e já está gerenciado. A mudança feita por `retirarDoEstoque` é detectada pelo dirty checking.
</details>

## 9. Transição

O percurso termina com a mesma regra que estudamos em JDBC, agora expressa como uma unidade de trabalho sobre entidades e relacionamentos.

## Desafio opcional — duas vendas da última unidade

O fluxo principal ensina atomicidade; concorrência e isolamento são problemas adicionais. Como extensão:

1. adicione um atributo `@Version` a `Livro`;
2. acrescente a coluna correspondente ao esquema de uma cópia do banco;
3. abra dois `EntityManager` e faça ambos lerem a última unidade;
4. tente confirmar as duas vendas;
5. observe a exceção de bloqueio otimista na segunda confirmação.

Faça o desafio em uma cópia do módulo. Não adicione apenas a anotação: sem adaptar a tabela, o mapeamento não corresponde ao banco existente.
