package br.edu.ibmec.livraria;

import java.math.BigDecimal;

// Entidade imutavel usada pelo DAO para receber e devolver dados de livro.
// No INSERT, id chega como zero; o DAO devolve outro record com a chave gerada.
// O record evita setters e torna explicito que a alteracao cria um novo valor.
public record Livro(long id, String titulo, String isbn, BigDecimal preco, int estoque, long autorId) {
}
