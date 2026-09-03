# Livraria JDBC e JPA

Projeto didático incremental com Java 17, SQLite, JDBC, Jakarta Persistence e Hibernate. O percurso acompanha uma única narrativa: conectar ao banco da livraria, enviar comandos seguros, transformar linhas em objetos, organizar um DAO, registrar uma venda transacional e observar como a JPA abstrai parte desse trabalho.

O material completo está em [`JDBC_JPA_Material_Estudo.md`](JDBC_JPA_Material_Estudo.md).

## Percurso em nove paradas

| Aula | Parada | Problema resolvido |
|---|---|---|
| 1 | [1 — conexão JDBC](parada-01-conexao/README.md) | abrir e fechar uma sessão com o SQLite |
| 1 | [2 — `PreparedStatement`](parada-02-prepared-statement/README.md) | enviar SQL e valores separadamente |
| 1 | [3 — `ResultSet` e Mapper](parada-03-resultset-mapeamento/README.md) | transformar linhas em objetos `Livro` |
| 1 | [4 — DAO e CRUD](parada-04-dao-crud/README.md) | concentrar as operações de persistência |
| 2 | [5 — transações JDBC](parada-05-transacoes/README.md) | confirmar ou desfazer uma venda completa |
| 2 | [6 — configuração JPA](parada-06-jpa-configuracao/README.md) | acessar o mesmo banco por entidades |
| 2 | [7 — CRUD e ciclo de vida JPA](parada-07-jpa-crud/README.md) | acompanhar estados e mudanças de `Livro` |
| 3 | [8 — relacionamentos JPA](parada-08-jpa-relacionamentos/README.md) | navegar entre `Autor` e `Livro` |
| 3 | [9 — transação JPA completa](parada-09-jpa-transacoes/README.md) | combinar cascade, dirty checking e rollback |

Cada pasta `parada-*` é um módulo independente, com código, testes e seu próprio `livraria.db`. Você pode começar por qualquer parada; não use classes compiladas de outra pasta.

## Pré-requisitos

- PowerShell;
- Java 17, já incluído no pacote completo em `.tools`.

As aplicações não criam tabelas, migrations nem dados iniciais. O driver SQLite é descoberto automaticamente pelo mecanismo Java Service Provider; não há `Class.forName`.

## Baixar o projeto

