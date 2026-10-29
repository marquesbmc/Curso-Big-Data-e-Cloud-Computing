package br.edu.ibmec.livraria;

import java.math.BigDecimal;

public class Aplicacao {
    public static void main(String[] args) {
        // A aplicacao conversa com o DAO e nao precisa conhecer JDBC ou SQL.
        LivroDAO dao = new LivroDAO(new ConnectionFactory());

        // O roteiro abaixo percorre o CRUD completo sobre o mesmo livro:
        // Create, Read, Update e Delete.
        Livro inserido = dao.inserir(new Livro(
                // Zero indica que o objeto ainda nao recebeu identidade do banco.
                0,
                "CRUD JDBC",
                "9789999000010",
                new BigDecimal("25.00"),
                4,
                1));
        System.out.println("[1] CREATE: " + inserido);

        System.out.println("[2] READ por ID: " + dao.buscarPorId(inserido.id()));
        System.out.println("    Total de livros: " + dao.listarTodos().size());

        // Records sao imutaveis, por isso criamos outro Livro com os novos dados.
        // O ID preservado informa ao UPDATE qual linha deve ser alterada.
        Livro atualizado = new Livro(
                inserido.id(),
                "CRUD atualizado",
                inserido.isbn(),
                inserido.preco(),
                5,
                inserido.autorId());
        System.out.println("[3] UPDATE executado: " + dao.atualizar(atualizado));

        System.out.println("[4] DELETE executado: " + dao.excluir(inserido.id()));
        // A busca final deve produzir Optional.empty.
        System.out.println("[5] Busca apos DELETE: " + dao.buscarPorId(inserido.id()));
    }
}
