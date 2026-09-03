package br.edu.ibmec.livraria;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public class ConsultaLivro {
    private final ConnectionFactory connectionFactory;
    private final LivroMapper livroMapper = new LivroMapper();

    // Esta classe representa o desenho anterior ao DAO completo e permanece no
    // projeto para que o aluno compare as duas organizacoes.
    public ConsultaLivro(ConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public Optional<Livro> buscarPorId(long id) {
        return buscarUm("SELECT * FROM livro WHERE id = ?", id);
    }

    public List<Livro> listarTodos() {
        return buscarLista("SELECT * FROM livro ORDER BY titulo", null);
    }

    public List<Livro> buscarPorParteDoTitulo(String titulo) {
        return buscarLista(
                "SELECT * FROM livro WHERE titulo LIKE ? ORDER BY titulo",
                "%" + titulo + "%");
    }

    private Optional<Livro> buscarUm(String sql, long id) {
        // Um resultado unico usa Optional para representar a ausencia da linha.
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setLong(1, id);

            try (ResultSet resultSet = statement.executeQuery()) {
                return resultSet.next()
                        ? Optional.of(livroMapper.mapear(resultSet))
                        : Optional.empty();
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Erro ao consultar livro", exception);
        }
    }

    private List<Livro> buscarLista(String sql, String parametro) {
        // Resultados multiplos sao acumulados em uma lista inicialmente vazia.
        List<Livro> livros = new ArrayList<>();
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            if (parametro != null) {
                statement.setString(1, parametro);
            }

            try (ResultSet resultSet = statement.executeQuery()) {
                while (resultSet.next()) {
                    livros.add(livroMapper.mapear(resultSet));
                }
            }
            return livros;
        } catch (SQLException exception) {
            throw new IllegalStateException("Erro ao listar livros", exception);
        }
    }
}
