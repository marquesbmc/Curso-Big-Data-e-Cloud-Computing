# Parada 4 — Como organizar o CRUD sem expor JDBC à aplicação?

## 1. O problema

A aplicação precisa inserir, buscar, listar, atualizar e excluir livros. Se cada fluxo conhecer SQL e recursos JDBC, as responsabilidades se misturam e a repetição cresce.

## 2. Objetivo

Ao concluir, você deverá explicar a responsabilidade do DAO, reconhecer o CRUD e interpretar ausência e quantidade de linhas afetadas.

## 3. Arquivos principais

1. [`LivroDAO.java`](src/main/java/br/edu/ibmec/livraria/LivroDAO.java)
2. [`LivroMapper.java`](src/main/java/br/edu/ibmec/livraria/LivroMapper.java)
3. [`Aplicacao.java`](src/main/java/br/edu/ibmec/livraria/Aplicacao.java)
4. [`LivroDAOTest.java`](src/test/java/br/edu/ibmec/livraria/LivroDAOTest.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-04-dao-crud`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-04-dao-crud'
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

- `LivroDAO` recebe `ConnectionFactory` por construtor;
- cada método abre e fecha sua própria conexão nesta parada;
- `preencherDadosDoLivro` e `buscarLista` são helpers internos;
- `UPDATE` e `DELETE` devolvem `true` apenas quando uma linha foi afetada;
- a busca posterior ao `DELETE` devolve `Optional.empty()`.

## 6. Experimento

Depois da exclusão, chame `dao.excluir(inserido.id())` pela segunda vez e identifique o retorno.

## 7. Resultado esperado

O primeiro ciclo executa Create, Read, Update e Delete. A segunda exclusão devolve `false`, pois já não há linha com aquele ID.

## 8. Pergunta de verificação

<details>
<summary>Por que o DAO recebe uma factory, em vez de manter uma `Connection` aberta?</summary>

Porque a conexão é um recurso temporário. A factory torna a dependência explícita e cada operação controla o próprio fechamento nesta etapa.
</details>

## 9. Transição

Uma operação isolada cabe em um método do DAO. Uma venda, porém, combina várias escritas que precisam compartilhar a mesma transação.
