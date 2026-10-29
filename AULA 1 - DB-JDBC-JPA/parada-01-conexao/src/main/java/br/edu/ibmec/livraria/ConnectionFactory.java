package br.edu.ibmec.livraria;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.nio.file.Files;
import java.nio.file.Path;

// Centraliza a criacao de conexoes. Se a URL ou o driver mudar, as classes que
// usam o banco continuam chamando somente obterConexao().
public class ConnectionFactory {
    // Permite que os testes apontem para uma copia temporaria do banco.
    private static final String PROPRIEDADE_ARQUIVO = "livraria.db";

    // Quando nenhuma propriedade e informada, o arquivo e procurado na pasta
    // a partir da qual a aplicacao foi executada.
    private static final String ARQUIVO_PADRAO = "livraria.db";

    // O prefixo jdbc:sqlite permite ao DriverManager escolher o driver correto.
    private static final String PREFIXO_URL_SQLITE = "jdbc:sqlite:";

    public Connection obterConexao() throws SQLException {
        // Primeiro separamos a localizacao do arquivo da abertura da conexao.
        Path arquivoBanco = localizarArquivoBanco();
        String url = PREFIXO_URL_SQLITE + arquivoBanco;

        // A URL informa ao DriverManager qual driver e qual arquivo devem ser usados.
        // O driver SQLite e descoberto automaticamente pelo mecanismo Service Provider.
        // A Connection aberta aqui deve ser fechada por quem a utiliza, com try-with-resources.
        return DriverManager.getConnection(url);
    }

    private Path localizarArquivoBanco() throws SQLException {
        // System.getProperty usa o valor configurado ou o nome padrao como fallback.
        String arquivoConfigurado = System.getProperty(PROPRIEDADE_ARQUIVO, ARQUIVO_PADRAO);

        // Caminho absoluto e normalizado torna mensagens e diagnosticos mais claros.
        Path arquivoBanco = Path.of(arquivoConfigurado).toAbsolutePath().normalize();

        // Evita criar por engano um banco SQLite vazio quando o caminho estiver errado.
        if (!Files.isRegularFile(arquivoBanco)) {
            throw new SQLException("Banco SQLite nao encontrado: " + arquivoBanco);
        }
        return arquivoBanco;
    }
}
