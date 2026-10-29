# Guia do professor: Parada 8

- Objetivo: mapear e navegar em relacionamentos JPA. Duracao: 40 minutos.
- Abra: `Autor.java`, `Livro.java` e `Aplicacao.java`.
- Ordem: compare `autorId` com `Autor autor`, leia `@JoinColumn`, identifique o `mappedBy` e acompanhe os SELECTs antes e depois da colecao.
- Pontos: `Livro` e o lado dono da relacao; `Autor.livros` e o lado inverso; lazy adia a consulta; `toString` nao deve percorrer os dois lados.
- Perguntas: qual atributo controla `autor_id`? Por que acessar a colecao produz outro SELECT?
- Resultado: navegacao Autor -> livros e Livro -> autor sem escrever SQL ou JPQL.
- Experimento: feche o EntityManager antes de acessar `autor.getLivros()` e observe a falha lazy.
- Transicao: a proxima parada usa relacionamentos e transacao para registrar uma venda.
