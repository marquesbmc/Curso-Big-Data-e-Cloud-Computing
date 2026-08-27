# Dependencias locais de JPA

Os JARs desta pasta permitem compilar e executar as paradas JPA somente com
`javac` e `java`. O arquivo `.tools/jpa-dependencies-pom.xml` registra as
versoes e pode ser usado para reconstruir esta pasta, mas Maven nao e necessario
durante as aulas.

Dependencias principais:

- Jakarta Persistence 3.2;
- Hibernate ORM 7.4.5.Final;
- Hibernate Community Dialects 7.4.5.Final;
- SQLite JDBC 3.46.1.3.
