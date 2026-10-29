package br.edu.ibmec.livraria;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.nio.file.Files;
import java.nio.file.Path;

// Abre a conexao que VendaService reutiliza durante toda a transacao. A fabrica
// nao inicia commit ou rollback; essa decisao pertence ao service.
public class ConnectionFactory {
    // Permite que os testes apontem para uma copia temporaria do banco.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    private static final String ARQUIVO_PADRAO = "livraria.db";
    private static final String PREFIXO_URL_SQLITE = "jdbc:sqlite:";

    public Connection obterConexao() throws SQLException {
        // Uma chamada cria uma sessao JDBC independente com o SQLite.
        Path arquivoBanco = localizarArquivoBanco();
        String url = PREFIXO_URL_SQLITE + arquivoBanco;

        // DriverManager escolhe o driver JDBC compativel com a URL.
        // O driver SQLite e descoberto automaticamente pelo mecanismo Service Provider.
        // VendaService mantem esta mesma Connection durante toda a transacao.
        return DriverManager.getConnection(url);
    }

    private Path localizarArquivoBanco() throws SQLException {
        // Testes podem apontar esta fabrica para um arquivo temporario.
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();
        // Evita criar por engano um banco SQLite vazio quando o caminho estiver errado.
        if (!Files.isRegularFile(arquivoBanco)) throw new SQLException("Banco SQLite nao encontrado: " + arquivoBanco);
        return arquivoBanco;
    }
}
