-- Script de inicialización de PostgreSQL
-- Se ejecuta automáticamente al levantar el contenedor por primera vez
-- (montado en /docker-entrypoint-initdb.d/)

-- La base de datos ya se crea con POSTGRES_DB en docker-compose.
-- Aquí solo garantizamos que el usuario tenga todos los privilegios.

GRANT ALL PRIVILEGES ON DATABASE data_engineering TO postgres;
