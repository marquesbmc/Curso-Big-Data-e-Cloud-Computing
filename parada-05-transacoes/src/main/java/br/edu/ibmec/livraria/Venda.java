package br.edu.ibmec.livraria;

import java.math.BigDecimal;
import java.time.LocalDateTime;

// Dados da venda confirmada depois do commit.
// LocalDateTime representa o momento da operacao e BigDecimal preserva o total
// monetario sem arredondamentos binarios.
public record Venda(long id, LocalDateTime dataHora, BigDecimal valorTotal) {
}
