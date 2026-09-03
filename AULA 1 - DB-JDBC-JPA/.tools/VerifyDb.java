import java.sql.*;
public class VerifyDb {
    public static void main(String[] args) throws Exception {
        String url = "jdbc:sqlite:" + args[0];
        try (Connection conn = DriverManager.getConnection(url)) {
            DatabaseMetaData dbm = conn.getMetaData();
            String[] tables = {"autor", "livro", "venda", "item_venda"};
            for (String table : tables) {
                try (ResultSet rs = dbm.getTables(null, null, table, null)) {
                    if (rs.next()) {
                        System.out.println("Table " + table + " exists.");
                    } else {
                        System.out.println("Table " + table + " does NOT exist.");
                    }
                }
            }
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM autor")) {
                if (rs.next()) {
                    System.out.println("autor has " + rs.getInt(1) + " rows.");
                }
            }
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM livro")) {
                if (rs.next()) {
                    System.out.println("livro has " + rs.getInt(1) + " rows.");
                }
            }
        }
    }
}
