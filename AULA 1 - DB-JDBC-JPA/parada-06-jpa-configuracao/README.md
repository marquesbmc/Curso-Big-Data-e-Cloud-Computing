# Parada 6 — Como a JPA encontra o mesmo banco SQLite?

## 1. O problema

Queremos buscar um `Livro` como entidade, mas a abstração precisa saber qual provedor usar, quais classes gerenciar e como chegar ao banco existente.

## 2. Objetivo

Ao concluir, você deverá diferenciar Jakarta Persistence de Hibernate, localizar driver, URL e dialeto e explicar os ciclos de vida de factory e manager.

## 3. Arquivos principais

1. [`persistence.xml`](src/main/resources/META-INF/persistence.xml)
2. [`JPAUtil.java`](src/main/java/br/edu/ibmec/livraria/JPAUtil.java)
3. [`Livro.java`](src/main/java/br/edu/ibmec/livraria/Livro.java)
4. [`Aplicacao.java`](src/main/java/br/edu/ibmec/livraria/Aplicacao.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-06-jpa-configuracao`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-06-jpa-configuracao'
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

- JPA é a especificação; Hibernate é o provedor;
- JDBC continua presente na configuração por meio do driver e da URL;
- a unidade `livraria` reúne entidades e propriedades;
- `EntityManagerFactory` é cara e reutilizada; `EntityManager` é curto;
- `find(Livro.class, id)` busca pela chave e devolve `null` quando não encontra.

## 6. Experimento

Troque o segundo `find` de `999L` para `2L` e compare o SQL e o objeto devolvido.

## 7. Resultado esperado

O Hibernate exibe o `SELECT`; o primeiro livro é materializado como entidade e a identidade ausente produz `null`.

## 8. Pergunta de verificação

<details>
<summary>Se usamos JPA, por que o `persistence.xml` ainda contém JDBC?</summary>

Porque o provedor implementa a abstração, mas normalmente usa JDBC e o driver para conversar com o banco.
</details>

## 9. Transição

Já carregamos uma entidade. A próxima parada mostra como o contexto acompanha `Livro` durante todo o CRUD.
