-- =====================================================
-- Script: merge_dim_producto.sql
-- Description: MERGE de staging.stg_productos a service.dim_producto
-- Tipo: SCD Tipo 1 (sobrescribe cambios)
-- =====================================================

MERGE INTO service.dim_producto AS d USING (
    SELECT
        id_producto,
        producto,
        tipo AS tipo_producto,
        precio AS precio_lista
    FROM staging.stg_productos
    WHERE
        is_deleted = FALSE -- Solo productos activos
) AS s ON d.id_producto = s.id_producto

-- MATCHED: Actualizar atributos (SCD Tipo 1)
WHEN MATCHED THEN
UPDATE
SET
    producto = s.producto,
    tipo_producto = s.tipo_producto,
    precio_lista = s.precio_lista,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar nuevos productos
WHEN NOT MATCHED THEN INSERT (
    id_producto,
    producto,
    tipo_producto,
    precio_lista,
    created_at,
    updated_at
)
VALUES (
        s.id_producto,
        s.producto,
        s.tipo_producto,
        s.precio_lista,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT 'dim_producto' AS dimension, COUNT(*) AS total_registros
FROM service.dim_producto;