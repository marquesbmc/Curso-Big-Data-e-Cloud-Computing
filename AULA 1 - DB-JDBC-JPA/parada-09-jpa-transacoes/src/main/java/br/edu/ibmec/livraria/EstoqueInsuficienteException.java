package br.edu.ibmec.livraria;

// Excecao de negocio unchecked: ao atravessar VendaService, ela interrompe o
// fluxo normal e faz o bloco catch executar rollback da transacao ativa.
public class EstoqueInsuficienteException extends RuntimeException {
    public EstoqueInsuficienteException(String mensagem) {
        super(mensagem);
    }
}
