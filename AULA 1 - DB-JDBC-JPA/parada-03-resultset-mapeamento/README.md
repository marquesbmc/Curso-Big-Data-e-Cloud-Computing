# Parada 3 — Como transformar linhas do banco em objetos `Livro`?

## 1. O problema

Uma consulta JDBC devolve um cursor, não uma coleção de objetos. Repetir a leitura de `id`, `titulo`, `preco` e estoque em toda consulta espalharia a mesma conversão pelo código.

## 2. Objetivo

Ao concluir, você deverá movimentar o cursor com `next()`, distinguir `if` de `while`, mapear preços com `BigDecimal` e escolher `Optional` ou `List` conforme a cardinalidade.

## 3. Arquivos principais

1. [`Livro.java`](src/main/java/br/edu/ibmec/livraria/Livro.java)
2. [`LivroMapper.java`](src/main/java/br/edu/ibmec/livraria/LivroMapper.java)
3. [`ConsultaLivro.java`](src/main/java/br/edu/ibmec/livraria/ConsultaLivro.java)
4. [`ConsultaLivroTest.java`](src/test/java/br/edu/ibmec/livraria/ConsultaLivroTest.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-03-resultset-mapeamento`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-03-resultset-mapeamento'
$Java = (Resolve-Path '.\.tools\jdk-17.0.20+8\bin\java.exe').Path
$Javac = (Resolve-Path '.\.tools\jdk-17.0.20+8\bin\javac.exe').Path
$Sqlite = (Resolve-Path '.\.lib\sqlite-jdbc-3.46.1.3.jar').Path

New-Item -ItemType Directory -Force "$Modulo\target\classes" | Out-Null
& $Javac -cp $Sqlite -d "$Modulo\target\classes" `
    (Get-ChildItem "$Modulo\src\main\java" -Recurse -Filter '*.java').FullName

Push-Location $Modulo
& $Java -cp "target\classes;$Sqlite" br.edu.ibmec.livraria.Aplicacao
Pop-Location
```

## 5. O que observar

- o cursor nasce antes da primeira linha;
- `if (next())` atende uma busca de zero ou um resultado;
- `while (next())` percorre todos os resultados;
- o Mapper lê pelo nome da coluna, mas não chama `next()` nem fecha o cursor;
- ausência vira `Optional.empty()` ou lista vazia, nunca `null`.

## 6. Experimento

Troque o ID inexistente `999` por outro ID válido. Depois busque por uma parte de título que não exista.

## 7. Resultado esperado

O primeiro resultado muda de `Optional.empty` para um `Livro`. A segunda busca devolve `[]`, mostrando que uma listagem vazia continua sendo um resultado válido.

## 8. Pergunta de verificação

<details>
<summary>Por que o Mapper não chama `resultSet.next()`?</summary>

Porque mover o cursor pertence ao controle da consulta. O Mapper tem uma responsabilidade menor: converter somente a linha atual.
</details>

## 9. Transição

O mapeamento ficou reutilizável, mas SQL, conexão e operações ainda estão espalhados. O DAO reunirá o CRUD em uma única abstração.
