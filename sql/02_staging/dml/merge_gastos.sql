-- =====================================================
-- Script: merge_gastos.sql
-- Description: MERGE de landing_zone.raw_gastos a staging.stg_gastos
-- Implementa: INSERT, UPDATE, y Soft Delete
-- =====================================================

MERGE INTO staging.stg_gastos AS d USING (
    SELECT
        CAST(
            NULLIF(TRIM(idgasto), '') AS INTEGER
        ) AS id_gasto,
        CAST(
            NULLIF(TRIM(idsucursal), '') AS INTEGER
        ) AS id_sucursal,
        CAST(
            NULLIF(TRIM(idtipogasto), '') AS INTEGER
        ) AS id_tipo_gasto,
        CAST(
            NULLIF(TRIM(fecha), '') AS DATE
        ) AS fecha,
        CAST(
            REPLACE(
                NULLIF(TRIM(monto), ''),
                ',',
                '.'
            ) AS NUMERIC(15, 2)
        ) AS monto,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_gastos
    WHERE
        TRIM(idgasto) IS NOT NULL
        AND TRIM(idgasto) <> ''
        AND TRIM(idgasto) ~ '^[0-9]+$'
) AS s ON d.id_gasto = s.id_gasto

-- 1. MATCHED: UPDATE
WHEN MATCHED THEN
UPDATE
SET
    id_sucursal = s.id_sucursal,
    id_tipo_gasto = s.id_tipo_gasto,
    fecha = s.fecha,
    monto = COALESCE(s.monto, 0),
    updated_at = s.updated_at,
    is_deleted = FALSE,
    deleted_at = NULL

-- 2. NOT MATCHED: INSERT
WHEN NOT MATCHED THEN INSERT (
    id_gasto,
    id_sucursal,
    id_tipo_gasto,
    fecha,
    monto,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
)
VALUES (
        s.id_gasto,
        s.id_sucursal,
        s.id_tipo_gasto,
        s.fecha,
        COALESCE(s.monto, 0),
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
SELECT
    'Gastos Activos' AS descripcion,
    COUNT(*) AS cantidad,
    SUM(monto) AS monto_total
FROM staging.stg_gastos
WHERE
    is_deleted = FALSE
UNION ALL
SELECT
    'Gastos Eliminados' AS descripcion,
    COUNT(*) AS cantidad,
    0 AS monto_total
FROM staging.stg_gastos
WHERE
    is_deleted = TRUE
ORDER BY descripcion DESC;