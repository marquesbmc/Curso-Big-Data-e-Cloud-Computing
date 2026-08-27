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

// Livro e o lado "muitos": varios livros podem apontar para o mesmo Autor.
@Entity
@Table(name = "livro")
public class Livro {
    // A chave primaria continua sendo um atributo simples da entidade.
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

    // O antigo campo autorId agora e uma referencia para um objeto Autor.
    // optional=false corresponde ao NOT NULL da coluna autor_id.
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    // @JoinColumn liga o atributo autor a chave estrangeira autor_id existente.
    @JoinColumn(name = "autor_id", nullable = false)
    private Autor autor;

    // O construtor sem argumentos pode ser protected porque e destinado ao JPA.
    protected Livro() {
    }

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

    public Autor getAutor() {
        // Se o autor ainda for apenas um proxy, acessar seus dados pode executar SELECT.
        return autor;
    }

    @Override
    public String toString() {
        // Nao acessamos o autor para evitar inicializar a associacao lazy.
        // Tambem evitamos a recursao Livro -> Autor -> livros -> Livro.
        return "Livro{" +
                "id=" + id +
                ", titulo='" + titulo + '\'' +
                ", isbn='" + isbn + '\'' +
                ", preco=" + preco +
                ", estoque=" + estoque +
                '}';
    }
}
