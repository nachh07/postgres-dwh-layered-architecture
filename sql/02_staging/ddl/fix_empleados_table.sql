-- Fix para tabla empleados: Recrear con clave compuesta
DROP TABLE IF EXISTS staging.stg_empleados CASCADE;

CREATE TABLE staging.stg_empleados (
    id_empleado INTEGER NOT NULL,
    apellido VARCHAR(100),
    nombre VARCHAR(100),
    sucursal VARCHAR(80) NOT NULL,
    sector VARCHAR(50),
    cargo VARCHAR(50),
    salario NUMERIC(15, 2),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    -- Clave compuesta: un empleado puede estar en múltiples sucursales
    PRIMARY KEY (id_empleado, sucursal)
);

CREATE INDEX idx_stg_empleados_is_deleted ON staging.stg_empleados (is_deleted);

COMMENT ON TABLE staging.stg_empleados IS 'Staging de empleados con PK compuesta (id_empleado, sucursal)';

SELECT 'Tabla stg_empleados recreada con éxito' AS status;