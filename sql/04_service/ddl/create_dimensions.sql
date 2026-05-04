-- =====================================================
-- Script: create_dimensions.sql (Service Layer)
-- Description: Creación de dimensiones para el modelo dimensional (Star Schema)
-- =====================================================

-- ============== DIMENSIÓN: dim_tiempo ==============
DROP TABLE IF EXISTS service.dim_tiempo CASCADE;

CREATE TABLE service.dim_tiempo (
    sk_tiempo SERIAL PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    dia INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    semana INTEGER NOT NULL,
    dia_nombre VARCHAR(20) NOT NULL,
    mes_nombre VARCHAR(20) NOT NULL,
    es_fin_semana BOOLEAN NOT NULL,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_tiempo_fecha ON service.dim_tiempo (fecha);

CREATE INDEX idx_dim_tiempo_anio_mes ON service.dim_tiempo (anio, mes);

COMMENT ON TABLE service.dim_tiempo IS 'Dimensión conformada de tiempo/calendario';

-- ============== DIMENSIÓN: dim_cliente ==============
DROP TABLE IF EXISTS service.dim_cliente CASCADE;

CREATE TABLE service.dim_cliente (
    sk_cliente SERIAL PRIMARY KEY,
    id_cliente INTEGER NOT NULL UNIQUE,
    nombre_apellido VARCHAR(150),
    provincia VARCHAR(50),
    localidad VARCHAR(80),
    domicilio VARCHAR(200),
    telefono VARCHAR(30),
    edad INTEGER,
    latitud NUMERIC(13, 10),
    longitud NUMERIC(13, 10),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_cliente_provincia ON service.dim_cliente (provincia);

CREATE INDEX idx_dim_cliente_localidad ON service.dim_cliente (localidad);

COMMENT ON TABLE service.dim_cliente IS 'Dimensión de clientes (SCD Tipo 1)';

-- ============== DIMENSIÓN: dim_producto ==============
DROP TABLE IF EXISTS service.dim_producto CASCADE;

CREATE TABLE service.dim_producto (
    sk_producto SERIAL PRIMARY KEY,
    id_producto INTEGER NOT NULL UNIQUE,
    producto VARCHAR(150),
    tipo_producto VARCHAR(50),
    precio_lista NUMERIC(15, 3),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_producto_tipo ON service.dim_producto (tipo_producto);

COMMENT ON TABLE service.dim_producto IS 'Dimensión de productos (SCD Tipo 1)';

-- ============== DIMENSIÓN: dim_sucursal ==============
DROP TABLE IF EXISTS service.dim_sucursal CASCADE;

CREATE TABLE service.dim_sucursal (
    sk_sucursal SERIAL PRIMARY KEY,
    id_sucursal INTEGER NOT NULL UNIQUE,
    sucursal VARCHAR(80),
    domicilio VARCHAR(200),
    localidad VARCHAR(80),
    provincia VARCHAR(50),
    latitud NUMERIC(13, 10),
    longitud NUMERIC(13, 10),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_sucursal_provincia ON service.dim_sucursal (provincia);

COMMENT ON TABLE service.dim_sucursal IS 'Dimensión de sucursales (SCD Tipo 1)';

-- ============== DIMENSIÓN: dim_empleado ==============
DROP TABLE IF EXISTS service.dim_empleado CASCADE;

CREATE TABLE service.dim_empleado (
    sk_empleado SERIAL,
    id_empleado INTEGER NOT NULL,
    apellido VARCHAR(100),
    nombre VARCHAR(100),
    sucursal VARCHAR(80) NOT NULL,
    sector VARCHAR(50),
    cargo VARCHAR(50),
    salario NUMERIC(15, 2),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Clave compuesta: empleado puede estar en múltiples sucursales
    PRIMARY KEY (id_empleado, sucursal)
);

CREATE INDEX idx_dim_empleado_sk ON service.dim_empleado (sk_empleado);

CREATE INDEX idx_dim_empleado_cargo ON service.dim_empleado (cargo);

CREATE INDEX idx_dim_empleado_sector ON service.dim_empleado (sector);

COMMENT ON TABLE service.dim_empleado IS 'Dimensión de empleados - Permite empleados en múltiples sucursales';

-- ============== DIMENSIÓN: dim_proveedor ==============
DROP TABLE IF EXISTS service.dim_proveedor CASCADE;

CREATE TABLE service.dim_proveedor (
    sk_proveedor SERIAL PRIMARY KEY,
    id_proveedor INTEGER NOT NULL UNIQUE,
    nombre VARCHAR(150),
    domicilio VARCHAR(200),
    ciudad VARCHAR(80),
    provincia VARCHAR(50),
    pais VARCHAR(50),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_proveedor_pais ON service.dim_proveedor (pais);

COMMENT ON TABLE service.dim_proveedor IS 'Dimensión de proveedores (SCD Tipo 1)';

-- ============== DIMENSIÓN: dim_canal ==============
DROP TABLE IF EXISTS service.dim_canal CASCADE;

CREATE TABLE service.dim_canal (
    sk_canal SERIAL PRIMARY KEY,
    id_canal INTEGER NOT NULL UNIQUE,
    canal VARCHAR(50),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE service.dim_canal IS 'Dimensión de canales de venta';

-- ============== DIMENSIÓN: dim_tipo_gasto ==============
DROP TABLE IF EXISTS service.dim_tipo_gasto CASCADE;

CREATE TABLE service.dim_tipo_gasto (
    sk_tipo_gasto SERIAL PRIMARY KEY,
    id_tipo_gasto INTEGER NOT NULL UNIQUE,
    descripcion VARCHAR(150),
    monto_aproximado NUMERIC(15, 2),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE service.dim_tipo_gasto IS 'Dimensión de tipos de gasto';

-- Verificar creación de dimensiones
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE
    table_schema = 'service'
    AND table_name LIKE 'dim_%'
ORDER BY table_name;