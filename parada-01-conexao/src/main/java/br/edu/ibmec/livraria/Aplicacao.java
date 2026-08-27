package br.edu.ibmec.livraria;

import java.sql.Connection;
import java.sql.SQLException;

public class Aplicacao {
    public static void main(String[] args) {
        // A fabrica sabe como localizar o banco e construir a URL JDBC.
        ConnectionFactory connectionFactory = new ConnectionFactory();
        System.out.println("[1] Abrindo conexao com o banco da livraria");

        // O try-with-resources chama connection.close() automaticamente ao final
        // do bloco, inclusive quando uma SQLException interrompe a execucao.
        try (Connection connection = connectionFactory.obterConexao()) {
            // Neste ponto existe uma sessao JDBC aberta com o arquivo SQLite.
            // Os metadados permitem inspecionar o driver e a URL da conexao aberta.
            System.out.println("[2] Conexao aberta: " + !connection.isClosed());
            System.out.println("[3] Driver: " + connection.getMetaData().getDriverName());
            System.out.println("    URL: " + connection.getMetaData().getURL());
        } catch (SQLException exception) {
            // Nesta primeira parada apenas apresentamos a falha ao usuario.
            System.err.println("[2] Falha ao conectar: " + exception.getMessage());
        }

        // Esta linha ocorre depois do fechamento automatico do recurso.
        System.out.println("[4] Conexao fechada");
    }
}
