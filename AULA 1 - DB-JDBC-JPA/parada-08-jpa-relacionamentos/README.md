# Parada 8 — Como navegar entre livros e autores sem escrever consultas?

## 1. O problema

Um ID informa quem é o autor, mas não oferece navegação entre objetos. Queremos percorrer `Livro → Autor` e `Autor → livros` sem esconder quando consultas adicionais ocorrem.

## 2. Objetivo

Ao concluir, você deverá identificar lado dono e inverso, interpretar `@JoinColumn` e `mappedBy` e observar lazy loading com o contexto aberto.

## 3. Arquivos principais

1. [`Livro.java`](src/main/java/br/edu/ibmec/livraria/Livro.java)
2. [`Autor.java`](src/main/java/br/edu/ibmec/livraria/Autor.java)
3. [`Aplicacao.java`](src/main/java/br/edu/ibmec/livraria/Aplicacao.java)
4. [`JPARelacionamentosTest.java`](src/test/java/br/edu/ibmec/livraria/JPARelacionamentosTest.java)

## 4. Execução

Abra o PowerShell **na raiz do repositório**, onde aparecem as pastas `.tools`, `.lib` e `parada-08-jpa-relacionamentos`. Copie somente as linhas dentro do bloco abaixo; não copie o texto `PS C:\...>` nem os sinais `>>` mostrados pelo terminal.

```powershell
$Modulo = 'parada-08-jpa-relacionamentos'
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

- `Livro.autor` substitui `autorId` e controla `autor_id` com `@ManyToOne`;
- `Autor.livros` é o lado inverso com `@OneToMany(mappedBy = "autor")`;
- `mappedBy` aponta para um atributo Java, não para uma coluna;
- a coleção está descarregada antes do primeiro uso e exige contexto aberto;
- os `toString()` não percorrem os dois lados, evitando recursão e carga acidental.

## 6. Experimento

Guarde o `Autor`, feche o `EntityManager` antes de percorrer `getLivros()` e tente consultar o tamanho da coleção ainda não inicializada.

## 7. Resultado esperado

Com o contexto aberto, o primeiro acesso gera outro `SELECT` e a coleção passa a carregada. Depois do fechamento antecipado, o provedor não consegue inicializá-la.

## 8. Pergunta de verificação

<details>
<summary>Por que `Livro` é o lado dono?</summary>

Porque seu atributo `autor` possui `@JoinColumn` e controla a chave estrangeira `autor_id`.
</details>

## 9. Transição

Relacionamentos já representam o grafo de objetos. A última parada usará esse grafo para persistir uma venda como uma unidade de trabalho.

> **Aprofundamento — serialização:** entidades com associações bidirecionais e lazy não devem ser serializadas sem planejar contexto, forma do JSON e risco de recursão.
