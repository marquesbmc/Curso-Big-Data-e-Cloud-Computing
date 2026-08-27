package br.edu.ibmec.livraria;

import java.math.BigDecimal;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

// Mantido nesta parada para mostrar que o cadastro continua igual enquanto a
// evolucao se concentra na conversao dos resultados de consulta.
public class CadastroLivro {
    private final ConnectionFactory connectionFactory;

    public CadastroLivro(ConnectionFactory connectionFactory) {
        // A classe recebe a fabrica e abre a conexao apenas quando inserir.
        this.connectionFactory = connectionFactory;
    }

    public long inserir(String titulo, String isbn, BigDecimal preco, int estoque, long autorId) {
        // Marcadores impedem concatenacao de valores no comando SQL.
        String sql = """
                INSERT INTO livro (titulo, isbn, preco, estoque, autor_id)
                VALUES (?, ?, ?, ?, ?)
                """;
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            // Cada setter corresponde ao marcador de mesma posicao, iniciando em 1.
            statement.setString(1, titulo);
            statement.setString(2, isbn);
            statement.setBigDecimal(3, preco);
            statement.setInt(4, estoque);
            statement.setLong(5, autorId);
            statement.executeUpdate();

            // A chave gerada vem em um ResultSet separado do comando de INSERT.
            try (ResultSet chaves = statement.getGeneratedKeys()) {
                // O cursor nasce antes da primeira linha e precisa avancar.
                if (chaves.next()) {
                    return chaves.getLong(1);
                }
                throw new SQLException("Insercao nao retornou chave gerada");
            }
        } catch (SQLException exception) {
            // Preservar a causa facilita enxergar restricoes como ISBN duplicado.
            throw new IllegalStateException("Erro ao inserir livro", exception);
        }
    }
}
