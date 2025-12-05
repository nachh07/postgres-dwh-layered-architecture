-- =====================================================
-- Script: merge_dim_cliente.sql
-- Description: MERGE de staging.stg_clientes a service.dim_cliente
-- Tipo: SCD Tipo 1 (sobrescribe cambios)
-- =====================================================

MERGE INTO service.dim_cliente AS d
USING (
    SELECT 
        id_cliente,
        nombre_apellido,
        provincia,
        localidad,
        domicilio,
        telefono,
        edad,
        latitud,
        longitud
    FROM staging.stg_clientes
    WHERE is_deleted = FALSE  -- Solo clientes activos
) AS s
ON d.id_cliente = s.id_cliente

-- MATCHED: Actualizar atributos (SCD Tipo 1)
WHEN MATCHED THEN
    UPDATE SET
        nombre_apellido = s.nombre_apellido,
        provincia = s.provincia,
        localidad = s.localidad,
        domicilio = s.domicilio,
        telefono = s.telefono,
        edad = s.edad,
        latitud = s.latitud,
        longitud = s.longitud,
        updated_at = CURRENT_TIMESTAMP

-- NOT MATCHED: Insertar nuevos clientes
WHEN NOT MATCHED THEN
    INSERT (
        id_cliente, nombre_apellido, provincia, localidad,
        domicilio, telefono, edad, latitud, longitud,
        created_at, updated_at
    )
    VALUES (
        s.id_cliente, s.nombre_apellido, s.provincia, s.localidad,
        s.domicilio, s.telefono, s.edad, s.latitud, s.longitud,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

-- Resumen
SELECT 'dim_cliente' AS dimension, COUNT(*) AS total_registros
FROM service.dim_cliente;
