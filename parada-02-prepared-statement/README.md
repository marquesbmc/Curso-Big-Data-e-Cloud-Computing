# Parada 2 — Como enviar valores sem montar SQL por concatenação?

## 1. O problema

A livraria precisa buscar títulos e cadastrar livros. Inserir IDs, títulos e preços diretamente no texto SQL mistura comando e dado, dificulta o tratamento de tipos e abre espaço para SQL Injection.

## 2. Objetivo

Ao concluir, você deverá preencher marcadores `?` com setters tipados, escolher entre `executeQuery` e `executeUpdate` e recuperar a identidade gerada.

## 3. Arquivos principais

1. [`ConsultaLivro.java`](src/main/java/br/edu/ibmec/livraria/ConsultaLivro.java)
2. [`CadastroLivro.java`](src/main/java/br/edu/ibmec/livraria/CadastroLivro.java)
3. [`Aplicacao.java`](src/main/java/br/edu/ibmec/livraria/Aplicacao.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-02-prepared-statement`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-02-prepared-statement'
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

A aplicação insere um registro. Antes de repetir, restaure o banco conforme o [README principal](../README.md#restaurar-os-bancos).

## 5. O que observar

- o SQL é fixo e os valores ocupam marcadores `?` numerados a partir de `1`;
- `%` faz parte do valor usado no `LIKE`;
- `executeQuery()` devolve `ResultSet`; `executeUpdate()` devolve linhas afetadas;
- `Statement.RETURN_GENERATED_KEYS` e `getGeneratedKeys()` recuperam o ID criado.

## 6. Experimento

Troque temporariamente a busca por `"Casa"` para `"Areia"`. Depois remova o `statement.setLong(5, autorId)` do cadastro, execute e restaure a linha.

## 7. Resultado esperado

A primeira mudança altera a lista sem mudar o SQL. Sem o quinto setter, o comando fica incompleto e falha; o tratamento preserva a `SQLException` como causa.

## 8. Pergunta de verificação

<details>
<summary>Por que os índices começam em 1?</summary>

Essa é a convenção da API JDBC para parâmetros e colunas. O primeiro `?` recebe o índice `1`.
</details>

## 9. Transição

Já conseguimos obter linhas. Na próxima parada, elas deixam de virar textos improvisados e passam a produzir objetos `Livro`.
