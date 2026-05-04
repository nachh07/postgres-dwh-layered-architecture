-- =====================================================
-- Script: merge_sucursales.sql
-- Description: MERGE de landing_zone.raw_sucursales a staging.stg_sucursales
-- Implementa: INSERT, UPDATE, y Soft Delete
-- =====================================================

MERGE INTO staging.stg_sucursales AS d USING (
    SELECT
        CAST(
            NULLIF(TRIM(id), '') AS INTEGER
        ) AS id_sucursal,
        TRIM(sucursal) AS sucursal,
        TRIM(direccion) AS domicilio,
        TRIM(localidad) AS localidad,
        TRIM(provincia) AS provincia,
        CAST(
            REPLACE(
                NULLIF(TRIM(latitud), ''),
                ',',
                '.'
            ) AS NUMERIC(13, 10)
        ) AS latitud,
        CAST(
            REPLACE(
                NULLIF(TRIM(longitud), ''),
                ',',
                '.'
            ) AS NUMERIC(13, 10)
        ) AS longitud,
        CURRENT_TIMESTAMP AS updated_at
    FROM landing_zone.raw_sucursales
    WHERE
        TRIM(id) IS NOT NULL
        AND TRIM(id) <> ''
        AND TRIM(id) ~ '^[0-9]+$'
) AS s ON d.id_sucursal = s.id_sucursal

-- 1. MATCHED: UPDATE
WHEN MATCHED THEN
UPDATE
SET
    sucursal = COALESCE(s.sucursal, 'Sin Dato'),
    domicilio = COALESCE(s.domicilio, 'Sin Dato'),
    localidad = COALESCE(s.localidad, 'Sin Dato'),
    provincia = COALESCE(s.provincia, 'Sin Dato'),
    latitud = COALESCE(s.latitud, 0),
    longitud = COALESCE(s.longitud, 0),
    updated_at = s.updated_at,
    is_deleted = FALSE,
    deleted_at = NULL

-- 2. NOT MATCHED: INSERT
WHEN NOT MATCHED THEN INSERT (
    id_sucursal,
    sucursal,
    domicilio,
    localidad,
    provincia,
    latitud,
    longitud,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
)
VALUES (
        s.id_sucursal,
        COALESCE(s.sucursal, 'Sin Dato'),
        COALESCE(s.domicilio, 'Sin Dato'),
        COALESCE(s.localidad, 'Sin Dato'),
        COALESCE(s.provincia, 'Sin Dato'),
        COALESCE(s.latitud, 0),
        COALESCE(s.longitud, 0),
        CURRENT_TIMESTAMP,
        s.updated_at,
        FALSE,
        NULL
    )

-- 3. NOT MATCHED BY SOURCE: Soft Delete
WHEN NOT MATCHED BY SOURCE
AND d.is_deleted = FALSE THEN
UPDATE
SET
    is_deleted = TRUE,
    deleted_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP;

-- Resumen
SELECT 'Sucursales Activas' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_sucursales
WHERE
    is_deleted = FALSE
UNION ALL
SELECT 'Sucursales Eliminadas' AS descripcion, COUNT(*) AS cantidad
FROM staging.stg_sucursales
WHERE
    is_deleted = TRUE
ORDER BY descripcion DESC;