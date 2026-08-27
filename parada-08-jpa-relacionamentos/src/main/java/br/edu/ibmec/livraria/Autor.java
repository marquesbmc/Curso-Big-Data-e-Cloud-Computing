package br.edu.ibmec.livraria;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import java.util.ArrayList;
import java.util.List;

// Autor representa o lado "um" do relacionamento: um autor pode possuir
// varios livros, mas continua armazenado em uma unica linha da tabela autor.
@Entity
@Table(name = "autor")
public class Autor {
    // A identidade permite ao JPA reconhecer quando dois objetos representam
    // a mesma linha, inclusive ao navegar a partir de Livro.
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String nome;

    // mappedBy informa que a coluna autor_id e controlada pelo atributo
    // Livro.autor. Nenhuma tabela ou coluna adicional sera criada.
    // LAZY cria uma colecao que consulta o banco somente no primeiro acesso.
    @OneToMany(mappedBy = "autor", fetch = FetchType.LAZY)
    private List<Livro> livros = new ArrayList<>();

    // Obrigatorio para o provedor instanciar a entidade por reflexao.
    protected Autor() {
    }

    public Long getId() {
        return id;
    }

    public String getNome() {
        return nome;
    }

    public List<Livro> getLivros() {
        // A chamada deste getter nao garante SELECT por si so; a inicializacao
        // normalmente ocorre quando a colecao e percorrida ou consulta seu tamanho.
        return livros;
    }

    @Override
    public String toString() {
        // Nao incluimos livros para evitar recursao Autor -> Livro -> Autor.
        // Isso tambem impede que uma simples impressao dispare o carregamento lazy.
        return "Autor{" + "id=" + id + ", nome='" + nome + "'}";
    }
}
