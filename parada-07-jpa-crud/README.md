# Parada 7 — O que acontece com uma entidade durante o CRUD?

## 1. O problema

Na JPA, chamar um método sobre um objeto pode gerar SQL depois. Para prever esse comportamento, precisamos saber se a entidade é nova, gerenciada, destacada ou removida.

## 2. Objetivo

Ao concluir, você deverá observar os quatro estados, usar `persist`, `find`, `clear`, `contains` e `remove`, e relacionar dirty checking ao `UPDATE`.

## 3. Arquivos principais

1. [`Livro.java`](src/main/java/br/edu/ibmec/livraria/Livro.java)
2. [`Aplicacao.java`](src/main/java/br/edu/ibmec/livraria/Aplicacao.java)
3. [`JPACrudTest.java`](src/test/java/br/edu/ibmec/livraria/JPACrudTest.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-07-jpa-crud`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-07-jpa-crud'
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

## 5. O que observar

- antes de `persist`, ID é `null` e `contains` é `false`;
- depois de `persist`, `Livro` está gerenciado;
- `clear()` destaca as entidades sem excluir linhas;
- `find()` devolve outra instância gerenciada;
- alterar essa instância produz `UPDATE` por dirty checking;
- escrita exige `EntityTransaction`; `remove` agenda o `DELETE`.

## 6. Experimento

Mova `encontrado.atualizar(...)` para depois de um `entityManager.clear()` e não faça outra busca. Execute e confira se há `UPDATE`.

## 7. Resultado esperado

No fluxo original aparecem `INSERT`, `SELECT`, `UPDATE` e `DELETE`. No experimento, a alteração da instância destacada não é sincronizada automaticamente.

## 8. Pergunta de verificação

<details>
<summary>Por que não existe `entityManager.update()`?</summary>

Porque o contexto detecta mudanças em entidades gerenciadas e gera o `UPDATE` na sincronização.
</details>

## 9. Transição

Até aqui `Livro` guarda apenas `autorId`. Agora substituiremos essa chave por uma associação navegável com `Autor`.
