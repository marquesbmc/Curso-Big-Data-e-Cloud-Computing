package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertFalse;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class ConnectionFactoryTest {
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        // Cada teste abre uma copia independente do arquivo de aula.
        bancoTemporario = Files.createTempFile("livraria-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        // A fabrica usa esta propriedade em vez de livraria.db.
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        // Limpa propriedade global e arquivo temporario.
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveAbrirConexao() throws Exception {
        // Valida a infraestrutura minima usada por todos os metodos do DAO.
        try (Connection connection = new ConnectionFactory().obterConexao()) {
            assertFalse(connection.isClosed());
        }
    }
}
