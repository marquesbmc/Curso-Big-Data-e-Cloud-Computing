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

class ConsultaLivroTest {
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        bancoTemporario = Files.createTempFile("livraria-consulta-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, StandardCopyOption.REPLACE_EXISTING);
        System.setProperty("livraria.db", bancoTemporario.toString());
    }

    @AfterEach
    void descartarBanco() throws Exception {
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveMapearResultadoOpcionalELista() {
        ConsultaLivro consulta = new ConsultaLivro(new ConnectionFactory());

        Livro livro = consulta.buscarPorId(1L).orElseThrow();
        assertEquals(1L, livro.id());
        assertEquals("Dom Casmurro", livro.titulo());
        assertEquals("9780000000001", livro.isbn());
        assertEquals(0, new BigDecimal("39.90").compareTo(livro.preco()));
        assertEquals(12, livro.estoque());
        assertEquals(1L, livro.autorId());

        assertTrue(consulta.buscarPorId(999L).isEmpty());
        assertEquals(8, consulta.listarTodos().size());
        assertEquals("Casa de Alvenaria", consulta.buscarPorParteDoTitulo("Casa").get(0).titulo());
        assertFalse(consulta.buscarPorParteDoTitulo("titulo inexistente").iterator().hasNext());
    }
}
