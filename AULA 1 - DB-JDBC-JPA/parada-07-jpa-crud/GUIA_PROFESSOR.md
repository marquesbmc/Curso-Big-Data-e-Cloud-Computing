# Guia do professor: Parada 7

- Objetivo: apresentar o ciclo de vida de entidades e o CRUD JPA. Duracao: 35 minutos.
- Abra: `Livro.java` e `Aplicacao.java`.
- Ordem: crie o objeto, verifique `contains`, execute `persist`, use `clear`, recupere com `find`, altere o objeto e finalize com `remove`.
- Pontos: operacoes de escrita exigem transacao; o ID aparece no persist; dirty checking elimina o UPDATE manual; `clear` destaca as entidades.
- Perguntas: por que nao existe chamada de update? O que muda depois de `clear`?
- Resultado: INSERT, SELECT, UPDATE e DELETE produzidos pelo Hibernate.
- Experimento: remova o `commit` da atualizacao e observe o banco.
- Transicao: a proxima parada troca `autorId` por um relacionamento entre objetos.
