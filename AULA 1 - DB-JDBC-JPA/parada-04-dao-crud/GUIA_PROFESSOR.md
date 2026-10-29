# Guia do professor: Parada 4

- Objetivo: organizar CRUD em um DAO. Duracao: 30 minutos.
- Abra: `LivroDAO.java`, `LivroMapper.java` e `Aplicacao.java`.
- Ordem: execute e acompanhe inserir, buscar, listar, atualizar, excluir e a comprovacao final.
- Pontos: DAO guarda o SQL; cada metodo abre sua Connection; PreparedStatement e try-with-resources aparecem em todas as operacoes.
- Perguntas: por que o DAO nao guarda uma Connection como atributo? Qual metodo retorna boolean?
- Resultado: registro inserido, atualizado, excluido e depois ausente.
- Experimento: busque o ID apos a exclusao.
- Transicao: uma venda precisa de varios comandos na mesma transacao.