package br.edu.ibmec.livraria;

import java.math.BigDecimal;

// Representa a associacao entre uma venda e o livro vendido.
// precoUnitario registra o valor praticado e nao deve depender de alteracoes
// futuras no preco atual do livro.
public record ItemVenda(
        long id,
        long vendaId,
        long livroId,
        int quantidade,
        BigDecimal precoUnitario) {
}
