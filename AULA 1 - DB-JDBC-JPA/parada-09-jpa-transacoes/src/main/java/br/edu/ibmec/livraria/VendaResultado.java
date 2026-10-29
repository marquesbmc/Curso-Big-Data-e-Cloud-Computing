package br.edu.ibmec.livraria;

// Este record e apenas um DTO; entidades JPA continuam sendo classes comuns.
// Ele devolve somente dados simples porque o EntityManager do service sera fechado.
public record VendaResultado(long vendaId, long itemVendaId, int estoqueRestante) {
}
