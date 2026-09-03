# Guia do professor: Parada 6

- Objetivo: apresentar a configuracao JPA e a primeira entidade. Duracao: 30 minutos.
- Abra: `persistence.xml`, `JPAUtil.java`, `Livro.java` e `Aplicacao.java`.
- Ordem: diferencie especificacao e implementacao, localize o dialeto SQLite, crie a fabrica, abra o EntityManager e execute os dois `find`.
- Pontos: Java 17 inclui JDBC, mas nao JPA; EntityManagerFactory e cara; EntityManager representa uma unidade de trabalho; `find` usa a chave primaria.
- Perguntas: quem implementa a especificacao JPA? Por que a fabrica nao deve ser criada para cada consulta?
- Resultado: um livro encontrado, um resultado nulo e o SQL gerado pelo Hibernate no console.
- Experimento: troque o ID por outro valor existente.
- Transicao: a proxima parada apresenta estados da entidade e operacoes CRUD.
