package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

// Infraestrutura minima para iniciar JPA fora de um servidor de aplicacao.
// As entidades dependem apenas de JPA, sem conhecer esta classe utilitaria.
public final class JPAUtil implements AutoCloseable {
    // Nome logico definido no persistence.xml.
    private static final String UNIDADE_PERSISTENCIA = "livraria";

    // Caminho configuravel para permitir testes em bancos temporarios.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    private static final String ARQUIVO_PADRAO = "livraria.db";

    // Uma fabrica atende toda a execucao; criar uma para cada consulta seria caro.
    private final EntityManagerFactory entityManagerFactory;

    public JPAUtil() {
        Path arquivoBanco = localizarArquivoBanco();

        // O mapa sobrescreve somente a URL; as outras opcoes continuam vindo do XML.
        Map<String, Object> propriedades = Map.of(
                "jakarta.persistence.jdbc.url",
                "jdbc:sqlite:" + arquivoBanco);
        entityManagerFactory = Persistence.createEntityManagerFactory(
                UNIDADE_PERSISTENCIA,
                propriedades);
    }

    public EntityManager criarEntityManager() {
        // O contexto de persistencia vive dentro deste EntityManager. Proxies e
        // colecoes lazy precisam dele aberto para buscar dados ainda nao carregados.
        return entityManagerFactory.createEntityManager();
    }

    private Path localizarArquivoBanco() {
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();

        // Evita confundir um caminho incorreto com um banco valido sem tabelas.
        if (!Files.isRegularFile(arquivoBanco)) {
            throw new IllegalStateException("Banco SQLite nao encontrado: " + arquivoBanco);
        }
        return arquivoBanco;
    }

    @Override
    public void close() {
        // O fechamento da fabrica ocorre uma vez, no encerramento da aplicacao.
        entityManagerFactory.close();
    }
}
