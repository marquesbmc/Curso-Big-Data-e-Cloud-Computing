package br.edu.ibmec.livraria;

public class Aplicacao {
    public static void main(String[] args) {
        // Uma unica instancia de consulta reutiliza a mesma fabrica e mapper.
        ConsultaLivro consulta = new ConsultaLivro(new ConnectionFactory());

        // As duas primeiras chamadas contrastam Optional preenchido e vazio.
        System.out.println("[1] Comparando resultados opcionais");
        System.out.println("    Livro 1: " + consulta.buscarPorId(1));
        System.out.println("    Livro inexistente: " + consulta.buscarPorId(999));

        // As consultas abaixo retornam listas de objetos Livro ja mapeados.
        // toString e fornecido automaticamente pelo record.
        System.out.println("[2] Percorrendo listas mapeadas");
        System.out.println("    Todos: " + consulta.listarTodos());
        System.out.println("    Com Casa: " + consulta.buscarPorParteDoTitulo("Casa"));
    }
}
