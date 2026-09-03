package br.edu.ibmec.livraria;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Savepoint;
import java.sql.Statement;
import java.time.LocalDateTime;

// O service coordena comandos JDBC que devem ter sucesso ou falhar juntos.
public class VendaService {
    // A fabrica sera usada para abrir uma Connection por tentativa de venda.
    private final ConnectionFactory connectionFactory;

    public VendaService(ConnectionFactory connectionFactory) {
        // Injecao por construtor deixa a dependencia explicita para a aplicacao.
        this.connectionFactory = connectionFactory;
    }

    public VendaResultado registrarVenda(long livroId, int quantidade) {
        if (quantidade <= 0) {
            throw new IllegalArgumentException("Quantidade deve ser positiva");
        }

        // A mesma Connection delimita toda a transacao. Se cada metodo abrisse uma
        // conexao diferente, o rollback nao conseguiria desfazer todos os comandos.
        try (Connection connection = connectionFactory.obterConexao()) {
            // Guardamos o estado recebido para nao impor outra configuracao a
            // quem reutilizasse esta Connection depois do metodo.
            boolean autoCommitOriginal = connection.getAutoCommit();

            // Com autoCommit desligado, os comandos aguardam commit ou rollback.
            connection.setAutoCommit(false);
            try {
                // Todas as chamadas abaixo recebem exatamente a mesma Connection.
                Livro livro = buscarLivro(connection, livroId);

                // A validacao ocorre antes de inserir venda ou baixar estoque.
                if (livro.estoque() < quantidade) {
                    throw new EstoqueInsuficienteException("Estoque insuficiente");
                }

                BigDecimal valorTotal = livro.preco().multiply(BigDecimal.valueOf(quantidade));

                // A venda precisa existir antes porque item_venda referencia seu ID.
                long vendaId = inserirVenda(connection, valorTotal);

                // Item e estoque completam a unidade atomica de trabalho.
                inserirItemVenda(connection, vendaId, livroId, quantidade, livro.preco());
                baixarEstoque(connection, livroId, quantidade);

                // Somente aqui as tres alteracoes se tornam definitivas no banco.
                connection.commit();
                return new VendaResultado(
                        new Venda(vendaId, LocalDateTime.now(), valorTotal),
                        livro.estoque() - quantidade);
            } catch (SQLException | RuntimeException exception) {
                // Qualquer falha desfaz venda, item e estoque como uma unica unidade.
                connection.rollback();

                // Relancar preserva a causa original para a camada chamadora.
                throw exception;
            } finally {
                // A conexao volta ao estado encontrado antes de iniciar a transacao.
                // O finally executa tanto depois de commit quanto depois de rollback.
                connection.setAutoCommit(autoCommitOriginal);
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Venda nao concluida", exception);
        }
    }

    // A Connection chega por parametro para que esta consulta participe da transacao.
    private Livro buscarLivro(Connection connection, long id) throws SQLException {
        // SELECT * e suficiente aqui porque LivroMapper precisa de todas as colunas.
        String sql = "SELECT * FROM livro WHERE id = ?";

        try (var statement = connection.prepareStatement(sql)) {
            statement.setLong(1, id);
            try (ResultSet resultSet = statement.executeQuery()) {
                // A venda exige um livro existente; ausencia e tratada como falha.
                if (!resultSet.next()) {
                    throw new SQLException("Livro inexistente");
                }
                return new LivroMapper().mapear(resultSet);
            }
        }
    }

    private long inserirVenda(Connection connection, BigDecimal valorTotal) throws SQLException {
        // data_hora e armazenada como texto ISO-8601 no esquema SQLite existente.
        String sql = "INSERT INTO venda (data_hora, valor_total) VALUES (?, ?)";

        try (var statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            statement.setString(1, LocalDateTime.now().toString());
            statement.setBigDecimal(2, valorTotal);
            statement.executeUpdate();

            try (ResultSet chaves = statement.getGeneratedKeys()) {
                // O ID e necessario para preencher venda_id em item_venda.
                chaves.next();
                return chaves.getLong(1);
            }
        }
    }

    private void inserirItemVenda(
            Connection connection,
            long vendaId,
            long livroId,
            int quantidade,
            BigDecimal precoUnitario) throws SQLException {
        // O item registra quantidade e preco do momento da venda.
        String sql = """
                INSERT INTO item_venda (venda_id, livro_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
                """;

        try (var statement = connection.prepareStatement(sql)) {
            // Os dois primeiros parametros formam as referencias da associacao.
            statement.setLong(1, vendaId);
            statement.setLong(2, livroId);
            statement.setInt(3, quantidade);
            statement.setBigDecimal(4, precoUnitario);
            statement.executeUpdate();
        }
    }

    private void baixarEstoque(Connection connection, long livroId, int quantidade) throws SQLException {
        // A subtracao ocorre no banco usando o valor atual da coluna.
        String sql = "UPDATE livro SET estoque = estoque - ? WHERE id = ?";

        try (var statement = connection.prepareStatement(sql)) {
            statement.setInt(1, quantidade);
            statement.setLong(2, livroId);
            statement.executeUpdate();
        }
    }

    public void demonstrarSavepoint() {
        // Esta demonstracao e separada da venda para nao misturar rollback total
        // com rollback parcial no primeiro contato do aluno com transacoes.
        try (Connection connection = connectionFactory.obterConexao()) {
            connection.setAutoCommit(false);
            try (var statement = connection.prepareStatement(
                    "UPDATE livro SET estoque = estoque WHERE id = ?")) {
                statement.setLong(1, 1);

                // UPDATE sem mudanca oferece um comando seguro para a demonstracao.
                statement.executeUpdate();

                // Um savepoint permite desfazer apenas uma parte da transacao.
                // rollback(ponto) preserva comandos anteriores ao ponto e desfaz
                // somente os posteriores; aqui o foco e apresentar a API.
                Savepoint ponto = connection.setSavepoint("demonstracao");
                connection.rollback(ponto);

                // O restante da transacao e confirmado normalmente.
                connection.commit();
                System.out.println("[4] Savepoint demonstrado");
            } finally {
                // Mesmo antes de fechar, restauramos o modo padrao da Connection.
                connection.setAutoCommit(true);
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Erro no savepoint", exception);
        }
    }
}
