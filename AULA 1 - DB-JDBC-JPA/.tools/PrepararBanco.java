import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.Statement;

public class PrepararBanco {
    public static void main(String[] args) throws Exception {
        Path destino = Path.of(args[0]).toAbsolutePath();
        Files.createDirectories(destino.getParent());
        Files.deleteIfExists(destino);

        try (Connection connection = DriverManager.getConnection("jdbc:sqlite:" + destino)) {
            try (Statement statement = connection.createStatement()) {
                statement.executeUpdate("CREATE TABLE autor (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL)");
                statement.executeUpdate("CREATE TABLE livro (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, isbn TEXT NOT NULL UNIQUE, preco NUMERIC NOT NULL, estoque INTEGER NOT NULL, autor_id INTEGER NOT NULL, FOREIGN KEY (autor_id) REFERENCES autor(id))");
                statement.executeUpdate("CREATE TABLE venda (id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT NOT NULL, valor_total NUMERIC NOT NULL)");
                statement.executeUpdate("CREATE TABLE item_venda (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER NOT NULL, livro_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, preco_unitario NUMERIC NOT NULL, FOREIGN KEY (venda_id) REFERENCES venda(id), FOREIGN KEY (livro_id) REFERENCES livro(id))");
            }

            inserirAutores(connection);
            inserirLivros(connection);
        }
    }

    private static void inserirAutores(Connection connection) throws Exception {
        try (PreparedStatement statement = connection.prepareStatement("INSERT INTO autor (nome) VALUES (?)")) {
            for (String nome : new String[] {"Machado de Assis", "Clarice Lispector", "Jorge Amado", "Carolina Maria de Jesus"}) {
                statement.setString(1, nome);
                statement.executeUpdate();
            }
        }
    }

    private static void inserirLivros(Connection connection) throws Exception {
        Object[][] livros = {
                {"Dom Casmurro", "9780000000001", "39.90", 12, 1},
                {"Memorias Postumas de Bras Cubas", "9780000000002", "44.50", 8, 1},
                {"A Hora da Estrela", "9780000000003", "35.00", 15, 2},
                {"Perto do Coracao Selvagem", "9780000000004", "48.90", 6, 2},
                {"Capitaes da Areia", "9780000000005", "42.00", 20, 3},
                {"Dona Flor e Seus Dois Maridos", "9780000000006", "52.75", 5, 3},
                {"Quarto de Despejo", "9780000000007", "37.40", 10, 4},
                {"Casa de Alvenaria", "9780000000008", "46.20", 7, 4}
        };
        try (PreparedStatement statement = connection.prepareStatement("INSERT INTO livro (titulo, isbn, preco, estoque, autor_id) VALUES (?, ?, ?, ?, ?)")) {
            for (Object[] livro : livros) {
                statement.setString(1, (String) livro[0]);
                statement.setString(2, (String) livro[1]);
                statement.setBigDecimal(3, new BigDecimal((String) livro[2]));
                statement.setInt(4, (Integer) livro[3]);
                statement.setInt(5, (Integer) livro[4]);
                statement.executeUpdate();
            }
        }
    }
}