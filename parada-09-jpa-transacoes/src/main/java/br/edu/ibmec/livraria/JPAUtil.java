package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

// Ponto unico de inicializacao do JPA. O service pede EntityManagers a esta
// classe, mas nao precisa conhecer URL, driver, dialeto ou persistence.xml.
public final class JPAUtil implements AutoCloseable {
    // Deve coincidir com o name da unidade declarada no XML.
    private static final String UNIDADE_PERSISTENCIA = "livraria";

    // A propriedade permite trocar somente o arquivo, sem alterar a configuracao.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    private static final String ARQUIVO_PADRAO = "livraria.db";

    // A fabrica e compartilhada; cada operacao cria seu proprio EntityManager.
    private final EntityManagerFactory entityManagerFactory;

    public JPAUtil() {
        Path arquivoBanco = localizarArquivoBanco();

        // O mapa tem precedencia sobre a URL relativa escrita no persistence.xml.
        Map<String, Object> propriedades = Map.of(
                "jakarta.persistence.jdbc.url",
                "jdbc:sqlite:" + arquivoBanco);
        entityManagerFactory = Persistence.createEntityManagerFactory(
                UNIDADE_PERSISTENCIA,
                propriedades);
    }

    public EntityManager criarEntityManager() {
        // EntityManager delimita um contexto de persistencia e nao e thread-safe.
        return entityManagerFactory.createEntityManager();
    }

    private Path localizarArquivoBanco() {
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();

        // A verificacao evita que SQLite crie um arquivo vazio por engano.
        if (!Files.isRegularFile(arquivoBanco)) {
            throw new IllegalStateException("Banco SQLite nao encontrado: " + arquivoBanco);
        }
        return arquivoBanco;
    }

    @Override
    public void close() {
        // Libera o pool interno e todos os recursos pertencentes ao provedor.
        entityManagerFactory.close();
    }
}
