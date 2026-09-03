package br.edu.ibmec.livraria;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

// Venda e a raiz do agregado persistido. Ela controla a composicao dos itens e
// calcula o total para impedir divergencia entre itens e valor_total.
@Entity
@Table(name = "venda")
public class Venda {
    // SQLite gera o ID no primeiro INSERT da venda.
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "data_hora", nullable = false)
    // O conversor e necessario porque a coluna existente e TEXT.
    @Convert(converter = LocalDateTimeStringConverter.class)
    private LocalDateTime dataHora;

    @Column(name = "valor_total", nullable = false)
    // Comecar em zero simplifica a soma incremental dos itens.
    private BigDecimal valorTotal = BigDecimal.ZERO;

    // Persistir a venda tambem persiste os itens adicionados a colecao.
    // mappedBy aponta para ItemVenda.venda, que controla a coluna venda_id.
    // orphanRemoval removeria do banco um item retirado desta colecao gerenciada.
    @OneToMany(mappedBy = "venda", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ItemVenda> itens = new ArrayList<>();

    protected Venda() {
    }

    // A aplicacao informa apenas o instante; ID e total surgem depois.
    public Venda(LocalDateTime dataHora) {
        this.dataHora = dataHora;
    }

    public ItemVenda adicionarItem(Livro livro, int quantidade) {
        // O construtor recebe this para manter os dois lados sincronizados:
        // a venda conhece o item e o item conhece sua venda.
        ItemVenda item = new ItemVenda(this, livro, quantidade, livro.getPreco());
        itens.add(item);

        // O preco usado e o valor atual do livro multiplicado pela quantidade.
        valorTotal = valorTotal.add(
                livro.getPreco().multiply(BigDecimal.valueOf(quantidade)));
        return item;
    }

    public Long getId() {
        return id;
    }

    public LocalDateTime getDataHora() {
        return dataHora;
    }

    public BigDecimal getValorTotal() {
        return valorTotal;
    }

    public List<ItemVenda> getItens() {
        // O acesso pode inicializar a colecao quando a Venda veio do banco.
        return itens;
    }
}
