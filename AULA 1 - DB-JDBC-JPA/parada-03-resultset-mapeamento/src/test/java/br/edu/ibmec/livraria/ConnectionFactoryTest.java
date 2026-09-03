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
        // A copia temporaria isola o teste do arquivo entregue aos alunos.
        bancoTemporario = Files.createTempFile("livraria-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        // ConnectionFactory consultara esta propriedade antes do caminho padrao.
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        // Limpa configuracao global e o arquivo criado para este teste.
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveAbrirConexao() throws Exception {
        // A conexao deve estar utilizavel dentro do try-with-resources.
        try (Connection connection = new ConnectionFactory().obterConexao()) {
            assertFalse(connection.isClosed());
        }
    }
}
