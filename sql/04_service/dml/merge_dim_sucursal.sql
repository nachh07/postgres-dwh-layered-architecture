-- =====================================================
-- Script: merge_dim_sucursal.sql
-- Description: MERGE de staging.stg_sucursales a service.dim_sucursal
-- Tipo: SCD Tipo 1
-- =====================================================

MERGE INTO service.dim_sucursal AS d USING (
    SELECT
        id_sucursal,
        sucursal,
        domicilio,
        localidad,
        provincia,
        latitud,
        longitud
    FROM staging.stg_sucursales
    WHERE
        is_deleted = FALSE
) AS s ON d.id_sucursal = s.id_sucursal

-- MATCHED: Actualizar
WHEN MATCHED THEN
UPDATE
SET
    sucursal = s.sucursal,
    domicilio = s.domicilio,
    localidad = s.localidad,
    provincia = s.provincia,
    latitud = s.latitud,
    longitud = s.longitud,
    updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar
WHEN NOT MATCHED THEN INSERT (
    id_sucursal,
    sucursal,
    domicilio,
    localidad,
    provincia,
    latitud,
    longitud,
    created_at,
    updated_at
)
VALUES (
        s.id_sucursal,
        s.sucursal,
        s.domicilio,
        s.localidad,
        s.provincia,
        s.latitud,
        s.longitud,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Resumen
SELECT 'dim_sucursal' AS dimension, COUNT(*) AS total_registros
FROM service.dim_sucursal;