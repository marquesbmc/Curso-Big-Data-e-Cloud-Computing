package br.edu.ibmec.livraria;

import java.math.BigDecimal;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

// Exemplo de cadastro das paradas anteriores. Ele permanece para comparacao,
// mas nao participa do fluxo transacional de venda.
public class CadastroLivro {
    private final ConnectionFactory connectionFactory;

    public CadastroLivro(ConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public long inserir(String titulo, String isbn, BigDecimal preco, int estoque, long autorId) {
        // Este metodo abre sua propria Connection; por isso nao seria adequado
        // para compor uma venda que precisa compartilhar uma unica transacao.
        String sql = """
                INSERT INTO livro (titulo, isbn, preco, estoque, autor_id)
                VALUES (?, ?, ?, ?, ?)
                """;
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            // Parametros seguem a ordem dos cinco marcadores do INSERT.
            statement.setString(1, titulo);
            statement.setString(2, isbn);
            statement.setBigDecimal(3, preco);
            statement.setInt(4, estoque);
            statement.setLong(5, autorId);
            statement.executeUpdate();

            // O ID gerado fica associado a sessao e ao INSERT recem-executado.
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
