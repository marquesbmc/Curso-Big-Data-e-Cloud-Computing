package br.edu.ibmec.livraria;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import jakarta.persistence.EntityManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.sql.DriverManager;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class JPATransacoesTest {
    private Path bancoTemporario;

    @BeforeEach
    void prepararBanco() throws Exception {
        // Vendas alteram tres tabelas; a copia temporaria protege o banco da aula.
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
    void deveConfirmarVendaEReverterFalha() {
        try (JPAUtil jpa = new JPAUtil()) {
            VendaService servico = new VendaService(jpa);
            int estoqueInicial = servico.consultarEstoque(1L);
            long vendasIniciais = contarLinhas("venda");
            long itensIniciais = contarLinhas("item_venda");

            // Caminho de commit: venda e item recebem IDs e o estoque diminui.
            VendaResultado resultado = servico.registrarVenda(1L, 2);
            assertEquals(estoqueInicial - 2, resultado.estoqueRestante());

            try (EntityManager entityManager = jpa.criarEntityManager()) {
                // find comprova que as duas insercoes foram confirmadas no banco.
                assertNotNull(entityManager.find(Venda.class, resultado.vendaId()));
                assertNotNull(entityManager.find(ItemVenda.class, resultado.itemVendaId()));
            }
            assertEquals(vendasIniciais + 1, contarLinhas("venda"));
            assertEquals(itensIniciais + 1, contarLinhas("item_venda"));

            // Caminho de rollback: a falha ocorre depois do SQL ter sido enviado.
            assertThrows(
                    IllegalStateException.class,
                    () -> servico.demonstrarRollback(1L, 1));
            assertEquals(estoqueInicial - 2, servico.consultarEstoque(1L));
            assertEquals(vendasIniciais + 1, contarLinhas("venda"));
            assertEquals(itensIniciais + 1, contarLinhas("item_venda"));

            // Uma regra de negocio tambem deve abortar a transacao sem mudar estoque.
            assertThrows(
                    EstoqueInsuficienteException.class,
                    () -> servico.registrarVenda(1L, 10_000));
            assertEquals(estoqueInicial - 2, servico.consultarEstoque(1L));
        }
    }

    private long contarLinhas(String tabela) {
        // Os nomes sao constantes internas do teste; nenhum dado externo compoe o SQL.
        String sql = "SELECT COUNT(*) FROM " + tabela;
        try (var connection = DriverManager.getConnection("jdbc:sqlite:" + bancoTemporario);
             var statement = connection.createStatement();
             var resultSet = statement.executeQuery(sql)) {
            resultSet.next();
            return resultSet.getLong(1);
        } catch (Exception exception) {
            throw new IllegalStateException("Falha ao contar " + tabela, exception);
        }
    }
}
