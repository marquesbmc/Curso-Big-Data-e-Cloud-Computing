package br.edu.ibmec.livraria;

public class Aplicacao {
    public static void main(String[] args) {
        // Service executa gravacoes; ConsultaLivro observa o estado do banco.
        VendaService servico = new VendaService(new ConnectionFactory());
        ConsultaLivro consulta = new ConsultaLivro(new ConnectionFactory());

        // Primeiro executamos o caminho feliz, que termina com commit.
        // orElseThrow deixa claro que o livro 1 deve existir no banco preparado.
        System.out.println("[1] Estoque inicial: " + consulta.buscarPorId(1).orElseThrow().estoque());
        VendaResultado resultado = servico.registrarVenda(1, 2);
        System.out.println("[2] Commit da venda: " + resultado.venda().id());
        System.out.println("    Novo estoque: " + resultado.estoqueRestante());

        // Depois forçamos uma falha de negocio para observar o rollback.
        // A quantidade e maior que qualquer estoque disponivel na base.
        try {
            servico.registrarVenda(1, 10_000);
        } catch (EstoqueInsuficienteException exception) {
            System.out.println("[3] Rollback: " + exception.getMessage());
        }

        // O metodo demonstrarSavepoint permanece disponivel como aprofundamento
        // opcional indicado no README, sem fazer parte deste fluxo principal.
    }
}
