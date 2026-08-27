package br.edu.ibmec.livraria;

import java.math.BigDecimal;

public class Aplicacao {
    public static void main(String[] args) {
        // As classes recebem a fabrica por construtor, em vez de criarem a conexao
        // internamente. Isso deixa a dependencia visivel e facilita os testes.
        ConsultaLivro consultaLivro = new ConsultaLivro(new ConnectionFactory());
        CadastroLivro cadastroLivro = new CadastroLivro(new ConnectionFactory());

        // A aplicacao demonstra os dois usos mais comuns do PreparedStatement:
        // SELECT parametrizado e INSERT com recuperacao da chave gerada.
        System.out.println("[1] Consultando por ID");
        System.out.println("    Livro 1: " + consultaLivro.buscarPorId(1));
        System.out.println("[2] Consultando com LIKE");
        System.out.println("    Livros com 'Casa': " + consultaLivro.buscarPorParteDoTitulo("Casa"));

        // BigDecimal evita arredondamentos inadequados para valores monetarios.
        // O ISBN e unico; restaure o banco antes de repetir esta demonstracao.
        long id = cadastroLivro.inserir("Livro JDBC de Demonstracao", "9789999000001", new BigDecimal("29.90"), 3, 1);
        System.out.println("[3] Livro inserido com ID: " + id);
    }
}
