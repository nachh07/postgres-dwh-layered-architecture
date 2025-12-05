-- =====================================================
-- Script: merge_clientes.sql
-- Description: MERGE de landing_zone.raw_clientes a staging.stg_clientes
-- Implementa: INSERT, UPDATE, y Soft Delete (NOT MATCHED BY SOURCE)
-- =====================================================

MERGE INTO staging.stg_clientes AS d
USING (
    SELECT 
        CAST(NULLIF(TRIM(id), '') AS INTEGER) AS id_cliente,
        TRIM(provincia) AS provincia,
        TRIM(nombre_y_apellido) AS nombre_apellido,
        TRIM(domicilio) AS domicilio,
        TRIM(telefono) AS telefono,
        CAST(NULLIF(TRIM(edad), '') AS INTEGER) AS edad,
        TRIM(localidad) AS localidad,
        CAST(REPLACE(NULLIF(TRIM(y), ''), ',', '.') AS NUMERIC(13,10)) AS latitud,
        CAST(REPLACE(NULLIF(TRIM(x), ''), ',', '.') AS NUMERIC(13,10)) AS longitud,
        CAST(NULLIF(TRIM(fecha_alta), '') AS DATE) AS fecha_alta,
        CAST(NULLIF(TRIM(fecha_ultima_modificacion), '') AS DATE) AS fecha_ultima_modificacion,
        CAST(NULLIF(TRIM(marca_baja), '') AS INTEGER) AS marca_baja,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_clientes
    WHERE TRIM(id) IS NOT NULL 
      AND TRIM(id) <> ''
      AND TRIM(id) ~ '^[0-9]+$'  -- Solo valores numéricos válidos
) AS s
ON d.id_cliente = s.id_cliente

-- 1. MATCHED: Si existe en ambos → UPDATE (mantiene activo)
WHEN MATCHED THEN
    UPDATE SET
        provincia = COALESCE(s.provincia, 'Sin Dato'),
        nombre_apellido = COALESCE(s.nombre_apellido, 'Sin Dato'),
        domicilio = COALESCE(s.domicilio, 'Sin Dato'),
        telefono = s.telefono,
        edad = s.edad,
        localidad = COALESCE(s.localidad, 'Sin Dato'),
        latitud = COALESCE(s.latitud, 0),
        longitud = COALESCE(s.longitud, 0),
        fecha_alta = s.fecha_alta,
        fecha_ultima_modificacion = s.fecha_ultima_modificacion,
        marca_baja = COALESCE(s.marca_baja, 0),
        updated_at = s.updated_at,
        is_deleted = FALSE,
        deleted_at = NULL

-- 2. NOT MATCHED: Si existe en origen pero no en destino → INSERT
WHEN NOT MATCHED THEN
    INSERT (
        id_cliente, provincia, nombre_apellido, domicilio, telefono,
        edad, localidad, latitud, longitud,
        fecha_alta, fecha_ultima_modificacion, marca_baja,
        created_at, updated_at, is_deleted, deleted_at
    )
    VALUES (
        s.id_cliente,
        COALESCE(s.provincia, 'Sin Dato'),
        COALESCE(s.nombre_apellido, 'Sin Dato'),
        COALESCE(s.domicilio, 'Sin Dato'),
        s.telefono,
        s.edad,
        COALESCE(s.localidad, 'Sin Dato'),
        COALESCE(s.latitud, 0),
        COALESCE(s.longitud, 0),
        s.fecha_alta,
        s.fecha_ultima_modificacion,
        COALESCE(s.marca_baja, 0),
        CURRENT_TIMESTAMP,
        s.updated_at,
        FALSE,
        NULL
    )

-- 3. NOT MATCHED BY SOURCE: Si existe en destino pero NO en origen → Soft Delete
WHEN NOT MATCHED BY SOURCE AND d.is_deleted = FALSE THEN
    UPDATE SET 
        is_deleted = TRUE,
        deleted_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;

-- Resumen de la operación
SELECT 
    'Clientes Activos' AS descripcion,
    COUNT(*) AS cantidad
FROM staging.stg_clientes
WHERE is_deleted = FALSE
UNION ALL
SELECT 
    'Clientes Eliminados (Soft Delete)' AS descripcion,
    COUNT(*) AS cantidad
FROM staging.stg_clientes
WHERE is_deleted = TRUE
ORDER BY descripcion DESC;
