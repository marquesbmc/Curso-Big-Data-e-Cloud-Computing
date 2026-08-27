# Parada 1 — Como abrir o banco da livraria com segurança?

## 1. O problema

Os livros já estão em `livraria.db`, mas a aplicação precisa localizar esse arquivo, escolher o driver correto e liberar a sessão mesmo quando algo falha.

## 2. Objetivo

Ao concluir, você deverá reconhecer a URL JDBC, explicar o papel de `DriverManager` e identificar quem fecha a `Connection`.

## 3. Arquivos principais

1. [`ConnectionFactory.java`](src/main/java/br/edu/ibmec/livraria/ConnectionFactory.java)
2. [`Aplicacao.java`](src/main/java/br/edu/ibmec/livraria/Aplicacao.java)
3. [`ConnectionFactoryTest.java`](src/test/java/br/edu/ibmec/livraria/ConnectionFactoryTest.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-01-conexao`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-01-conexao'
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

Consulte o [README principal](../README.md#executar-os-testes-pelo-pacote-local) para compilar e executar os testes.

## 5. O que observar

- `jdbc:sqlite:` permite ao `DriverManager` escolher o driver;
- o arquivo é validado antes da conexão, evitando um SQLite vazio por engano;
- o driver é descoberto automaticamente, sem `Class.forName`;
- a factory devolve a conexão; o `try-with-resources` de quem a usa executa `close()`.

## 6. Experimento

Execute com um arquivo inexistente, sem editar o código:

```powershell
Push-Location $Modulo
& $Java -Dlivraria.db=ausente.db -cp "target\classes;$Sqlite" br.edu.ibmec.livraria.Aplicacao
Pop-Location
```

## 7. Resultado esperado

A execução normal mostra conexão aberta, driver, URL e fechamento. O experimento informa o caminho absoluto que não foi encontrado e não cria `ausente.db`.

## 8. Pergunta de verificação

<details>
<summary>Por que a factory não fecha a conexão que acabou de criar?</summary>

Porque ela transfere o uso da `Connection` ao chamador. Quem controla o período de uso também deve fechá-la, neste caso com `try-with-resources`.
</details>

## 9. Transição

A sessão está aberta. Agora precisamos enviar consultas e inserções sem misturar valores recebidos com o texto SQL.
