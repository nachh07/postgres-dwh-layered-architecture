-- =====================================================
-- Script: merge_fact_compras.sql
-- Description: MERGE de staging.stg_compras a service.fact_compras
-- Nota: Requiere dimensiones cargadas
-- =====================================================

MERGE INTO service.fact_compras AS d USING (
    SELECT
        c.id_compra,
        dp.sk_producto,
        dpr.sk_proveedor,
        dt.sk_tiempo,
        c.cantidad,
        c.precio AS precio_unitario,
        (c.precio * c.cantidad) AS monto_total
    FROM staging.stg_compras c
        INNER JOIN service.dim_producto dp ON c.id_producto = dp.id_producto
        INNER JOIN service.dim_proveedor dpr ON c.id_proveedor = dpr.id_proveedor
        INNER JOIN service.dim_tiempo dt ON c.fecha = dt.fecha
    WHERE
        c.is_deleted = FALSE
) AS s ON d.id_compra = s.id_compra

-- MATCHED: Actualizar
WHEN MATCHED THEN
UPDATE
SET
    sk_producto = s.sk_producto,
    sk_proveedor = s.sk_proveedor,
    sk_tiempo = s.sk_tiempo,
    cantidad = s.cantidad,
    precio_unitario = s.precio_unitario,
    monto_total = s.monto_total,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar
WHEN NOT MATCHED THEN INSERT (
    id_compra,
    sk_producto,
    sk_proveedor,
    sk_tiempo,
    cantidad,
    precio_unitario,
    monto_total,
    created_at,
    updated_at
)
VALUES (
        s.id_compra,
        s.sk_producto,
        s.sk_proveedor,
        s.sk_tiempo,
        s.cantidad,
        s.precio_unitario,
        s.monto_total,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT
    'fact_compras' AS tabla,
    COUNT(*) AS total_registros,
    SUM(monto_total) AS monto_total_compras
FROM service.fact_compras;