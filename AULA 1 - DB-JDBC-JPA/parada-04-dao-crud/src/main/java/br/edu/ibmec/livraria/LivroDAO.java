package br.edu.ibmec.livraria;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

// DAO (Data Access Object) concentra o SQL e esconde os detalhes do JDBC
// das outras classes da aplicacao.
public class LivroDAO {
    // A fabrica abre conexoes; o mapper transforma linhas em objetos.
    private final ConnectionFactory connectionFactory;
    private final LivroMapper livroMapper = new LivroMapper();

    public LivroDAO(ConnectionFactory connectionFactory) {
        // Injecao por construtor deixa a dependencia visivel e substituivel.
        this.connectionFactory = connectionFactory;
    }

    public Livro inserir(Livro livro) {
        // O DAO concentra o SQL, evitando espalhar nomes de tabela pela aplicacao.
        String sql = """
                INSERT INTO livro (titulo, isbn, preco, estoque, autor_id)
                VALUES (?, ?, ?, ?, ?)
                """;

        // Cada operacao abre e fecha sua propria conexao nesta etapa.
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            preencherDadosDoLivro(statement, livro);

            // executeUpdate executa INSERT e devolve a quantidade de linhas afetadas.
            statement.executeUpdate();

            // A chave gerada completa o objeto que chegou com ID igual a zero.
            try (ResultSet chaves = statement.getGeneratedKeys()) {
                if (chaves.next()) {
                    return new Livro(
                            chaves.getLong(1),
                            livro.titulo(),
                            livro.isbn(),
                            livro.preco(),
                            livro.estoque(),
                            livro.autorId());
                }
                throw new SQLException("Chave ausente");
            }
        } catch (SQLException exception) {
            // A SQLException original permanece como causa da excecao de aplicacao.
            throw new IllegalStateException(exception);
        }
    }

    public Optional<Livro> buscarPorId(long id) {
        // A chave primaria garante no maximo uma linha de resultado.
        String sql = "SELECT * FROM livro WHERE id = ?";

        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setLong(1, id);

            try (ResultSet resultSet = statement.executeQuery()) {
                // A ausencia de uma linha e um resultado esperado, nao uma excecao.
                return resultSet.next()
                        ? Optional.of(livroMapper.mapear(resultSet))
                        : Optional.empty();
            }
        } catch (SQLException exception) {
            throw new IllegalStateException(exception);
        }
    }

    public List<Livro> listarTodos() {
        // null informa ao helper que o SQL nao possui marcador de parametro.
        return buscarLista("SELECT * FROM livro ORDER BY titulo", null);
    }

    public List<Livro> buscarPorTitulo(String titulo) {
        // Os curingas pertencem ao valor vinculado, nao ao texto do SQL.
        return buscarLista(
                "SELECT * FROM livro WHERE titulo LIKE ?",
                "%" + titulo + "%");
    }

    public boolean atualizar(Livro livro) {
        // O ID fica no WHERE e, portanto, ocupa o sexto parametro.
        String sql = """
                UPDATE livro
                SET titulo = ?, isbn = ?, preco = ?, estoque = ?, autor_id = ?
                WHERE id = ?
                """;

        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            preencherDadosDoLivro(statement, livro);
            statement.setLong(6, livro.id());

            // executeUpdate devolve quantas linhas foram afetadas. Uma linha indica sucesso.
            return statement.executeUpdate() == 1;
        } catch (SQLException exception) {
            throw new IllegalStateException(exception);
        }
    }

    public boolean excluir(long id) {
        // Excluir por chave primaria afeta zero ou uma linha.
        String sql = "DELETE FROM livro WHERE id = ?";

        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setLong(1, id);

            // Zero linhas significa que o ID informado nao existia.
            return statement.executeUpdate() == 1;
        } catch (SQLException exception) {
            throw new IllegalStateException(exception);
        }
    }

    private List<Livro> buscarLista(String sql, String parametro) {
        // O helper reduz repeticao entre listarTodos e buscarPorTitulo.
        List<Livro> livros = new ArrayList<>();

        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            if (parametro != null) {
                statement.setString(1, parametro);
            }

            try (ResultSet resultSet = statement.executeQuery()) {
                // next movimenta o cursor uma linha por vez ate o fim.
                while (resultSet.next()) {
                    livros.add(livroMapper.mapear(resultSet));
                }
            }
            return livros;
        } catch (SQLException exception) {
            throw new IllegalStateException(exception);
        }
    }

    // INSERT e UPDATE usam os mesmos cinco campos e a mesma ordem de parametros.
    // Centralizar esse preenchimento evita que os dois comandos se comportem diferente.
    private void preencherDadosDoLivro(PreparedStatement statement, Livro livro) throws SQLException {
        // O metodo nao chama executeUpdate; ele apenas prepara o statement recebido.
        statement.setString(1, livro.titulo());
        statement.setString(2, livro.isbn());
        statement.setBigDecimal(3, livro.preco());
        statement.setInt(4, livro.estoque());
        statement.setLong(5, livro.autorId());
    }
}
