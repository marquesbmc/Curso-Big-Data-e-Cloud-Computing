package br.edu.ibmec.livraria;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.nio.file.Files;
import java.nio.file.Path;

// Fabrica responsavel por esconder URL, caminho do arquivo e DriverManager das
// classes que executam comandos SQL.
public class ConnectionFactory {
    // Permite que os testes apontem para uma copia temporaria do banco.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    // O caminho relativo e resolvido a partir da pasta atual do processo.
    private static final String ARQUIVO_PADRAO = "livraria.db";
    private static final String PREFIXO_URL_SQLITE = "jdbc:sqlite:";

    public Connection obterConexao() throws SQLException {
        // Cada chamada devolve uma nova sessao JDBC com o banco.
        Path arquivoBanco = localizarArquivoBanco();
        String url = PREFIXO_URL_SQLITE + arquivoBanco;

        // DriverManager escolhe o driver JDBC compativel com a URL.
        // O driver SQLite e descoberto automaticamente pelo mecanismo Service Provider.
        // Quem recebe esta Connection deve fecha-la com try-with-resources.
        return DriverManager.getConnection(url);
    }

    private Path localizarArquivoBanco() throws SQLException {
        // Testes podem sobrescrever o arquivo sem mudar o codigo de producao.
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();

        // Evita criar por engano um banco SQLite vazio quando o caminho estiver errado.
        if (!Files.isRegularFile(arquivoBanco)) {
            throw new SQLException("Banco SQLite nao encontrado: " + arquivoBanco);
        }
        return arquivoBanco;
    }
}
