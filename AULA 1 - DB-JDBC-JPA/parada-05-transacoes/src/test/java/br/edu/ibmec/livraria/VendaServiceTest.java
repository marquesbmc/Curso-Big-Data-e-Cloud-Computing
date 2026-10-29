package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.sql.Connection;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class VendaServiceTest {
    private Path bancoTemporario;
    private ConnectionFactory connectionFactory;

    @BeforeEach
    void prepararBanco() throws Exception {
        bancoTemporario = Files.createTempFile("livraria-venda-", ".db");
        Files.copy(Path.of("livraria.db"), bancoTemporario, StandardCopyOption.REPLACE_EXISTING);
        System.setProperty("livraria.db", bancoTemporario.toString());
        connectionFactory = new ConnectionFactory();
    }

    @AfterEach
    void descartarBanco() throws Exception {
        System.clearProperty("livraria.db");
        Files.deleteIfExists(bancoTemporario);
    }

    @Test
    void deveConfirmarVendaValidaEReverterVendaInvalida() {
        VendaService servico = new VendaService(connectionFactory);
        int estoqueInicial = consultarInteiro("SELECT estoque FROM livro WHERE id = 1");
        int vendasIniciais = consultarInteiro("SELECT COUNT(*) FROM venda");
        int itensIniciais = consultarInteiro("SELECT COUNT(*) FROM item_venda");

        VendaResultado resultado = servico.registrarVenda(1L, 2);
        assertTrue(resultado.venda().id() > 0);
        assertEquals(estoqueInicial - 2, resultado.estoqueRestante());
        assertEquals(estoqueInicial - 2, consultarInteiro("SELECT estoque FROM livro WHERE id = 1"));
        assertEquals(vendasIniciais + 1, consultarInteiro("SELECT COUNT(*) FROM venda"));
        assertEquals(itensIniciais + 1, consultarInteiro("SELECT COUNT(*) FROM item_venda"));

        assertThrows(
                EstoqueInsuficienteException.class,
                () -> servico.registrarVenda(1L, 10_000));
        assertEquals(estoqueInicial - 2, consultarInteiro("SELECT estoque FROM livro WHERE id = 1"));
        assertEquals(vendasIniciais + 1, consultarInteiro("SELECT COUNT(*) FROM venda"));
        assertEquals(itensIniciais + 1, consultarInteiro("SELECT COUNT(*) FROM item_venda"));

        assertThrows(IllegalArgumentException.class, () -> servico.registrarVenda(1L, 0));
    }

    private int consultarInteiro(String sql) {
        try (Connection connection = connectionFactory.obterConexao();
             var statement = connection.createStatement();
             var resultSet = statement.executeQuery(sql)) {
            resultSet.next();
            return resultSet.getInt(1);
        } catch (Exception exception) {
            throw new IllegalStateException("Falha ao consultar banco de teste", exception);
        }
    }
}
