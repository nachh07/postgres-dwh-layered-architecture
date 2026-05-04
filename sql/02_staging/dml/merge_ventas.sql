-- =====================================================
-- Script: merge_ventas.sql
-- Description: MERGE de landing_zone.raw_ventas a staging.stg_ventas
-- Implementa: INSERT, UPDATE, y Soft Delete (NOT MATCHED BY SOURCE)
-- =====================================================

MERGE INTO staging.stg_ventas AS d
USING (
    SELECT 
        CAST(NULLIF(TRIM(idventa), '') AS INTEGER) AS id_venta,
        CAST(NULLIF(TRIM(fecha), '') AS DATE) AS fecha,
        CAST(NULLIF(TRIM(fecha_entrega), '') AS DATE) AS fecha_entrega,
        CAST(NULLIF(TRIM(idcanal), '') AS INTEGER) AS id_canal,
        CAST(NULLIF(TRIM(idcliente), '') AS INTEGER) AS id_cliente,
        CAST(NULLIF(TRIM(idsucursal), '') AS INTEGER) AS id_sucursal,
        CAST(NULLIF(TRIM(idempleado), '') AS INTEGER) AS id_empleado,
        CAST(NULLIF(TRIM(idproducto), '') AS INTEGER) AS id_producto,
        CAST(REPLACE(NULLIF(TRIM(precio), ''), ',', '.') AS NUMERIC(15,3)) AS precio,
        CAST(REPLACE(NULLIF(TRIM(cantidad), ''), ',', '.') AS INTEGER) AS cantidad,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_ventas
    WHERE TRIM(idventa) IS NOT NULL 
      AND TRIM(idventa) <> ''
      AND TRIM(idventa) ~ '^[0-9]+$'
) AS s
ON d.id_venta = s.id_venta

-- 1. MATCHED: Si existe en ambos → UPDATE (mantiene activo)
WHEN MATCHED THEN
    UPDATE SET
        fecha = s.fecha,
        fecha_entrega = s.fecha_entrega,
        id_canal = s.id_canal,
        id_cliente = s.id_cliente,
        id_sucursal = s.id_sucursal,
        id_empleado = s.id_empleado,
        id_producto = s.id_producto,
        precio = COALESCE(s.precio, 0),
        cantidad = COALESCE(s.cantidad, 1),
        updated_at = s.updated_at,
        is_deleted = FALSE,
        deleted_at = NULL

-- 2. NOT MATCHED: Si existe en origen pero no en destino → INSERT
WHEN NOT MATCHED THEN
    INSERT (
        id_venta, fecha, fecha_entrega, id_canal, id_cliente,
        id_sucursal, id_empleado, id_producto, precio, cantidad,
        created_at, updated_at, is_deleted, deleted_at
    )
    VALUES (
        s.id_venta, s.fecha, s.fecha_entrega, s.id_canal, s.id_cliente,
        s.id_sucursal, s.id_empleado, s.id_producto,
        COALESCE(s.precio, 0),
        COALESCE(s.cantidad, 1),
        CURRENT_TIMESTAMP, s.updated_at, FALSE, NULL
    )

-- 3. NOT MATCHED BY SOURCE: Si existe en destino pero NO en origen → Soft Delete
WHEN NOT MATCHED BY SOURCE AND d.is_deleted = FALSE THEN
    UPDATE SET 
        is_deleted = TRUE,
        deleted_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;

-- Resumen de la operación
SELECT 
    'Ventas Activas' AS descripcion,
    COUNT(*) AS cantidad,
    SUM(precio * cantidad) AS monto_total
FROM staging.stg_ventas
WHERE is_deleted = FALSE
UNION ALL
SELECT 
    'Ventas Eliminadas (Soft Delete)' AS descripcion,
    COUNT(*) AS cantidad,
    0 AS monto_total
FROM staging.stg_ventas
WHERE is_deleted = TRUE
ORDER BY descripcion DESC;
