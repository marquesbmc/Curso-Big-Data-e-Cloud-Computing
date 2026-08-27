package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class CadastroLivroTest {
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        bancoTemporario = Files.createTempFile("livraria-mapper-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, StandardCopyOption.REPLACE_EXISTING);
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveInserirLivroERetornarChaveGerada() {
        // Arrange: prepara o colaborador responsavel pelo INSERT.
        CadastroLivro cadastro = new CadastroLivro(new ConnectionFactory());

        // Act: cadastra uma linha com todos os parametros exigidos.
        long id = cadastro.inserir("Teste PreparedStatement", "9789999000002", new BigDecimal("10.00"), 1, 1);

        // Assert: a chave confirma que o SQLite aceitou e identificou a linha.
        assertTrue(id > 0);
    }
}
