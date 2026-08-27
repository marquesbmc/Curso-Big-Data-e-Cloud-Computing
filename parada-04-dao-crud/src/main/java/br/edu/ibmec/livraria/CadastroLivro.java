package br.edu.ibmec.livraria;

import java.math.BigDecimal;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

// Exemplo da parada anterior mantido para comparacao. No fluxo principal desta
// aula, a responsabilidade de inserir passa para LivroDAO.
public class CadastroLivro {
    private final ConnectionFactory connectionFactory;

    public CadastroLivro(ConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public long inserir(String titulo, String isbn, BigDecimal preco, int estoque, long autorId) {
        // PreparedStatement separa o comando dos cinco valores recebidos.
        String sql = """
                INSERT INTO livro (titulo, isbn, preco, estoque, autor_id)
                VALUES (?, ?, ?, ?, ?)
                """;
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            // A ordem dos setters precisa acompanhar a ordem das colunas no INSERT.
            statement.setString(1, titulo);
            statement.setString(2, isbn);
            statement.setBigDecimal(3, preco);
            statement.setInt(4, estoque);
            statement.setLong(5, autorId);
            statement.executeUpdate();

            // O ID AUTOINCREMENT completa a identidade da linha recem-criada.
            try (ResultSet chaves = statement.getGeneratedKeys()) {
                if (chaves.next()) {
                    return chaves.getLong(1);
                }
                throw new SQLException("Insercao nao retornou chave gerada");
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Erro ao inserir livro", exception);
        }
    }
}
