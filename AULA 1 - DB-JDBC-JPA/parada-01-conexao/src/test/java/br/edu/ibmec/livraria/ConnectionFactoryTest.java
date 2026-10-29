package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertFalse;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class ConnectionFactoryTest {
    // Cada teste guarda o caminho de sua propria copia descartavel.
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        // Criar um arquivo temporario evita usar diretamente o banco da aula.
        bancoTemporario = Files.createTempFile("livraria-", ".db");

        // A copia preserva tabelas e dados necessarios para abrir a conexao.
        Files.copy(Path.of("livraria.db"), bancoTemporario, java.nio.file.StandardCopyOption.REPLACE_EXISTING);

        // ConnectionFactory le esta propriedade antes de usar o caminho padrao.
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        // A limpeza impede que um teste influencie os seguintes.
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveAbrirConexao() throws Exception {
        // O teste valida a conexao dentro do bloco em que ela ainda esta aberta.
        try (Connection connection = new ConnectionFactory().obterConexao()) {
            assertFalse(connection.isClosed());
        }
    }
}
