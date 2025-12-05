-- =====================================================
-- Script: merge_tipo_gasto.sql
-- Description: MERGE de landing_zone.raw_tipo_gasto a staging.stg_tipo_gasto
-- Implementa: INSERT, UPDATE, y Soft Delete
-- =====================================================

MERGE INTO staging.stg_tipo_gasto AS d USING (
    SELECT
        CAST(
            NULLIF(TRIM(idtipogasto), '') AS INTEGER
        ) AS id_tipo_gasto,
        TRIM(descripcion) AS descripcion,
        CAST(
            REPLACE(
                NULLIF(TRIM(monto_aproximado), ''),
                ',',
                '.'
            ) AS NUMERIC(15, 2)
        ) AS monto_aproximado,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_tipo_gasto
    WHERE
        TRIM(idtipogasto) IS NOT NULL
        AND TRIM(idtipogasto) <> ''
        AND TRIM(idtipogasto) ~ '^[0-9]+$'
) AS s ON d.id_tipo_gasto = s.id_tipo_gasto

-- 1. MATCHED: UPDATE
WHEN MATCHED THEN
UPDATE
SET
    descripcion = COALESCE(s.descripcion, 'Sin Dato'),
    monto_aproximado = COALESCE(s.monto_aproximado, 0),
    updated_at = s.updated_at,
    is_deleted = FALSE,
    deleted_at = NULL

-- 2. NOT MATCHED: INSERT
WHEN NOT MATCHED THEN INSERT (
    id_tipo_gasto,
    descripcion,
    monto_aproximado,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
)
VALUES (
        s.id_tipo_gasto,
        COALESCE(s.descripcion, 'Sin Dato'),
        COALESCE(s.monto_aproximado, 0),
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
SELECT 'Tipos de Gasto Activos' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_tipo_gasto
WHERE
    is_deleted = FALSE
UNION ALL
SELECT 'Tipos de Gasto Eliminados' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_tipo_gasto
WHERE
    is_deleted = TRUE
ORDER BY descripcion DESC;