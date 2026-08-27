package br.edu.ibmec.livraria;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

// Consultas de apoio usadas pela aplicacao para observar o estoque antes e
// depois da venda. O fluxo de gravacao fica concentrado em VendaService.
public class ConsultaLivro {
    private final ConnectionFactory connectionFactory;
    private final LivroMapper livroMapper = new LivroMapper();

    public ConsultaLivro(ConnectionFactory connectionFactory) {
        // A classe guarda a fabrica, e nao uma Connection permanentemente aberta.
        this.connectionFactory = connectionFactory;
    }

    public Optional<Livro> buscarPorId(long id) {
        // Optional distingue livro ausente de falha ao consultar.
        return buscarUm("SELECT * FROM livro WHERE id = ?", id);
    }

    public List<Livro> listarTodos() {
        // O helper recebe null porque esta consulta nao possui parametro.
        return buscarLista("SELECT * FROM livro ORDER BY titulo", null);
    }

    public List<Livro> buscarPorParteDoTitulo(String titulo) {
        // Os curingas pertencem ao valor enviado ao PreparedStatement.
        return buscarLista("SELECT * FROM livro WHERE titulo LIKE ? ORDER BY titulo", "%" + titulo + "%");
    }

    private Optional<Livro> buscarUm(String sql, long id) {
        // Os tres recursos JDBC sao fechados automaticamente.
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setLong(1, id);

            try (ResultSet resultSet = statement.executeQuery()) {
                // next posiciona o cursor antes de LivroMapper ler as colunas.
                return resultSet.next()
                        ? Optional.of(livroMapper.mapear(resultSet))
                        : Optional.empty();
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Erro ao consultar livro", exception);
        }
    }

    private List<Livro> buscarLista(String sql, String parametro) {
        // Nenhuma linha resulta em lista vazia, nunca em null.
        List<Livro> livros = new ArrayList<>();
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            if (parametro != null) {
                statement.setString(1, parametro);
            }

            try (ResultSet resultSet = statement.executeQuery()) {
                // Cada linha e convertida em um record independente.
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
