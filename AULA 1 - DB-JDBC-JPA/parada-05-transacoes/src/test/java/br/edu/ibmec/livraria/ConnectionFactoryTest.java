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
        // O teste trabalha em uma copia para proteger vendas e estoques da aula.
        bancoTemporario = Files.createTempFile("livraria-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        // ConnectionFactory usara a copia enquanto esta propriedade existir.
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        // Remove configuracao global e o arquivo temporario.
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveAbrirConexao() throws Exception {
        // Confirma a infraestrutura minima antes dos testes de transacao.
        try (Connection connection = new ConnectionFactory().obterConexao()) {
            assertFalse(connection.isClosed());
        }
    }
}
