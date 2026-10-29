package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import jakarta.persistence.EntityManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class JPAConfiguracaoTest {
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        // Cada teste recebe uma copia isolada. Assim nenhuma execucao altera o
        // livraria.db distribuido para a aula.
        bancoTemporario = Files.createTempFile("livraria-jpa-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, StandardCopyOption.REPLACE_EXISTING);
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        // Remover a propriedade faz a proxima execucao voltar ao caminho padrao.
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveLocalizarLivroPelaChavePrimaria() {
        // Arrange e Act: inicializa JPA e pesquisa duas chaves primarias.
        try (JPAUtil jpa = new JPAUtil();
             EntityManager entityManager = jpa.criarEntityManager()) {
            Livro livro = entityManager.find(Livro.class, 1L);

            // Assert: uma chave conhecida retorna entidade; uma ausente retorna null.
            assertEquals("Dom Casmurro", livro.getTitulo());
            assertNull(entityManager.find(Livro.class, 999L));
        }
    }
}
