-- =====================================================
-- Script: merge_fact_ventas.sql
-- Description: MERGE de staging.stg_ventas a service.fact_ventas
-- Nota: Requiere que todas las dimensiones estén cargadas
-- =====================================================

MERGE INTO service.fact_ventas AS d USING (
    SELECT
        v.id_venta,
        dc.sk_cliente,
        dp.sk_producto,
        ds.sk_sucursal,
        de.sk_empleado,
        dt_venta.sk_tiempo AS sk_tiempo_venta,
        dt_entrega.sk_tiempo AS sk_tiempo_entrega,
        dcan.sk_canal,
        v.cantidad,
        v.precio AS precio_unitario,
        (v.precio * v.cantidad) AS monto_total
    FROM
        staging.stg_ventas v
        INNER JOIN service.dim_cliente dc ON v.id_cliente = dc.id_cliente
        INNER JOIN service.dim_producto dp ON v.id_producto = dp.id_producto
        INNER JOIN service.dim_sucursal ds ON v.id_sucursal = ds.id_sucursal
        LEFT JOIN service.dim_empleado de ON v.id_empleado = de.id_empleado
        AND ds.sucursal = de.sucursal
        INNER JOIN service.dim_tiempo dt_venta ON v.fecha = dt_venta.fecha
        INNER JOIN service.dim_tiempo dt_entrega ON v.fecha_entrega = dt_entrega.fecha
        INNER JOIN service.dim_canal dcan ON v.id_canal = dcan.id_canal
    WHERE
        v.is_deleted = FALSE
) AS s ON d.id_venta = s.id_venta

-- MATCHED: Actualizar métricas (por si cambian precios o cantidades)
WHEN MATCHED THEN
UPDATE
SET
    sk_cliente = s.sk_cliente,
    sk_producto = s.sk_producto,
    sk_sucursal = s.sk_sucursal,
    sk_empleado = s.sk_empleado,
    sk_tiempo_venta = s.sk_tiempo_venta,
    sk_tiempo_entrega = s.sk_tiempo_entrega,
    sk_canal = s.sk_canal,
    cantidad = s.cantidad,
    precio_unitario = s.precio_unitario,
    monto_total = s.monto_total,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar nuevas ventas
WHEN NOT MATCHED THEN INSERT (
    id_venta,
    sk_cliente,
    sk_producto,
    sk_sucursal,
    sk_empleado,
    sk_tiempo_venta,
    sk_tiempo_entrega,
    sk_canal,
    cantidad,
    precio_unitario,
    monto_total,
    created_at,
    updated_at
)
VALUES (
        s.id_venta,
        s.sk_cliente,
        s.sk_producto,
        s.sk_sucursal,
        s.sk_empleado,
        s.sk_tiempo_venta,
        s.sk_tiempo_entrega,
        s.sk_canal,
        s.cantidad,
        s.precio_unitario,
        s.monto_total,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT
    'fact_ventas' AS tabla,
    COUNT(*) AS total_registros,
    SUM(monto_total) AS monto_total_ventas,
    MIN(sk_tiempo_venta) AS fecha_min,
    MAX(sk_tiempo_venta) AS fecha_max
FROM service.fact_ventas;