package br.edu.ibmec.livraria;

// Excecao de negocio: interrompe a venda e provoca o rollback da transacao.
// RuntimeException permite atravessar os metodos sem declarar throws em todos eles.
// A mensagem explica a regra violada para a camada que chamou o service.
public class EstoqueInsuficienteException extends RuntimeException {
    public EstoqueInsuficienteException(String mensagem) {
        super(mensagem);
    }
}
