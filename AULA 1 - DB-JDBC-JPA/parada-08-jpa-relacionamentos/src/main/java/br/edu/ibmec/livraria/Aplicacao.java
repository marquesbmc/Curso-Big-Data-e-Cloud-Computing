package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;
import jakarta.persistence.Persistence;

public class Aplicacao {
    public static void main(String[] args) {
        // O EntityManager deve permanecer aberto durante toda a navegacao lazy.
        try (JPAUtil jpa = new JPAUtil();
             EntityManager entityManager = jpa.criarEntityManager()) {

            // find carrega apenas a linha de autor. A colecao nao faz parte deste SELECT.
            Autor autor = entityManager.find(Autor.class, 1L);
            System.out.println("[1] Autor: " + autor.getNome());

            // A colecao ainda nao foi consultada porque o relacionamento e lazy.
            // PersistenceUtil verifica o estado sem forcar a inicializacao.
            System.out.println("[2] Livros carregados antes do acesso: " +
                    Persistence.getPersistenceUtil().isLoaded(autor, "livros"));

            // A primeira navegacao pela colecao dispara um SELECT adicional.
            // O Hibernate usa autor_id para localizar apenas os livros deste autor.
            for (Livro livro : autor.getLivros()) {
                System.out.println("    - " + livro.getTitulo());
            }
            System.out.println("[3] Livros carregados depois do acesso: " +
                    Persistence.getPersistenceUtil().isLoaded(autor, "livros"));

            // Agora percorremos o caminho inverso: Livro -> Autor.
            Livro livro = entityManager.find(Livro.class, 3L);
            System.out.println("[4] Livro: " + livro.getTitulo());

            // getAutor devolve a referencia associada. getNome exige os dados do
            // autor e pode disparar outro SELECT quando o proxy ainda esta lazy.
            System.out.println("[5] Autor do livro: " + livro.getAutor().getNome());
        }
    }
}
