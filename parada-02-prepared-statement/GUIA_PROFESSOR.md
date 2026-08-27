# Guia do professor: Parada 2

- Objetivo: demonstrar PreparedStatement, parametros e chave gerada. Duracao: 25 minutos.
- Abra: `ConsultaLivro.java`, `CadastroLivro.java` e `Aplicacao.java`.
- Ordem: execute, compare o SQL com `?`, acompanhe os `set...`, depois `executeQuery`, `executeUpdate` e `getGeneratedKeys`.
- Pontos: SQL e valores sao partes diferentes; parametros nunca sao concatenados no comando.
- Perguntas: quando usar executeQuery? Por que a chave e recuperada depois da insercao?
- Resultado: consultas retornam livros e a insercao informa um novo ID.
- Experimento: remova temporariamente um `setString` para observar a falha de parametro.
- Transicao: a proxima parada transforma linhas em objetos Livro.