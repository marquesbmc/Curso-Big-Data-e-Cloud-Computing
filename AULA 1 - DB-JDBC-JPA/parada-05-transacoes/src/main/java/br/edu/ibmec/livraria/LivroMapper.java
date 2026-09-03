package br.edu.ibmec.livraria;

import java.sql.ResultSet;
import java.sql.SQLException;

// Converte a linha atual em Livro. O metodo nao chama next e nao fecha ResultSet;
// essas responsabilidades permanecem com o codigo que executou a consulta.
public class LivroMapper {
    public Livro mapear(ResultSet resultSet) throws SQLException {
        // O mapper separa a leitura das colunas da regra de negocio da venda.
        // Ler pelo nome reduz dependencia da ordem das colunas no SELECT.
        return new Livro(resultSet.getLong("id"), resultSet.getString("titulo"), resultSet.getString("isbn"),
                resultSet.getBigDecimal("preco"), resultSet.getInt("estoque"), resultSet.getLong("autor_id"));
    }
}
