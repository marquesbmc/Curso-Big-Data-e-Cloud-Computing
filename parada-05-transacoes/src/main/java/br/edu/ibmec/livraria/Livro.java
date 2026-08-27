package br.edu.ibmec.livraria;

import java.math.BigDecimal;

// Estado do livro lido antes de validar a quantidade e atualizar o estoque.
// O record e imutavel: VendaService calcula o estoque restante sem modificar
// este objeto, enquanto o UPDATE altera diretamente a linha no banco.
public record Livro(long id, String titulo, String isbn, BigDecimal preco, int estoque, long autorId) {
}
