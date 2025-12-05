-- =====================================================
-- Script: create_tables.sql (Landing Zone)
-- Description: Creación de tablas en landing_zone para datos crudos
-- Nota: Todos los campos son permisivos (TEXT/VARCHAR) para aceptar cualquier dato
-- =====================================================

-- ============== TABLA: raw_clientes ==============
DROP TABLE IF EXISTS landing_zone.raw_clientes CASCADE;
CREATE TABLE landing_zone.raw_clientes (
    id TEXT,
    provincia TEXT,
    nombre_y_apellido TEXT,
    domicilio TEXT,
    telefono TEXT,
    edad TEXT,
    localidad TEXT,
    x TEXT,  -- Longitud
    y TEXT,  -- Latitud
    fecha_alta TEXT,
    usuario_alta TEXT,
    fecha_ultima_modificacion TEXT,
    usuario_ultima_modificacion TEXT,
    marca_baja TEXT,
    col10 TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_clientes IS 'Tabla cruda de clientes desde CSV';

-- ============== TABLA: raw_ventas ==============
DROP TABLE IF EXISTS landing_zone.raw_ventas CASCADE;
CREATE TABLE landing_zone.raw_ventas (
    idventa TEXT,
    fecha TEXT,
    fecha_entrega TEXT,
    idcanal TEXT,
    idcliente TEXT,
    idsucursal TEXT,
    idempleado TEXT,
    idproducto TEXT,
    precio TEXT,
    cantidad TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_ventas IS 'Tabla cruda de ventas desde CSV';

-- ============== TABLA: raw_productos ==============
DROP TABLE IF EXISTS landing_zone.raw_productos CASCADE;
CREATE TABLE landing_zone.raw_productos (
    id_producto TEXT,
    concepto TEXT,
    tipo TEXT,
    precio TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_productos IS 'Tabla cruda de productos desde CSV';

-- ============== TABLA: raw_compras ==============
DROP TABLE IF EXISTS landing_zone.raw_compras CASCADE;
CREATE TABLE landing_zone.raw_compras (
    idcompra TEXT,
    fecha TEXT,
    idproducto TEXT,
    cantidad TEXT,
    precio TEXT,
    idproveedor TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_compras IS 'Tabla cruda de compras desde CSV';

-- ============== TABLA: raw_gastos ==============
DROP TABLE IF EXISTS landing_zone.raw_gastos CASCADE;
CREATE TABLE landing_zone.raw_gastos (
    idgasto TEXT,
    idsucursal TEXT,
    idtipogasto TEXT,
    fecha TEXT,
    monto TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_gastos IS 'Tabla cruda de gastos desde CSV';

-- ============== TABLA: raw_empleados ==============
DROP TABLE IF EXISTS landing_zone.raw_empleados CASCADE;
CREATE TABLE landing_zone.raw_empleados (
    id_empleado TEXT,
    apellido TEXT,
    nombre TEXT,
    sucursal TEXT,
    sector TEXT,
    cargo TEXT,
    salario TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_empleados IS 'Tabla cruda de empleados desde CSV';

-- ============== TABLA: raw_sucursales ==============
DROP TABLE IF EXISTS landing_zone.raw_sucursales CASCADE;
CREATE TABLE landing_zone.raw_sucursales (
    id TEXT,
    sucursal TEXT,
    direccion TEXT,
    localidad TEXT,
    provincia TEXT,
    latitud TEXT,
    longitud TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_sucursales IS 'Tabla cruda de sucursales desde CSV';

-- ============== TABLA: raw_proveedores ==============
DROP TABLE IF EXISTS landing_zone.raw_proveedores CASCADE;
CREATE TABLE landing_zone.raw_proveedores (
    idproveedor TEXT,
    nombre TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    departamen TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_proveedores IS 'Tabla cruda de proveedores desde CSV';

-- ============== TABLA: raw_canal_venta ==============
DROP TABLE IF EXISTS landing_zone.raw_canal_venta CASCADE;
CREATE TABLE landing_zone.raw_canal_venta (
    codigo TEXT,
    descripcion TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_canal_venta IS 'Tabla cruda de canales de venta desde CSV';

-- ============== TABLA: raw_tipo_gasto ==============
DROP TABLE IF EXISTS landing_zone.raw_tipo_gasto CASCADE;
CREATE TABLE landing_zone.raw_tipo_gasto (
    idtipogasto TEXT,
    descripcion TEXT,
    monto_aproximado TEXT,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landing_zone.raw_tipo_gasto IS 'Tabla cruda de tipos de gasto desde CSV';

-- Verificar creación de tablas
SELECT 
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'landing_zone'
ORDER BY table_name;
