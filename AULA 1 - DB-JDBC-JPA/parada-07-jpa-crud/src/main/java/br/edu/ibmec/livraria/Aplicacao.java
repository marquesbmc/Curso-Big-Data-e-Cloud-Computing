package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityTransaction;
import java.math.BigDecimal;

public class Aplicacao {
    public static void main(String[] args) {
        try (JPAUtil jpa = new JPAUtil();
             EntityManager entityManager = jpa.criarEntityManager()) {

            Livro livro = new Livro(
                    "JPA na Pratica",
                    "9789999000020",
                    new BigDecimal("54.90"),
                    6,
                    1L);

            // ESTADO NOVO/TRANSIENTE: o objeto existe apenas na memoria. Ele ainda
            // nao tem ID e nao pertence ao contexto do EntityManager.
            System.out.println("[1] Novo e gerenciado: " + entityManager.contains(livro));

            // RESOURCE_LOCAL exige controle explicito da transacao para escritas.
            EntityTransaction transacao = entityManager.getTransaction();
            try {
                transacao.begin();

                // ESTADO GERENCIADO: persist associa o objeto ao contexto. Com
                // IDENTITY, o INSERT ocorre cedo para que o ID seja recuperado.
                entityManager.persist(livro);
                System.out.println("[2] Apos persist e gerenciado: " + entityManager.contains(livro));
                transacao.commit();
            } catch (RuntimeException exception) {
                // Uma transacao que falhou nao deve permanecer ativa.
                if (transacao.isActive()) {
                    transacao.rollback();
                }
                throw exception;
            }

            Long id = livro.getId();
            System.out.println("    Inserido: " + livro);

            // clear destaca todas as entidades que estavam no contexto.
            // ESTADO DESTACADO/DETACHED: o objeto continua existindo, mas suas
            // proximas alteracoes nao serao sincronizadas automaticamente.
            entityManager.clear();
            System.out.println("[3] Apos clear e gerenciado: " + entityManager.contains(livro));

            // find executa SELECT e devolve outra instancia gerenciada.
            Livro encontrado = entityManager.find(Livro.class, id);
            System.out.println("[4] Encontrado e gerenciado: " + entityManager.contains(encontrado));

            try {
                transacao.begin();
                encontrado.atualizar("JPA atualizado", new BigDecimal("59.90"), 8);
                // Nao chamamos um metodo update: o commit sincroniza a mudanca.
                // Esse mecanismo e chamado dirty checking.
                transacao.commit();
            } catch (RuntimeException exception) {
                if (transacao.isActive()) {
                    transacao.rollback();
                }
                throw exception;
            }
            System.out.println("[5] Atualizado por dirty checking: " + encontrado);

            try {
                transacao.begin();

                // ESTADO REMOVIDO: remove agenda o DELETE. A exclusao se torna
                // definitiva apenas quando a transacao confirma o commit.
                entityManager.remove(encontrado);
                transacao.commit();
            } catch (RuntimeException exception) {
                if (transacao.isActive()) {
                    transacao.rollback();
                }
                throw exception;
            }
            System.out.println("[6] Busca apos exclusao: " + entityManager.find(Livro.class, id));
        }
    }
}
