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
        // O teste abre uma copia para nunca depender de um banco vazio ou alterado.
        bancoTemporario = Files.createTempFile("livraria-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, java.nio.file.StandardCopyOption.REPLACE_EXISTING);

        // A propriedade redireciona ConnectionFactory somente durante o teste.
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        // Restaurar o ambiente e tao importante quanto preparar os dados.
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveAbrirConexao() throws Exception {
        // isClosed deve ser falso antes de sair do try-with-resources.
        try (Connection connection = new ConnectionFactory().obterConexao()) {
            assertFalse(connection.isClosed());
        }
    }
}
