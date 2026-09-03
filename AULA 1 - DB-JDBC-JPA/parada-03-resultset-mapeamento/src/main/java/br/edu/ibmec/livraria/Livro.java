package br.edu.ibmec.livraria;

import java.math.BigDecimal;

// O record representa uma linha da tabela livro e gera construtor e acessores.
// BigDecimal e usado para valores monetarios, evitando erros de ponto flutuante.
// Os componentes seguem os nomes e tipos conceituais das colunas mapeadas.
// Como o record e imutavel, cada linha produz um objeto completo de uma vez.
public record Livro(long id, String titulo, String isbn, BigDecimal preco, int estoque, long autorId) {
}
