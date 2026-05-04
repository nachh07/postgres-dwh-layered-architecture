-- =====================================================
-- Script: merge_productos.sql
-- Description: MERGE de landing_zone.raw_productos a staging.stg_productos
-- Implementa: INSERT, UPDATE, y Soft Delete
-- =====================================================

MERGE INTO staging.stg_productos AS d
USING (
    SELECT 
        CAST(NULLIF(TRIM(id_producto), '') AS INTEGER) AS id_producto,
        TRIM(concepto) AS producto,
        TRIM(tipo) AS tipo,
        CAST(REPLACE(NULLIF(TRIM(precio), ''), ',', '.') AS NUMERIC(15,3)) AS precio,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_productos
    WHERE TRIM(id_producto) IS NOT NULL 
      AND TRIM(id_producto) <> ''
      AND TRIM(id_producto) ~ '^[0-9]+$'
) AS s
ON d.id_producto = s.id_producto

-- 1. MATCHED: UPDATE
WHEN MATCHED THEN
    UPDATE SET
        producto = COALESCE(s.producto, 'Sin Dato'),
        tipo = COALESCE(s.tipo, 'Sin Dato'),
        precio = COALESCE(s.precio, 0),
        updated_at = s.updated_at,
        is_deleted = FALSE,
        deleted_at = NULL

-- 2. NOT MATCHED: INSERT
WHEN NOT MATCHED THEN
    INSERT (
        id_producto, producto, tipo, precio,
        created_at, updated_at, is_deleted, deleted_at
    )
    VALUES (
        s.id_producto,
        COALESCE(s.producto, 'Sin Dato'),
        COALESCE(s.tipo, 'Sin Dato'),
        COALESCE(s.precio, 0),
        CURRENT_TIMESTAMP, s.updated_at, FALSE, NULL
    )

-- 3. NOT MATCHED BY SOURCE: Soft Delete
WHEN NOT MATCHED BY SOURCE AND d.is_deleted = FALSE THEN
    UPDATE SET 
        is_deleted = TRUE,
        deleted_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;
