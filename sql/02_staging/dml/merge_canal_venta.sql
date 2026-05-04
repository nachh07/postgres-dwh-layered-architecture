-- =====================================================
-- Script: merge_canal_venta.sql
-- Description: MERGE de landing_zone.raw_canal_venta a staging.stg_canal_venta
-- Implementa: INSERT, UPDATE, y Soft Delete
-- =====================================================

MERGE INTO staging.stg_canal_venta AS d USING (
    SELECT
        CAST(
            NULLIF(TRIM(codigo), '') AS INTEGER
        ) AS id_canal,
        TRIM(descripcion) AS canal,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_canal_venta
    WHERE
        TRIM(codigo) IS NOT NULL
        AND TRIM(codigo) <> ''
        AND TRIM(codigo) ~ '^[0-9]+$'
) AS s ON d.id_canal = s.id_canal

-- 1. MATCHED: UPDATE
WHEN MATCHED THEN
UPDATE
SET
    canal = COALESCE(s.canal, 'Sin Dato'),
    updated_at = s.updated_at,
    is_deleted = FALSE,
    deleted_at = NULL

-- 2. NOT MATCHED: INSERT
WHEN NOT MATCHED THEN INSERT (
    id_canal,
    canal,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
)
VALUES (
        s.id_canal,
        COALESCE(s.canal, 'Sin Dato'),
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
SELECT 'Canales Activos' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_canal_venta
WHERE
    is_deleted = FALSE
UNION ALL
SELECT 'Canales Eliminados' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_canal_venta
WHERE
    is_deleted = TRUE
ORDER BY descripcion DESC;