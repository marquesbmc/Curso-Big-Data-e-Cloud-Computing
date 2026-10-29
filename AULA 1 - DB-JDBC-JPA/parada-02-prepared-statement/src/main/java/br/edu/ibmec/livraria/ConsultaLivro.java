package br.edu.ibmec.livraria;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

// Reune exemplos de leitura com um resultado opcional e com varios resultados.
public class ConsultaLivro {
    // A ConnectionFactory centraliza a forma de abrir conexoes com o banco.
    private final ConnectionFactory connectionFactory;

    public ConsultaLivro(ConnectionFactory connectionFactory) {
        // A consulta depende da fabrica, e nao de uma Connection mantida aberta.
        this.connectionFactory = connectionFactory;
    }

    public Optional<String> buscarPorId(long id) {
        // O texto SQL fica fixo; o valor do ID sera informado separadamente.
        String sql = """
                SELECT id, titulo
                FROM livro
                WHERE id = ?
                """;
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            // Connection e PreparedStatement serao fechados na ordem inversa.
            // O indice 1 corresponde ao primeiro marcador ? do SQL.
            statement.setLong(1, id);
            try (ResultSet resultSet = statement.executeQuery()) {
                // next() move o cursor para a primeira linha, se ela existir.
                if (resultSet.next()) {
                    return Optional.of(resultSet.getLong("id") + " - " + resultSet.getString("titulo"));
                }
                // Optional.empty representa uma consulta valida que nao encontrou linha.
                return Optional.empty();
            }
        } catch (SQLException exception) {
            // A causa original continua disponivel em exception.getCause().
            throw new IllegalStateException("Erro ao consultar livro", exception);
        }
    }

    public List<String> buscarPorParteDoTitulo(String titulo) {
        String sql = """
                SELECT id, titulo
                FROM livro
                WHERE titulo LIKE ?
                ORDER BY titulo
                """;
        List<String> livros = new ArrayList<>();
        // A lista vazia e um resultado valido quando nenhuma linha corresponde.
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            // Os % pertencem ao valor do parametro LIKE, nao ao texto do SQL.
            statement.setString(1, "%" + titulo + "%");
            try (ResultSet resultSet = statement.executeQuery()) {
                // Cada chamada de next() posiciona o cursor em uma nova linha.
                // Diferente da busca por ID, esta consulta pode produzir varias linhas.
                while (resultSet.next()) {
                    livros.add(resultSet.getLong("id") + " - " + resultSet.getString("titulo"));
                }
            }
            return livros;
        } catch (SQLException exception) {
            throw new IllegalStateException("Erro ao consultar livros", exception);
        }
    }
}
