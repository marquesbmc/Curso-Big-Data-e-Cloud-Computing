package br.edu.ibmec.livraria;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.time.LocalDateTime;

// A tabela existente guarda data_hora como TEXT. Este conversor define de forma
// explicita a passagem entre LocalDateTime no Java e texto ISO-8601 no SQLite.
@Converter
public class LocalDateTimeStringConverter implements AttributeConverter<LocalDateTime, String> {
    @Override
    public String convertToDatabaseColumn(LocalDateTime valorJava) {
        // LocalDateTime.toString produz formato ISO-8601, por exemplo 2026-08-19T22:30.
        return valorJava == null ? null : valorJava.toString();
    }

    @Override
    public LocalDateTime convertToEntityAttribute(String valorBanco) {
        // A operacao inversa reconstrui o tipo Java ao ler a coluna TEXT.
        return valorBanco == null ? null : LocalDateTime.parse(valorBanco);
    }
}
