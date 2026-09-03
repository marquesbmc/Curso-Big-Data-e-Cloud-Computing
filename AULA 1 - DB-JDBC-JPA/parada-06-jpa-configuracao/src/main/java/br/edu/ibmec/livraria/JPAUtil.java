package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

// Centraliza a inicializacao do JPA para que as demais classes nao precisem
// conhecer persistence.xml, URL JDBC ou EntityManagerFactory.
public final class JPAUtil implements AutoCloseable {
    // Este nome deve ser igual ao atributo name do persistence-unit.
    private static final String UNIDADE_PERSISTENCIA = "livraria";

    // A propriedade de sistema permite que os testes usem uma copia temporaria.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    private static final String ARQUIVO_PADRAO = "livraria.db";

    // EntityManagerFactory e um objeto caro. A aplicacao cria apenas uma fabrica
    // e a reutiliza para produzir EntityManagers leves.
    private final EntityManagerFactory entityManagerFactory;

    public JPAUtil() {
        // Validamos o caminho antes de inicializar o Hibernate. Sem essa validacao,
        // o SQLite criaria silenciosamente outro arquivo de banco vazio.
        Path arquivoBanco = localizarArquivoBanco();

        // Esta propriedade sobrescreve a URL padrao do persistence.xml. Assim a
        // aplicacao usa livraria.db e os testes podem apontar para outro arquivo.
        Map<String, Object> propriedades = Map.of(
                "jakarta.persistence.jdbc.url",
                "jdbc:sqlite:" + arquivoBanco);

        // O nome deve corresponder ao persistence-unit do persistence.xml.
        entityManagerFactory = Persistence.createEntityManagerFactory(
                UNIDADE_PERSISTENCIA,
                propriedades);
    }

    public EntityManager criarEntityManager() {
        // Cada unidade de trabalho abre seu proprio EntityManager.
        // EntityManager nao deve ser compartilhado entre threads.
        return entityManagerFactory.createEntityManager();
    }

    private Path localizarArquivoBanco() {
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();

        // SQLite criaria um banco vazio se o caminho estivesse errado.
        if (!Files.isRegularFile(arquivoBanco)) {
            throw new IllegalStateException("Banco SQLite nao encontrado: " + arquivoBanco);
        }
        return arquivoBanco;
    }

    @Override
    public void close() {
        // Fechar a fabrica libera conexoes e outros recursos mantidos pelo provedor.
        entityManagerFactory.close();
    }
}
