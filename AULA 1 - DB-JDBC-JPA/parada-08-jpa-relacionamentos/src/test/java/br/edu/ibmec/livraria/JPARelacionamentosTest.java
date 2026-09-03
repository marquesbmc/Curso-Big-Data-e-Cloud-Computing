package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import jakarta.persistence.EntityManager;
import jakarta.persistence.Persistence;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class JPARelacionamentosTest {
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        // Embora este teste seja de leitura, a copia mantem o mesmo isolamento das aulas.
        bancoTemporario = Files.createTempFile("livraria-jpa-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, StandardCopyOption.REPLACE_EXISTING);
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveNavegarEntreAutorELivros() {
        try (JPAUtil jpa = new JPAUtil();
             EntityManager entityManager = jpa.criarEntityManager()) {
            Autor autor = entityManager.find(Autor.class, 1L);

            // A verificacao antes/depois prova que a colecao foi carregada sob demanda.
            assertFalse(Persistence.getPersistenceUtil().isLoaded(autor, "livros"));
            assertEquals(2, autor.getLivros().size());
            assertTrue(Persistence.getPersistenceUtil().isLoaded(autor, "livros"));

            // Tambem validamos a navegacao inversa, do lado muitos para o lado um.
            Livro livro = entityManager.find(Livro.class, 3L);
            assertEquals("Clarice Lispector", livro.getAutor().getNome());
        }
    }
}
