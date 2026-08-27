package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

// Mantem uma unica EntityManagerFactory e oferece EntityManagers para as
// unidades de trabalho. A fabrica e pesada; o EntityManager e leve e descartavel.
public final class JPAUtil implements AutoCloseable {
    // Liga esta classe a configuracao <persistence-unit name="livraria">.
    private static final String UNIDADE_PERSISTENCIA = "livraria";

    // Testes sobrescrevem este valor com -Dlivraria.db ou System.setProperty.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    private static final String ARQUIVO_PADRAO = "livraria.db";

    private final EntityManagerFactory entityManagerFactory;

    public JPAUtil() {
        // Resolver o caminho absoluto evita que o resultado dependa de mudancas
        // posteriores no diretorio de trabalho do processo.
        Path arquivoBanco = localizarArquivoBanco();

        // Propriedades fornecidas na inicializacao tem precedencia sobre o XML.
        Map<String, Object> propriedades = Map.of(
                "jakarta.persistence.jdbc.url",
                "jdbc:sqlite:" + arquivoBanco);
        entityManagerFactory = Persistence.createEntityManagerFactory(
                UNIDADE_PERSISTENCIA,
                propriedades);
    }

    public EntityManager criarEntityManager() {
        // Um EntityManager mantem seu proprio contexto de persistencia e nao e
        // seguro para uso concorrente. Abra, use e feche por unidade de trabalho.
        return entityManagerFactory.createEntityManager();
    }

    private Path localizarArquivoBanco() {
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();

        // Sem esta verificacao, uma grafia incorreta criaria um SQLite vazio.
        if (!Files.isRegularFile(arquivoBanco)) {
            throw new IllegalStateException("Banco SQLite nao encontrado: " + arquivoBanco);
        }
        return arquivoBanco;
    }

    @Override
    public void close() {
        // Normalmente a fabrica vive durante toda a aplicacao e fecha no encerramento.
        entityManagerFactory.close();
    }
}
