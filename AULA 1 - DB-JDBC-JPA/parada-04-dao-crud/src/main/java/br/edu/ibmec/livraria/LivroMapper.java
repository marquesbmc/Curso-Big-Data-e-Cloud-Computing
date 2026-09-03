package br.edu.ibmec.livraria;

import java.sql.ResultSet;
import java.sql.SQLException;

// Compartilhado pelos metodos de leitura do DAO para que todas as consultas
// convertam colunas em Livro da mesma forma.
public class LivroMapper {
    public Livro mapear(ResultSet resultSet) throws SQLException {
        // O ResultSet deve estar posicionado em uma linha antes deste metodo.
        // Os nomes usados aqui correspondem diretamente as colunas da tabela.
        // O mapper pode propagar SQLException porque o DAO decide como trata-la.
        return new Livro(resultSet.getLong("id"), resultSet.getString("titulo"), resultSet.getString("isbn"),
                resultSet.getBigDecimal("preco"), resultSet.getInt("estoque"), resultSet.getLong("autor_id"));
    }
}
