-- =====================================================
-- Script: merge_dim_proveedor.sql
-- Description: MERGE de staging.stg_proveedores a service.dim_proveedor
-- Tipo: SCD Tipo 1
-- =====================================================

MERGE INTO service.dim_proveedor AS d USING (
    SELECT
        id_proveedor,
        nombre,
        domicilio,
        ciudad,
        provincia,
        pais
    FROM staging.stg_proveedores
    WHERE
        is_deleted = FALSE
) AS s ON d.id_proveedor = s.id_proveedor

-- MATCHED: Actualizar
WHEN MATCHED THEN
UPDATE
SET
    nombre = s.nombre,
    domicilio = s.domicilio,
    ciudad = s.ciudad,
    provincia = s.provincia,
    pais = s.pais,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar
WHEN NOT MATCHED THEN INSERT (
    id_proveedor,
    nombre,
    domicilio,
    ciudad,
    provincia,
    pais,
    created_at,
    updated_at
)
VALUES (
        s.id_proveedor,
        s.nombre,
        s.domicilio,
        s.ciudad,
        s.provincia,
        s.pais,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT 'dim_proveedor' AS dimension, COUNT(*) AS total_registros
FROM service.dim_proveedor;