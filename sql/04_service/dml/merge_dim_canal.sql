-- =====================================================
-- Script: merge_dim_canal.sql
-- Description: MERGE de staging.stg_canal_venta a service.dim_canal
-- Tipo: SCD Tipo 1
-- =====================================================

MERGE INTO service.dim_canal AS d USING (
    SELECT id_canal, canal
    FROM staging.stg_canal_venta
    WHERE
        is_deleted = FALSE
) AS s ON d.id_canal = s.id_canal

-- MATCHED: Actualizar
WHEN MATCHED THEN
UPDATE
SET
    canal = s.canal,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar
WHEN NOT MATCHED THEN INSERT (
    id_canal,
    canal,
    created_at,
    updated_at
)
VALUES (
        s.id_canal,
        s.canal,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT 'dim_canal' AS dimension, COUNT(*) AS total_registros
FROM service.dim_canal;