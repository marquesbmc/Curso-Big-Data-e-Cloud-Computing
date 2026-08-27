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

// ItemVenda materializa a ligacao entre uma venda e um livro. Alem das chaves,
// guarda quantidade e preco praticado no momento da operacao.
@Entity
@Table(name = "item_venda")
public class ItemVenda {
    // Cada item possui identidade propria na tabela item_venda.
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // Este e o lado dono do relacionamento porque contem venda_id.
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "venda_id", nullable = false)
    private Venda venda;

    // Muitos itens, inclusive de vendas diferentes, podem apontar ao mesmo livro.
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "livro_id", nullable = false)
    private Livro livro;

    @Column(nullable = false)
    private int quantidade;

    // Guardar uma copia do preco preserva o historico mesmo que Livro.preco mude.
    @Column(name = "preco_unitario", nullable = false)
    private BigDecimal precoUnitario;

    protected ItemVenda() {
    }

    // O construtor exige todas as informacoes que tornam um item valido.
    public ItemVenda(Venda venda, Livro livro, int quantidade, BigDecimal precoUnitario) {
        this.venda = venda;
        this.livro = livro;
        this.quantidade = quantidade;
        this.precoUnitario = precoUnitario;
    }

    public Long getId() {
        return id;
    }

    public Venda getVenda() {
        return venda;
    }

    public Livro getLivro() {
        return livro;
    }

    public int getQuantidade() {
        return quantidade;
    }

    public BigDecimal getPrecoUnitario() {
        return precoUnitario;
    }
}
