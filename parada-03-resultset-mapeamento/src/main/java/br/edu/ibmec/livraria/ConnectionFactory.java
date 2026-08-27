package br.edu.ibmec.livraria;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.nio.file.Files;
import java.nio.file.Path;

// Fornece conexoes prontas para as classes de consulta e cadastro, mantendo
// caminho, prefixo JDBC e DriverManager em um unico lugar.
public class ConnectionFactory {
    // Permite que os testes apontem para uma copia temporaria do banco.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    private static final String ARQUIVO_PADRAO = "livraria.db";
    private static final String PREFIXO_URL_SQLITE = "jdbc:sqlite:";

    public Connection obterConexao() throws SQLException {
        // Uma nova Connection e aberta por operacao e fechada por quem a recebe.
        Path arquivoBanco = localizarArquivoBanco();
        String url = PREFIXO_URL_SQLITE + arquivoBanco;

        // DriverManager escolhe o driver JDBC compativel com a URL.
        // O driver SQLite e descoberto automaticamente pelo mecanismo Service Provider.
        // Quem recebe esta Connection deve fecha-la com try-with-resources.
        return DriverManager.getConnection(url);
    }

    private Path localizarArquivoBanco() throws SQLException {
        // O valor alternativo e usado pelos testes para trabalhar em uma copia.
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();
        // Evita criar por engano um banco SQLite vazio quando o caminho estiver errado.
        if (!Files.isRegularFile(arquivoBanco)) throw new SQLException("Banco SQLite nao encontrado: " + arquivoBanco);
        return arquivoBanco;
    }
}
