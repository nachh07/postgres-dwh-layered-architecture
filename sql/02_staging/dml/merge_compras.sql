-- =====================================================
-- Script: merge_compras.sql
-- Description: MERGE de landing_zone.raw_compras a staging.stg_compras
-- Implementa: INSERT, UPDATE, y Soft Delete (NOT MATCHED BY SOURCE)
-- =====================================================

MERGE INTO staging.stg_compras AS d USING (
    SELECT
        CAST(
            NULLIF(TRIM(idcompra), '') AS INTEGER
        ) AS id_compra,
        CAST(
            NULLIF(TRIM(fecha), '') AS DATE
        ) AS fecha,
        CAST(
            NULLIF(TRIM(idproducto), '') AS INTEGER
        ) AS id_producto,
        CAST(
            NULLIF(TRIM(cantidad), '') AS INTEGER
        ) AS cantidad,
        CAST(
            REPLACE(
                NULLIF(TRIM(precio), ''),
                ',',
                '.'
            ) AS NUMERIC(15, 3)
        ) AS precio,
        CAST(
            NULLIF(TRIM(idproveedor), '') AS INTEGER
        ) AS id_proveedor,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_compras
    WHERE
        TRIM(idcompra) IS NOT NULL
        AND TRIM(idcompra) <> ''
        AND TRIM(idcompra) ~ '^[0-9]+$'
) AS s ON d.id_compra = s.id_compra

-- 1. MATCHED: Si existe en ambos → UPDATE (mantiene activo)
WHEN MATCHED THEN
UPDATE
SET
    fecha = s.fecha,
    id_producto = s.id_producto,
    cantidad = s.cantidad,
    precio = COALESCE(s.precio, 0),
    id_proveedor = s.id_proveedor,
    updated_at = s.updated_at,
    is_deleted = FALSE,
    deleted_at = NULL

-- 2. NOT MATCHED: Si existe en origen pero no en destino → INSERT
WHEN NOT MATCHED THEN INSERT (
    id_compra,
    fecha,
    id_producto,
    cantidad,
    precio,
    id_proveedor,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
)
VALUES (
        s.id_compra,
        s.fecha,
        s.id_producto,
        s.cantidad,
        COALESCE(s.precio, 0),
        s.id_proveedor,
        CURRENT_TIMESTAMP,
        s.updated_at,
        FALSE,
        NULL
    )

-- 3. NOT MATCHED BY SOURCE: Si existe en destino pero NO en origen → Soft Delete
WHEN NOT MATCHED BY SOURCE
AND d.is_deleted = FALSE THEN
UPDATE
SET
    is_deleted = TRUE,
    deleted_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP;

-- Resumen de la operación
SELECT
    'Compras Activas' AS descripcion,
    COUNT(*) AS cantidad,
    SUM(precio * cantidad) AS monto_total
FROM staging.stg_compras
WHERE
    is_deleted = FALSE
UNION ALL
SELECT
    'Compras Eliminadas (Soft Delete)' AS descripcion,
    COUNT(*) AS cantidad,
    0 AS monto_total
FROM staging.stg_compras
WHERE
    is_deleted = TRUE
ORDER BY descripcion DESC;