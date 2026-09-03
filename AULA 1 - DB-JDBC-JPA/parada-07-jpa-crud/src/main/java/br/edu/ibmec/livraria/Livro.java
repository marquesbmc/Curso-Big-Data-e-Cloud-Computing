package br.edu.ibmec.livraria;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;

// Esta classe representa simultaneamente um objeto do dominio e uma linha da
// tabela livro enquanto estiver associada a um contexto de persistencia.
@Entity
@Table(name = "livro")
public class Livro {
    // Long, em vez de long, permite usar null enquanto o objeto ainda e novo.
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

    @Column(name = "autor_id", nullable = false)
    private Long autorId;

    // O provedor chama este construtor por reflexao ao materializar uma linha.
    protected Livro() {
    }

    // A aplicacao nao informa o ID: o SQLite o gera durante o persist.
    public Livro(String titulo, String isbn, BigDecimal preco, int estoque, Long autorId) {
        this.titulo = titulo;
        this.isbn = isbn;
        this.preco = preco;
        this.estoque = estoque;
        this.autorId = autorId;
    }

    // Alterar uma entidade gerenciada e suficiente. No commit, o Hibernate
    // detecta a mudanca e produz o UPDATE automaticamente (dirty checking).
    public void atualizar(String titulo, BigDecimal preco, int estoque) {
        this.titulo = titulo;
        this.preco = preco;
        this.estoque = estoque;
    }

    // Nao existe setId: a identidade pertence ao banco e ao provedor JPA.

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
