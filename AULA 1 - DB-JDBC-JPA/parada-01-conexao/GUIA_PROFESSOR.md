# Guia do professor: Parada 1

- Objetivo: apresentar DriverManager, Connection e try-with-resources. Duracao: 15 minutos.
- Abra: `ConnectionFactory.java` e `Aplicacao.java`.
- Ordem: execute a aplicacao, leia a URL `jdbc:sqlite:livraria.db`, localize `DriverManager.getConnection` e acompanhe o fechamento automatico.
- Pontos: a Connection representa a sessao com o banco; o driver e localizado automaticamente pelo Service Provider.
- Perguntas: quem fecha a conexao? O que acontece ao sair do try-with-resources?
- Resultado: driver, URL e confirmacao de fechamento no console.
- Experimento: altere temporariamente o nome do arquivo na URL e observe a falha.
- Transicao: a proxima parada envia comandos e parametros para a mesma conexao.