-- =====================================================
-- Script: create_tables.sql (Staging)
-- Description: Creación de tablas en staging con tipos de datos correctos y columnas de auditoría
-- Nota: Incluye created_at, updated_at, is_deleted, deleted_at
-- =====================================================

-- ============== TABLA: stg_clientes ==============
DROP TABLE IF EXISTS staging.stg_clientes CASCADE;

CREATE TABLE staging.stg_clientes (
    id_cliente INTEGER NOT NULL PRIMARY KEY,
    provincia VARCHAR(50),
    nombre_apellido VARCHAR(150),
    domicilio VARCHAR(200),
    telefono VARCHAR(30),
    edad INTEGER,
    localidad VARCHAR(80),
    latitud NUMERIC(13, 10),
    longitud NUMERIC(13, 10),
    fecha_alta DATE,
    fecha_ultima_modificacion DATE,
    marca_baja INTEGER,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_clientes_is_deleted ON staging.stg_clientes (is_deleted);

COMMENT ON TABLE staging.stg_clientes IS 'Staging de clientes con limpieza y auditoría';

-- ============== TABLA: stg_ventas ==============
DROP TABLE IF EXISTS staging.stg_ventas CASCADE;

CREATE TABLE staging.stg_ventas (
    id_venta INTEGER NOT NULL PRIMARY KEY,
    fecha DATE NOT NULL,
    fecha_entrega DATE NOT NULL,
    id_canal INTEGER,
    id_cliente INTEGER,
    id_sucursal INTEGER,
    id_empleado INTEGER,
    id_producto INTEGER,
    precio NUMERIC(15, 3),
    cantidad INTEGER,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_ventas_fecha ON staging.stg_ventas (fecha);

CREATE INDEX idx_stg_ventas_is_deleted ON staging.stg_ventas (is_deleted);

COMMENT ON TABLE staging.stg_ventas IS 'Staging de ventas con limpieza y auditoría';

-- ============== TABLA: stg_productos ==============
DROP TABLE IF EXISTS staging.stg_productos CASCADE;

CREATE TABLE staging.stg_productos (
    id_producto INTEGER NOT NULL PRIMARY KEY,
    producto VARCHAR(150),
    tipo VARCHAR(50),
    precio NUMERIC(15, 3),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_productos_is_deleted ON staging.stg_productos (is_deleted);

COMMENT ON TABLE staging.stg_productos IS 'Staging de productos con limpieza y auditoría';

-- ============== TABLA: stg_compras ==============
DROP TABLE IF EXISTS staging.stg_compras CASCADE;

CREATE TABLE staging.stg_compras (
    id_compra INTEGER NOT NULL PRIMARY KEY,
    fecha DATE NOT NULL,
    id_producto INTEGER,
    cantidad INTEGER,
    precio NUMERIC(15, 3),
    id_proveedor INTEGER,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_compras_fecha ON staging.stg_compras (fecha);

CREATE INDEX idx_stg_compras_is_deleted ON staging.stg_compras (is_deleted);

COMMENT ON TABLE staging.stg_compras IS 'Staging de compras con limpieza y auditoría';

-- ============== TABLA: stg_gastos ==============
DROP TABLE IF EXISTS staging.stg_gastos CASCADE;

CREATE TABLE staging.stg_gastos (
    id_gasto INTEGER NOT NULL PRIMARY KEY,
    id_sucursal INTEGER,
    id_tipo_gasto INTEGER,
    fecha DATE NOT NULL,
    monto NUMERIC(15, 2),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_gastos_fecha ON staging.stg_gastos (fecha);

CREATE INDEX idx_stg_gastos_is_deleted ON staging.stg_gastos (is_deleted);

COMMENT ON TABLE staging.stg_gastos IS 'Staging de gastos con limpieza y auditoría';

-- ============== TABLA: stg_empleados ==============
DROP TABLE IF EXISTS staging.stg_empleados CASCADE;

CREATE TABLE staging.stg_empleados (
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
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    -- Clave compuesta: un empleado puede estar en múltiples sucursales
    PRIMARY KEY (id_empleado, sucursal)
);

CREATE INDEX idx_stg_empleados_is_deleted ON staging.stg_empleados (is_deleted);

COMMENT ON TABLE staging.stg_empleados IS 'Staging de empleados con limpieza y auditoría. PK compuesta: (id_empleado, sucursal)';

-- ============== TABLA: stg_sucursales ==============
DROP TABLE IF EXISTS staging.stg_sucursales CASCADE;

CREATE TABLE staging.stg_sucursales (
    id_sucursal INTEGER NOT NULL PRIMARY KEY,
    sucursal VARCHAR(80),
    domicilio VARCHAR(200),
    localidad VARCHAR(80),
    provincia VARCHAR(50),
    latitud NUMERIC(13, 10),
    longitud NUMERIC(13, 10),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_sucursales_is_deleted ON staging.stg_sucursales (is_deleted);

COMMENT ON TABLE staging.stg_sucursales IS 'Staging de sucursales con limpieza y auditoría';

-- ============== TABLA: stg_proveedores ==============
DROP TABLE IF EXISTS staging.stg_proveedores CASCADE;

CREATE TABLE staging.stg_proveedores (
    id_proveedor INTEGER NOT NULL PRIMARY KEY,
    nombre VARCHAR(150),
    domicilio VARCHAR(200),
    ciudad VARCHAR(80),
    provincia VARCHAR(50),
    pais VARCHAR(50),
    departamento VARCHAR(80),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_proveedores_is_deleted ON staging.stg_proveedores (is_deleted);

COMMENT ON TABLE staging.stg_proveedores IS 'Staging de proveedores con limpieza y auditoría';

-- ============== TABLA: stg_canal_venta ==============
DROP TABLE IF EXISTS staging.stg_canal_venta CASCADE;

CREATE TABLE staging.stg_canal_venta (
    id_canal INTEGER NOT NULL PRIMARY KEY,
    canal VARCHAR(50),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_canal_is_deleted ON staging.stg_canal_venta (is_deleted);

COMMENT ON TABLE staging.stg_canal_venta IS 'Staging de canales de venta con auditoría';

-- ============== TABLA: stg_tipo_gasto ==============
DROP TABLE IF EXISTS staging.stg_tipo_gasto CASCADE;

CREATE TABLE staging.stg_tipo_gasto (
    id_tipo_gasto INTEGER NOT NULL PRIMARY KEY,
    descripcion VARCHAR(150),
    monto_aproximado NUMERIC(15, 2),
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_stg_tipo_gasto_is_deleted ON staging.stg_tipo_gasto (is_deleted);

COMMENT ON TABLE staging.stg_tipo_gasto IS 'Staging de tipos de gasto con auditoría';

-- Verificar creación de tablas
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE
    table_schema = 'staging'
ORDER BY table_name;