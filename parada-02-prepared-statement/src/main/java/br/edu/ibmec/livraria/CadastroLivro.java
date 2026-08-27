package br.edu.ibmec.livraria;

import java.math.BigDecimal;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

// Executa o caso de escrita desta parada: inserir uma linha com parametros e
// recuperar o identificador gerado pelo banco.
public class CadastroLivro {
    // A classe conhece a fabrica, mas nao guarda uma Connection aberta como atributo.
    private final ConnectionFactory connectionFactory;

    public CadastroLivro(ConnectionFactory connectionFactory) {
        // Receber a dependencia no construtor facilita substituir o banco em testes.
        this.connectionFactory = connectionFactory;
    }

    public long inserir(String titulo, String isbn, BigDecimal preco, int estoque, long autorId) {
        // Os marcadores ? reservam os lugares dos valores. Nenhum dado recebido
        // pelo metodo e concatenado ao texto SQL.
        String sql = """
                INSERT INTO livro (titulo, isbn, preco, estoque, autor_id)
                VALUES (?, ?, ?, ?, ?)
                """;
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            // RETURN_GENERATED_KEYS pede ao banco o ID criado para esta nova linha.
            // Os tipos dos setters devem combinar com os tipos dos valores Java.
            // Os indices comecam em 1 e seguem a ordem dos marcadores no SQL.
            statement.setString(1, titulo);
            statement.setString(2, isbn);
            statement.setBigDecimal(3, preco);
            statement.setInt(4, estoque);
            statement.setLong(5, autorId);
            // INSERT, UPDATE e DELETE usam executeUpdate e retornam linhas afetadas.
            // Nesta parada o retorno nao e usado; a chave e lida logo em seguida.
            statement.executeUpdate();

            // GeneratedKeys e outro ResultSet e tambem precisa ser fechado.
            try (ResultSet chaves = statement.getGeneratedKeys()) {
                // O ResultSet de chaves tambem precisa ser posicionado com next().
                if (chaves.next()) {
                    return chaves.getLong(1);
                }
                throw new SQLException("Insercao nao retornou chave gerada");
            }
        } catch (SQLException exception) {
            // Convertemos a excecao verificada em falha da operacao de cadastro,
            // preservando a SQLException original como causa para diagnostico.
            throw new IllegalStateException("Erro ao inserir livro", exception);
        }
    }
}
