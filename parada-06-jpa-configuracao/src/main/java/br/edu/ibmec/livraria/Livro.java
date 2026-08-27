package br.edu.ibmec.livraria;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;

// @Entity faz a classe participar do contexto de persistencia. A partir daqui,
// objetos Livro podem ser carregados e acompanhados pelo EntityManager.
@Entity
// @Table e necessario porque queremos explicitar a tabela existente no SQLite.
@Table(name = "livro")
public class Livro {
    // Toda entidade JPA precisa de uma identidade. O campo corresponde a chave
    // primaria da tabela e diferencia um Livro persistente de todos os demais.
    @Id
    // IDENTITY informa que o valor e produzido pelo proprio banco no INSERT.
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // nullable=false documenta no modelo Java a restricao NOT NULL do esquema.
    @Column(nullable = false)
    private String titulo;

    // unique=true espelha a restricao UNIQUE existente para o ISBN.
    @Column(nullable = false, unique = true)
    private String isbn;

    // BigDecimal representa valores monetarios sem imprecisao de ponto flutuante.
    @Column(nullable = false)
    private BigDecimal preco;

    @Column(nullable = false)
    private int estoque;

    // O relacionamento com Autor sera apresentado apenas na parada 8.
    @Column(name = "autor_id", nullable = false)
    private Long autorId;

    // JPA precisa deste construtor para criar a entidade por reflexao.
    protected Livro() {
    }

    // Nesta parada a entidade e somente leitura. Por isso expomos acessores,
    // mas ainda nao fornecemos construtor de negocio ou metodos de alteracao.

    public Long getId() {
        return id;
    }

    public String getTitulo() {
        return titulo;
    }

    public String getIsbn() {
        return isbn;
    }

    public BigDecimal getPreco() {
        return preco;
    }

    public int getEstoque() {
        return estoque;
    }

    public Long getAutorId() {
        return autorId;
    }

    @Override
    public String toString() {
        return "Livro{" +
                "id=" + id +
                ", titulo='" + titulo + '\'' +
                ", isbn='" + isbn + '\'' +
                ", preco=" + preco +
                ", estoque=" + estoque +
                ", autorId=" + autorId +
                '}';
    }
}
