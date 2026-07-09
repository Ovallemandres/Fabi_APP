---
trigger: always_on
---

REGLA DE ENTORNO ESTRICTA:
A partir de ahora, nuestra base de datos es PostgreSQL. Al generar código de Django (modelos, vistas o queries), debes cumplir estas reglas obligatorias:

1. Tipado Estricto: Respeta los max_length y los tipos de datos exactos. Postgres no perdona inserciones incorrectas.
2. Migraciones Seguras: Si sugieres agregar un campo nuevo a un modelo existente, asegúrate de incluir null=True, blank=True o un valor default explícito.
3. Búsquedas Insensibles y sin Acentos: Utiliza siempre __unaccent__icontains en lugar de __contains para búsquedas de texto (requiere UnaccentExtension). Postgres es Case Sensitive y distingue tildes.
4. Concurrencia: Mantén el uso de transaction.atomic() y select_for_update() para la generación de códigos financieros o actualización de inventario para aprovechar el bloqueo de filas.
5. Base de datos física: Nunca sugieras borrar archivos .sqlite3. Todo manejo de DB se hace mediante manage.py dbshell o migrate.
6. Restricciones a nivel DB: Utiliza CheckConstraint y UniqueConstraint en la clase Meta para evitar datos inconsistentes (ej. totales negativos), delegando la responsabilidad a Postgres.
7. Campos Especiales: Utiliza JSONField para datos no estructurados y ArrayField para listas simples en lugar de crear modelos relacionales innecesarios.
8. Indexación: Añade db_index=True a columnas que se usarán constantemente en filtros (fechas, estatus) para no penalizar el I/O.
