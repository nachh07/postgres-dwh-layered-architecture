-- =====================================================
-- Script: merge_proveedores.sql
-- Description: MERGE de landing_zone.raw_proveedores a staging.stg_proveedores
-- Implementa: INSERT, UPDATE, y Soft Delete
-- =====================================================

MERGE INTO staging.stg_proveedores AS d USING (
    SELECT
        CAST(
            NULLIF(TRIM(idproveedor), '') AS INTEGER
        ) AS id_proveedor,
        TRIM(nombre) AS nombre,
        TRIM(address) AS domicilio,
        TRIM(city) AS ciudad,
        TRIM(state) AS provincia,
        TRIM(country) AS pais,
        TRIM(departamen) AS departamento,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_proveedores
    WHERE
        TRIM(idproveedor) IS NOT NULL
        AND TRIM(idproveedor) <> ''
        AND TRIM(idproveedor) ~ '^[0-9]+$'
) AS s ON d.id_proveedor = s.id_proveedor

-- 1. MATCHED: UPDATE
WHEN MATCHED THEN
UPDATE
SET
    nombre = COALESCE(s.nombre, 'Sin Dato'),
    domicilio = COALESCE(s.domicilio, 'Sin Dato'),
    ciudad = COALESCE(s.ciudad, 'Sin Dato'),
    provincia = COALESCE(s.provincia, 'Sin Dato'),
    pais = COALESCE(s.pais, 'Sin Dato'),
    departamento = COALESCE(s.departamento, 'Sin Dato'),
    updated_at = s.updated_at,
    is_deleted = FALSE,
    deleted_at = NULL

-- 2. NOT MATCHED: INSERT
WHEN NOT MATCHED THEN INSERT (
    id_proveedor,
    nombre,
    domicilio,
    ciudad,
    provincia,
    pais,
    departamento,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
)
VALUES (
        s.id_proveedor,
        COALESCE(s.nombre, 'Sin Dato'),
        COALESCE(s.domicilio, 'Sin Dato'),
        COALESCE(s.ciudad, 'Sin Dato'),
        COALESCE(s.provincia, 'Sin Dato'),
        COALESCE(s.pais, 'Sin Dato'),
        COALESCE(s.departamento, 'Sin Dato'),
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
SELECT 'Proveedores Activos' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_proveedores
WHERE
    is_deleted = FALSE
UNION ALL
SELECT 'Proveedores Eliminados' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_proveedores
WHERE
    is_deleted = TRUE
ORDER BY descripcion DESC;