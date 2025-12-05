-- =====================================================
-- Script: merge_dim_empleado.sql
-- Description: MERGE de staging.stg_empleados a service.dim_empleado
-- Tipo: SCD Tipo 1 con clave compuesta (id_empleado, sucursal)
-- =====================================================

MERGE INTO service.dim_empleado AS d USING (
    SELECT
        id_empleado,
        apellido,
        nombre,
        sucursal,
        sector,
        cargo,
        salario
    FROM staging.stg_empleados
    WHERE
        is_deleted = FALSE
) AS s ON d.id_empleado = s.id_empleado
AND d.sucursal = s.sucursal

-- MATCHED: Actualizar
WHEN MATCHED THEN
UPDATE
SET
    apellido = s.apellido,
    nombre = s.nombre,
    sector = s.sector,
    cargo = s.cargo,
    salario = s.salario,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar
WHEN NOT MATCHED THEN INSERT (
    id_empleado,
    apellido,
    nombre,
    sucursal,
    sector,
    cargo,
    salario,
    created_at,
    updated_at
)
VALUES (
        s.id_empleado,
        s.apellido,
        s.nombre,
        s.sucursal,
        s.sector,
        s.cargo,
        s.salario,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT 'dim_empleado' AS dimension, COUNT(*) AS total_registros
FROM service.dim_empleado;