- [Repositório no GitHub](https://github.com/marquesbmc/JDBC-JPA-DB)
- [Slides da aula](https://github.com/marquesbmc/JDBC-JPA-DB/releases/download/v1.0.0/JDBC_JPA_Apresentacao.pptx)
- [Pacote completo](https://github.com/marquesbmc/JDBC-JPA-DB/releases/download/v1.0.0/JDBC-JPA-DB-completo-v1.0.0.zip)

Depois de baixar ou clonar, abra o PowerShell na raiz, onde estão `.tools`, `.lib` e as nove pastas.

## Execução com Java e JARs locais

Este é o único caminho de execução utilizado no percurso e funciona nas nove paradas sem baixar dependências. Defina primeiro os atalhos abaixo:

```powershell
$Java = (Resolve-Path '.\.tools\jdk-17.0.20+8\bin\java.exe').Path
$Javac = (Resolve-Path '.\.tools\jdk-17.0.20+8\bin\javac.exe').Path
$Sqlite = (Resolve-Path '.\.lib\sqlite-jdbc-3.46.1.3.jar').Path
$Junit = (Resolve-Path '.\.lib\junit-platform-console-standalone-1.11.0.jar').Path
$Jpa = (Resolve-Path '.\.lib\jpa').Path + '\*'
```

### Paradas 1–5 — JDBC

Escolha um módulo e compile a aplicação:

```powershell
$Modulo = 'parada-03-resultset-mapeamento' # troque por uma parada de 1 a 5
New-Item -ItemType Directory -Force "$Modulo\target\classes" | Out-Null
& $Javac -cp $Sqlite -d "$Modulo\target\classes" `
    (Get-ChildItem "$Modulo\src\main\java" -Recurse -Filter '*.java').FullName
```

Execute a partir da pasta da parada, pois `livraria.db` é um caminho relativo:

```powershell
Push-Location $Modulo
& $Java -cp "target\classes;$Sqlite" br.edu.ibmec.livraria.Aplicacao
Pop-Location
```

### Paradas 6–9 — JPA

```powershell
$Modulo = 'parada-08-jpa-relacionamentos' # troque por uma parada de 6 a 9
New-Item -ItemType Directory -Force "$Modulo\target\classes" | Out-Null
& $Javac -cp $Jpa -d "$Modulo\target\classes" `
    (Get-ChildItem "$Modulo\src\main\java" -Recurse -Filter '*.java').FullName

Push-Location $Modulo
& $Java -cp "target\classes;src\main\resources;$Jpa" br.edu.ibmec.livraria.Aplicacao
Pop-Location
```

O `persistence.xml` das paradas JPA mantém JDBC visível: ele informa driver, URL e dialeto SQLite ao Hibernate.

## Executar os testes pelo pacote local

Compile primeiro a aplicação da parada com um dos blocos anteriores. Para JDBC:

```powershell
New-Item -ItemType Directory -Force "$Modulo\target\test-classes" | Out-Null
& $Javac -cp "$Modulo\target\classes;$Sqlite;$Junit" `
    -d "$Modulo\target\test-classes" `
    (Get-ChildItem "$Modulo\src\test\java" -Recurse -Filter '*.java').FullName

Push-Location $Modulo
& $Java -cp "target\classes;target\test-classes;$Sqlite;$Junit" `
    org.junit.platform.console.ConsoleLauncher execute --scan-class-path
Pop-Location
```

Para JPA, troque apenas os classpaths de compilação e execução:

```powershell
New-Item -ItemType Directory -Force "$Modulo\target\test-classes" | Out-Null
& $Javac -cp "$Modulo\target\classes;$Jpa;$Junit" `
    -d "$Modulo\target\test-classes" `
    (Get-ChildItem "$Modulo\src\test\java" -Recurse -Filter '*.java').FullName

Push-Location $Modulo
& $Java -cp "target\classes;target\test-classes;src\main\resources;$Jpa;$Junit" `
    org.junit.platform.console.ConsoleLauncher execute --scan-class-path
Pop-Location
```

Os testes de escrita criam cópias temporárias do banco e não alteram o arquivo da parada.

## Restaurar os bancos

As paradas 2, 4, 5, 7 e 9 executam escrita. Algumas limpam seus dados demonstrativos, mas uma interrupção pode deixar mudanças. Para restaurar uma parada:

```powershell
Copy-Item -Force banco\livraria-base.db parada-05-transacoes\livraria.db
```

Para restaurar todas:

```powershell
Get-ChildItem -Directory 'parada-*' | ForEach-Object {
    Copy-Item -Force banco\livraria-base.db (Join-Path $_.FullName 'livraria.db')
}
```

Essa operação substitui os dados atuais da parada. Faça uma cópia antes se quiser preservar algum experimento.

## O que permanece separado

- `.lib` contém os JARs usados na execução manual;
- `.tools` contém o Java 17 do pacote e utilitários de preparação do banco;
- `banco/livraria-base.db` é a cópia limpa para restauração;
- cada parada abre apenas o banco que está em sua própria pasta;
- `target` contém somente artefatos gerados e não deve ser versionado.

## Referências do projeto

- [Material de estudo](JDBC_JPA_Material_Estudo.md)
- [Descrição do banco-base](banco/README.md)
- [`persistence.xml` inicial](parada-06-jpa-configuracao/src/main/resources/META-INF/persistence.xml)
- [Jakarta Persistence 3.2](https://jakarta.ee/specifications/persistence/3.2/)
- [Hibernate ORM](https://hibernate.org/orm/documentation/)
- [SQLite JDBC](https://github.com/xerial/sqlite-jdbc)
