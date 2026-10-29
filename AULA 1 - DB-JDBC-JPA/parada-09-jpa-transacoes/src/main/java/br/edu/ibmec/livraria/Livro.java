package br.edu.ibmec.livraria;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;

// Livro e uma entidade existente que participa da venda. Nao chamamos persist
// para ela: find a coloca no estado gerenciado e o dirty checking cuida do UPDATE.
@Entity
@Table(name = "livro")
public class Livro {
    // O wrapper Long tambem permite distinguir uma entidade nova com ID nulo.
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String titulo;

    @Column(nullable = false, unique = true)
    private String isbn;

    @Column(nullable = false)
    private BigDecimal preco;

    @Column(nullable = false)
    private int estoque;

    // O relacionamento e mantido para que o modelo JPA continue coerente com a
    // parada anterior. A venda nao precisa carregar o autor para baixar estoque.
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "autor_id", nullable = false)
    private Autor autor;

    protected Livro() {
    }

    public void retirarDoEstoque(int quantidade) {
        // Validacoes ficam no objeto que conhece a regra e o estado atual.
        if (quantidade <= 0) {
            throw new IllegalArgumentException("Quantidade deve ser positiva");
        }
        if (quantidade > estoque) {
            // Lancar antes da subtracao impede estoque negativo em memoria.
            throw new EstoqueInsuficienteException(
                    "Estoque insuficiente para " + titulo + ": disponivel=" + estoque);
        }

        // Como Livro esta gerenciado, esta mudanca produz UPDATE no commit.
        // Nenhuma chamada entityManager.merge ou update e necessaria aqui.
        estoque -= quantidade;
    }

    public Long getId() {
        return id;
    }

    public String getTitulo() {
        return titulo;
    }

    public BigDecimal getPreco() {
        return preco;
    }

    public int getEstoque() {
        return estoque;
    }

    public Autor getAutor() {
        return autor;
    }
}
