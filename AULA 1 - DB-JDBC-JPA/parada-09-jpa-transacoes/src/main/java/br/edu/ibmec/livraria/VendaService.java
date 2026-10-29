package br.edu.ibmec.livraria;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityTransaction;
import java.time.LocalDateTime;

// Coordena a unidade de trabalho da venda. Regras ficam nas entidades; abertura,
// confirmacao e cancelamento da transacao ficam neste service.
public class VendaService {
    // JPAUtil e compartilhado e fornece um novo EntityManager por operacao.
    private final JPAUtil jpa;

    public VendaService(JPAUtil jpa) {
        this.jpa = jpa;
    }

    public VendaResultado registrarVenda(long livroId, int quantidade) {
        // Caminho normal: toda a unidade de trabalho termina em commit.
        return executarVenda(livroId, quantidade, false);
    }

    public void demonstrarRollback(long livroId, int quantidade) {
        // Caminho didatico: executa o mesmo fluxo, mas falha depois do flush.
        executarVenda(livroId, quantidade, true);
    }

    private VendaResultado executarVenda(
            long livroId,
            int quantidade,
            boolean simularFalhaDepoisDoFlush) {
        try (EntityManager entityManager = jpa.criarEntityManager()) {
            // EntityTransaction pertence a este EntityManager e controla a mesma
            // conexao usada por todos os comandos da unidade de trabalho.
            EntityTransaction transacao = entityManager.getTransaction();

            try {
                // Escritas JPA exigem uma transacao ativa.
                transacao.begin();

                // find devolve uma entidade gerenciada dentro deste contexto.
                Livro livro = entityManager.find(Livro.class, livroId);
                if (livro == null) {
                    throw new IllegalArgumentException("Livro inexistente: " + livroId);
                }

                livro.retirarDoEstoque(quantidade);

                // Venda e ItemVenda ainda sao objetos novos neste momento.
                Venda venda = new Venda(LocalDateTime.now());
                ItemVenda item = venda.adicionarItem(livro, quantidade);

                // CascadeType.ALL faz o persist alcancar ItemVenda.
                // A entidade Livro nao e persistida novamente porque ja e gerenciada.
                entityManager.persist(venda);

                if (simularFalhaDepoisDoFlush) {
                    // flush envia INSERTs e UPDATE ao banco sem confirmar a transacao.
                    // A excecao seguinte permite observar o rollback desfazendo SQL ja executado.
                    entityManager.flush();
                    throw new IllegalStateException("Falha simulada depois do flush");
                }

                transacao.commit();

                // Depois do commit os IDs gerados ja estao disponiveis nos objetos.
                return new VendaResultado(
                        venda.getId(),
                        item.getId(),
                        livro.getEstoque());
            } catch (RuntimeException exception) {
                if (transacao.isActive()) {
                    // O rollback descarta tanto entidades novas quanto mudancas no estoque.
                    transacao.rollback();
                }
                // Relancamos para que a camada chamadora saiba por que a venda falhou.
                throw exception;
            }
        }
    }

    public int consultarEstoque(long livroId) {
        // Leitura simples nao altera estado e, neste exemplo RESOURCE_LOCAL, nao
        // precisa abrir transacao explicita.
        try (EntityManager entityManager = jpa.criarEntityManager()) {
            Livro livro = entityManager.find(Livro.class, livroId);
            if (livro == null) {
                throw new IllegalArgumentException("Livro inexistente: " + livroId);
            }
            return livro.getEstoque();
        }
    }
}
