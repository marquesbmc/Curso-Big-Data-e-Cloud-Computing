# Guia do professor: Parada 3

- Objetivo: mapear ResultSet para objetos Java. Duracao: 25 minutos.
- Abra: `Livro.java`, `LivroMapper.java`, `ConsultaLivro.java` e `Aplicacao.java`.
- Ordem: execute, observe o Optional vazio, acompanhe `resultSet.next()` e leia o mapeamento por nome de coluna.
- Pontos: getLong, getString, getBigDecimal e getInt leem a linha atual; o mapper evita repeticao.
- Perguntas: por que o cursor precisa de next? Quando Optional e mais apropriado que List?
- Resultado: livro encontrado, resultado vazio e listas no console.
- Experimento: consulte um ID inexistente.
- Transicao: o DAO centraliza o SQL e o mapeamento.