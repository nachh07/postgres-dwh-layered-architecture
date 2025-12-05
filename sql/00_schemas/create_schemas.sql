-- =====================================================
-- Script: create_schemas.sql
-- Description: Creación de schemas para arquitectura de data engineering en 4 capas
-- Author: Data Engineering Team
-- Date: 2025-12-05
-- =====================================================

-- Capa 1: Landing Zone - Datos crudos sin transformar
DROP SCHEMA IF EXISTS landing_zone CASCADE;
CREATE SCHEMA landing_zone;
COMMENT ON SCHEMA landing_zone IS 'Capa de datos crudos sin transformaciones. Replica estructura de archivos CSV.';

-- Capa 2: Staging - Datos limpios con auditoría y soft deletes
DROP SCHEMA IF EXISTS staging CASCADE;
CREATE SCHEMA staging;
COMMENT ON SCHEMA staging IS 'Capa de staging con limpieza de datos, deduplicación y soft deletes mediante MERGE.';

-- Capa 3: Transformation - Transformaciones de negocio
DROP SCHEMA IF EXISTS transformation CASCADE;
CREATE SCHEMA transformation;
COMMENT ON SCHEMA transformation IS 'Capa de transformación con normalizaciones y lógica de negocio aplicada.';

-- Capa 4: Service - Modelo dimensional (Data Warehouse)
DROP SCHEMA IF EXISTS service CASCADE;
CREATE SCHEMA service;
COMMENT ON SCHEMA service IS 'Capa de servicio con modelo dimensional (Star Schema): dimensiones y hechos.';

-- Verificar creación de schemas
SELECT 
    schema_name,
    schema_owner,
    catalog_name
FROM information_schema.schemata
WHERE schema_name IN ('landing_zone', 'staging', 'transformation', 'service')
ORDER BY schema_name;

COMMENT ON SCHEMA landing_zone IS 'Landing Zone - Datos crudos desde CSV';
COMMENT ON SCHEMA staging IS 'Staging - Limpieza y MERGE con soft deletes';
COMMENT ON SCHEMA transformation IS 'Transformation - Transformaciones de negocio';
COMMENT ON SCHEMA service IS 'Service - Data Warehouse (Star Schema)';
