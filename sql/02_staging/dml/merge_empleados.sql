-- =====================================================
-- Script: merge_empleados.sql
-- Description: MERGE de landing_zone.raw_empleados a staging.stg_empleados
-- Implementa: INSERT, UPDATE, y Soft Delete
-- =====================================================

MERGE INTO staging.stg_empleados AS d USING (
    SELECT
        CAST(
            NULLIF(TRIM(id_empleado), '') AS INTEGER
        ) AS id_empleado,
        TRIM(apellido) AS apellido,
        TRIM(nombre) AS nombre,
        TRIM(sucursal) AS sucursal,
        TRIM(sector) AS sector,
        TRIM(cargo) AS cargo,
        CAST(
            REPLACE(
                NULLIF(TRIM(salario), ''),
                ',',
                '.'
            ) AS NUMERIC(15, 2)
        ) AS salario,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_empleados
    WHERE
        TRIM(id_empleado) IS NOT NULL
        AND TRIM(id_empleado) <> ''
        AND TRIM(id_empleado) ~ '^[0-9]+$'
) AS s ON d.id_empleado = s.id_empleado
AND d.sucursal = s.sucursal

-- 1. MATCHED: UPDATE
WHEN MATCHED THEN
UPDATE
SET
    apellido = COALESCE(s.apellido, 'Sin Dato'),
    nombre = COALESCE(s.nombre, 'Sin Dato'),
    sucursal = COALESCE(s.sucursal, 'Sin Dato'),
    sector = COALESCE(s.sector, 'Sin Dato'),
    cargo = COALESCE(s.cargo, 'Sin Dato'),
    salario = COALESCE(s.salario, 0),
    updated_at = s.updated_at,
    is_deleted = FALSE,
    deleted_at = NULL

-- 2. NOT MATCHED: INSERT
WHEN NOT MATCHED THEN INSERT (
    id_empleado,
    apellido,
    nombre,
    sucursal,
    sector,
    cargo,
    salario,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
)
VALUES (
        s.id_empleado,
        COALESCE(s.apellido, 'Sin Dato'),
        COALESCE(s.nombre, 'Sin Dato'),
        COALESCE(s.sucursal, 'Sin Dato'),
        COALESCE(s.sector, 'Sin Dato'),
        COALESCE(s.cargo, 'Sin Dato'),
        COALESCE(s.salario, 0),
        CURRENT_TIMESTAMP,
        s.updated_at,
        FALSE,
        NULL
    )

-- 3. NOT MATCHED BY SOURCE: Soft Delete
WHEN NOT MATCHED BY SOURCE
AND d.is_deleted = FALSE THEN
UPDATE
SET
    is_deleted = TRUE,
    deleted_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP;

-- Resumen
SELECT 'Empleados Activos' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_empleados
WHERE
    is_deleted = FALSE
UNION ALL
SELECT 'Empleados Eliminados' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_empleados
WHERE
    is_deleted = TRUE
ORDER BY descripcion DESC;