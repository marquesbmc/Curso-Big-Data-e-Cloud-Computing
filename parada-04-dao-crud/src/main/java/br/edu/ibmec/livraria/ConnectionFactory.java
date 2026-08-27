package br.edu.ibmec.livraria;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.nio.file.Files;
import java.nio.file.Path;

// Cria conexoes para o DAO. A fabrica nao guarda estado de uma operacao e pode
// ser reutilizada por todos os metodos CRUD.
public class ConnectionFactory {
    // Permite que os testes apontem para uma copia temporaria do banco.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";
    private static final String ARQUIVO_PADRAO = "livraria.db";
    private static final String PREFIXO_URL_SQLITE = "jdbc:sqlite:";

    public Connection obterConexao() throws SQLException {
        // Nesta parada cada metodo do DAO abre sua propria Connection.
        Path arquivoBanco = localizarArquivoBanco();
        String url = PREFIXO_URL_SQLITE + arquivoBanco;

        // DriverManager escolhe o driver JDBC compativel com a URL.
        // O driver SQLite e descoberto automaticamente pelo mecanismo Service Provider.
        // Cada metodo do DAO recebe uma Connection nova e a fecha com try-with-resources.
        return DriverManager.getConnection(url);
    }

    private Path localizarArquivoBanco() throws SQLException {
        // A propriedade de sistema permite redirecionar testes para outro arquivo.
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();
        // Evita criar por engano um banco SQLite vazio quando o caminho estiver errado.
        if (!Files.isRegularFile(arquivoBanco)) throw new SQLException("Banco SQLite nao encontrado: " + arquivoBanco);
        return arquivoBanco;
    }
}
