package br.edu.ibmec.livraria;

// Agrupa os dois dados que a aplicacao precisa exibir ao concluir uma venda.
// Este DTO evita devolver a Connection ou outros recursos JDBC para a aplicacao.
public record VendaResultado(Venda venda, int estoqueRestante) {
}
