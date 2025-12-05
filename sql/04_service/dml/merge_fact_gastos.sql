-- =====================================================
-- Script: merge_fact_gastos.sql
-- Description: MERGE de staging.stg_gastos a service.fact_gastos
-- Nota: Requiere dimensiones cargadas
-- =====================================================

MERGE INTO service.fact_gastos AS d USING (
    SELECT g.id_gasto, ds.sk_sucursal, dt.sk_tiempo, dtg.sk_tipo_gasto, g.monto
    FROM staging.stg_gastos g
        INNER JOIN service.dim_sucursal ds ON g.id_sucursal = ds.id_sucursal
        INNER JOIN service.dim_tiempo dt ON g.fecha = dt.fecha
        INNER JOIN service.dim_tipo_gasto dtg ON g.id_tipo_gasto = dtg.id_tipo_gasto
    WHERE
        g.is_deleted = FALSE
) AS s ON d.id_gasto = s.id_gasto

-- MATCHED: Actualizar
WHEN MATCHED THEN
UPDATE
SET
    sk_sucursal = s.sk_sucursal,
    sk_tiempo = s.sk_tiempo,
    sk_tipo_gasto = s.sk_tipo_gasto,
    monto = s.monto,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar
WHEN NOT MATCHED THEN INSERT (
    id_gasto,
    sk_sucursal,
    sk_tiempo,
    sk_tipo_gasto,
    monto,
    created_at,
    updated_at
)
VALUES (
        s.id_gasto,
        s.sk_sucursal,
        s.sk_tiempo,
        s.sk_tipo_gasto,
        s.monto,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT
    'fact_gastos' AS tabla,
    COUNT(*) AS total_registros,
    SUM(monto) AS monto_total_gastos
FROM service.fact_gastos;