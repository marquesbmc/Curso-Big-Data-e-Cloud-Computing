package br.edu.ibmec.livraria;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// Nesta parada Autor e necessario porque Livro.autor continua sendo um
// relacionamento JPA, embora a venda nao altere dados do autor.
@Entity
@Table(name = "autor")
public class Autor {
    // O ID permite que o Hibernate represente o autor por um proxy lazy.
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String nome;

    // Construtor reservado ao mecanismo de materializacao do JPA.
    protected Autor() {
    }

    public Long getId() {
        return id;
    }

    public String getNome() {
        return nome;
    }
}
