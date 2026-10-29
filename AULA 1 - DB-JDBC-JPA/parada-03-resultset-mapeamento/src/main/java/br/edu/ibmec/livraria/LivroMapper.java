package br.edu.ibmec.livraria;

import java.sql.ResultSet;
import java.sql.SQLException;

// Traduz uma linha JDBC para o modelo Java. O mapper nao abre conexao, nao
// executa SQL e nao movimenta o cursor: essas responsabilidades ficam na consulta.
public class LivroMapper {
    public Livro mapear(ResultSet resultSet) throws SQLException {
        // O cursor ja deve estar posicionado em uma linha pelo resultSet.next().
        // Ler pelo nome da coluna deixa clara a relacao entre SQL e objeto Java.
        // getBigDecimal preserva a precisao de NUMERIC usada para preco.
        // autor_id vira autorId porque o modelo Java usa camelCase.
        return new Livro(resultSet.getLong("id"), resultSet.getString("titulo"), resultSet.getString("isbn"),
                resultSet.getBigDecimal("preco"), resultSet.getInt("estoque"), resultSet.getLong("autor_id"));
    }
}
