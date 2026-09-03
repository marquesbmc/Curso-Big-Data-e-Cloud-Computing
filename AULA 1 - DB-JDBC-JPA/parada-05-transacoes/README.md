# Parada 5 — Como impedir uma venda pela metade?

## 1. O problema

Registrar uma venda exige criar `venda`, criar `item_venda` e reduzir o estoque. Confirmar apenas parte desses comandos deixaria o banco incoerente.

## 2. Objetivo

Ao concluir, você deverá delimitar uma transação com a mesma `Connection`, explicar `commit` e `rollback` e reconhecer a ordem de inserção entre venda e item.

## 3. Arquivos principais

1. [`VendaService.java`](src/main/java/br/edu/ibmec/livraria/VendaService.java)
2. [`Venda.java`](src/main/java/br/edu/ibmec/livraria/Venda.java)
3. [`ItemVenda.java`](src/main/java/br/edu/ibmec/livraria/ItemVenda.java)
4. [`Aplicacao.java`](src/main/java/br/edu/ibmec/livraria/Aplicacao.java)
5. [`VendaServiceTest.java`](src/test/java/br/edu/ibmec/livraria/VendaServiceTest.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-05-transacoes`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-05-transacoes'
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

Restaure o banco antes de repetir a venda; veja o [README principal](../README.md#restaurar-os-bancos).

## 5. O que observar

- `setAutoCommit(false)` coloca a confirmação sob controle da aplicação;
- todos os helpers recebem a mesma `Connection`;
- `venda` vem antes de `item_venda`, que precisa de `venda_id`;
- a falha executa `rollback()` e o `finally` restaura o auto-commit original;
- atomicidade garante tudo ou nada, mas não resolve sozinha duas vendas concorrentes.

## 6. Experimento

Altere temporariamente a quantidade da primeira venda de `2` para `10_000` e compare estoque e registros antes e depois.

## 7. Resultado esperado

A venda válida confirma as duas inserções e a baixa de estoque. A inválida não altera nenhuma das três partes.

## 8. Pergunta de verificação

<details>
<summary>Por que abrir uma conexão em cada helper quebraria a atomicidade?</summary>

Porque `commit` e `rollback` atuam sobre os comandos da mesma conexão. Outra conexão criaria outra fronteira transacional.
</details>

## 9. Transição

O JDBC exigiu SQL, chaves e sincronização manual. Agora veremos a JPA acessar o mesmo banco e assumir parte desse trabalho.

> **Aprofundamento — `Savepoint`:** `demonstrarSavepoint()` apresenta rollback parcial em um exemplo separado. Use-o depois de dominar o rollback total da venda.
