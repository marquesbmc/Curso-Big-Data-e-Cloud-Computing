package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class LivroDAOTest {
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        bancoTemporario = Files.createTempFile("livraria-dao-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, StandardCopyOption.REPLACE_EXISTING);
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveExecutarCrudCompleto() {
        LivroDAO dao = new LivroDAO(new ConnectionFactory());

        Livro inserido = dao.inserir(new Livro(
                0L, "Teste DAO", "9789999000040",
                new BigDecimal("30.00"), 4, 1L));
        assertTrue(inserido.id() > 0);
        assertEquals("Teste DAO", dao.buscarPorId(inserido.id()).orElseThrow().titulo());

        Livro atualizado = new Livro(
                inserido.id(), "Teste DAO atualizado", inserido.isbn(),
                new BigDecimal("32.50"), 7, inserido.autorId());
        assertTrue(dao.atualizar(atualizado));

        Livro relido = dao.buscarPorId(inserido.id()).orElseThrow();
        assertEquals("Teste DAO atualizado", relido.titulo());
        assertEquals(0, new BigDecimal("32.50").compareTo(relido.preco()));
        assertEquals(7, relido.estoque());

        assertTrue(dao.excluir(inserido.id()));
        assertTrue(dao.buscarPorId(inserido.id()).isEmpty());
        assertFalse(dao.atualizar(atualizado));
        assertFalse(dao.excluir(inserido.id()));
    }
}
