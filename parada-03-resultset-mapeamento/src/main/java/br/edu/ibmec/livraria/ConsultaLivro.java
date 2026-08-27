package br.edu.ibmec.livraria;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

// Nesta parada as consultas deixam de devolver textos montados e passam a
// devolver objetos Livro, separando dados do banco de sua apresentacao.
public class ConsultaLivro {
    private final ConnectionFactory connectionFactory;

    // O mapper concentra a conversao de uma linha JDBC em um objeto Livro.
    private final LivroMapper livroMapper = new LivroMapper();

    public ConsultaLivro(ConnectionFactory connectionFactory) {
        // A dependencia e fornecida de fora e pode apontar para outro banco em testes.
        this.connectionFactory = connectionFactory;
    }

    public Optional<Livro> buscarPorId(long id) {
        // A API publica expressa que zero ou uma entidade pode ser encontrada.
        return buscarUm("SELECT * FROM livro WHERE id = ?", id);
    }

    public List<Livro> listarTodos() {
        // parametro null indica que este SQL nao possui marcador para preencher.
        return buscarLista("SELECT * FROM livro ORDER BY titulo", null);
    }

    public List<Livro> buscarPorParteDoTitulo(String titulo) {
        // Os curingas fazem parte do valor; o SQL continua fixo e parametrizado.
        return buscarLista("SELECT * FROM livro WHERE titulo LIKE ? ORDER BY titulo", "%" + titulo + "%");
    }

    // Consultas que esperam no maximo uma linha usam Optional como retorno.
    private Optional<Livro> buscarUm(String sql, long id) {
        // Connection, statement e ResultSet possuem ciclos de vida encaixados.
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setLong(1, id);

            // Quando nao ha linha, Optional.empty comunica a ausencia sem usar null.
            try (ResultSet resultSet = statement.executeQuery()) {
                // next posiciona o cursor. O mapper so pode ler depois desse passo.
                return resultSet.next()
                        ? Optional.of(livroMapper.mapear(resultSet))
                        : Optional.empty();
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Erro ao consultar livro", exception);
        }
    }

    // O mesmo metodo atende a consulta completa e a consulta com filtro opcional.
    private List<Livro> buscarLista(String sql, String parametro) {
        // Uma consulta sem linhas devolve uma lista vazia, nunca null.
        List<Livro> livros = new ArrayList<>();
        try (var connection = connectionFactory.obterConexao();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            if (parametro != null) {
                // Somente a consulta com LIKE possui o primeiro marcador.
                statement.setString(1, parametro);
            }

            // Enquanto houver linha, ela e mapeada e adicionada a lista.
            try (ResultSet resultSet = statement.executeQuery()) {
                // O mesmo mapper e reutilizado para todas as linhas do resultado.
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
