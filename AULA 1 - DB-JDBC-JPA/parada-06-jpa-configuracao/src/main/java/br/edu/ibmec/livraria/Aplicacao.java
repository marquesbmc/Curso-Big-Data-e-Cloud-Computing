package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;

public class Aplicacao {
    public static void main(String[] args) {
        // JPAUtil fecha a fabrica e EntityManager fecha a unidade de trabalho.
        // O try-with-resources garante ambos os fechamentos mesmo quando ha falha.
        try (JPAUtil jpa = new JPAUtil();
             EntityManager entityManager = jpa.criarEntityManager()) {

            // find procura pela chave primaria e devolve null quando nao encontra.
            // O primeiro argumento informa o tipo da entidade; o segundo e o ID.
            System.out.println("[1] Buscando entidades pela chave primaria");
            Livro encontrado = entityManager.find(Livro.class, 1L);
            Livro inexistente = entityManager.find(Livro.class, 999L);

            // O objeto encontrado esta gerenciado enquanto o EntityManager estiver aberto.
            System.out.println("[2] Livro 1: " + encontrado);
            System.out.println("[3] Livro inexistente: " + inexistente);
        }
    }
}
