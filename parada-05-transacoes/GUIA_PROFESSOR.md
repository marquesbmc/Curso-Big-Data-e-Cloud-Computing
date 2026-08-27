# Guia do professor: Parada 5

- Objetivo: apresentar commit, rollback e Savepoint. Duracao: 35 minutos.
- Abra: `VendaService.java` e `Aplicacao.java`.
- Ordem: execute a venda valida, acompanhe setAutoCommit(false), insercoes, atualizacao de estoque e commit; depois observe a venda invalida e rollback.
- Pontos: todos os comandos usam a mesma Connection; o finally restaura autoCommit; o Savepoint e um exemplo separado.
- Perguntas: o que ficaria inconsistente se a venda fosse inserida e o estoque nao fosse atualizado?
- Resultado: venda valida reduz estoque; venda invalida nao altera venda, item ou estoque.
- Experimento: aumente a quantidade acima do estoque disponivel.
- Transicao: encerramento da sequencia JDBC.