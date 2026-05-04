-- =====================================================
-- Script: merge_dim_tipo_gasto.sql
-- Description: MERGE de staging.stg_tipo_gasto a service.dim_tipo_gasto
-- Tipo: SCD Tipo 1
-- =====================================================

MERGE INTO service.dim_tipo_gasto AS d USING (
    SELECT
        id_tipo_gasto,
        descripcion,
        monto_aproximado
    FROM staging.stg_tipo_gasto
    WHERE
        is_deleted = FALSE
) AS s ON d.id_tipo_gasto = s.id_tipo_gasto

-- MATCHED: Actualizar
WHEN MATCHED THEN
UPDATE
SET
    descripcion = s.descripcion,
    monto_aproximado = s.monto_aproximado,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar
WHEN NOT MATCHED THEN INSERT (
    id_tipo_gasto,
    descripcion,
    monto_aproximado,
    created_at,
    updated_at
)
VALUES (
        s.id_tipo_gasto,
        s.descripcion,
        s.monto_aproximado,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT 'dim_tipo_gasto' AS dimension, COUNT(*) AS total_registros
FROM service.dim_tipo_gasto;