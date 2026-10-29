# Guia do professor: Parada 9

- Objetivo: registrar uma venda atomica com JPA. Duracao: 40 minutos.
- Abra: `VendaService.java`, `Venda.java`, `ItemVenda.java`, `Livro.java` e `LocalDateTimeStringConverter.java`.
- Ordem: inicie a transacao, recupere o livro, altere o estoque, monte venda e item, execute `persist` e acompanhe o commit; depois execute a falha controlada apos `flush`.
- Pontos: um EntityManager delimita o contexto; cascade persiste o item; dirty checking atualiza o livro; flush envia SQL sem confirmar; rollback descarta toda a unidade de trabalho; o converter adapta LocalDateTime para a coluna TEXT existente.
- Perguntas: por que apenas `Venda` recebe `persist`? De onde vem o UPDATE de livro?
- Resultado: venda e item inseridos, estoque reduzido e uma segunda tentativa integralmente revertida.
- Experimento: remova o `flush` da demonstracao e compare quais comandos aparecem antes do rollback.
- Transicao: encerramento da sequencia JPA sem JPQL.
