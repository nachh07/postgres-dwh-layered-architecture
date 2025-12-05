-- =====================================================
-- Script: create_facts.sql (Service Layer)
-- Description: Creación de tablas de hechos para el modelo dimensional
-- =====================================================

-- ============== HECHO: fact_ventas ==============
DROP TABLE IF EXISTS service.fact_ventas CASCADE;

CREATE TABLE service.fact_ventas (
    sk_venta SERIAL PRIMARY KEY,
    id_venta INTEGER NOT NULL UNIQUE,
    -- Foreign Keys (Surrogate Keys de dimensiones)
    sk_cliente INTEGER NOT NULL,
    sk_producto INTEGER NOT NULL,
    sk_sucursal INTEGER NOT NULL,
    sk_empleado INTEGER, -- NULLABLE: puede ser NULL si empleado no existe en esa sucursal
    sk_tiempo_venta INTEGER NOT NULL,
    sk_tiempo_entrega INTEGER NOT NULL,
    sk_canal INTEGER NOT NULL,
    -- Métricas (medidas)
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(15, 3) NOT NULL,
    monto_total NUMERIC(15, 3) NOT NULL,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Foreign Key Constraints
    -- Nota: dim_empleado tiene clave compuesta, por lo que no se puede crear FK directa
    CONSTRAINT fk_fact_ventas_cliente FOREIGN KEY (sk_cliente) REFERENCES service.dim_cliente (sk_cliente),
    CONSTRAINT fk_fact_ventas_producto FOREIGN KEY (sk_producto) REFERENCES service.dim_producto (sk_producto),
    CONSTRAINT fk_fact_ventas_sucursal FOREIGN KEY (sk_sucursal) REFERENCES service.dim_sucursal (sk_sucursal),
    CONSTRAINT fk_fact_ventas_tiempo_venta FOREIGN KEY (sk_tiempo_venta) REFERENCES service.dim_tiempo (sk_tiempo),
    CONSTRAINT fk_fact_ventas_tiempo_entrega FOREIGN KEY (sk_tiempo_entrega) REFERENCES service.dim_tiempo (sk_tiempo),
    CONSTRAINT fk_fact_ventas_canal FOREIGN KEY (sk_canal) REFERENCES service.dim_canal (sk_canal)
);

CREATE INDEX idx_fact_ventas_cliente ON service.fact_ventas (sk_cliente);

CREATE INDEX idx_fact_ventas_producto ON service.fact_ventas (sk_producto);

CREATE INDEX idx_fact_ventas_sucursal ON service.fact_ventas (sk_sucursal);

CREATE INDEX idx_fact_ventas_tiempo_venta ON service.fact_ventas (sk_tiempo_venta);

COMMENT ON TABLE service.fact_ventas IS 'Tabla de hechos de ventas - Grain: Una venta por registro';

-- ============== HECHO: fact_compras ==============
DROP TABLE IF EXISTS service.fact_compras CASCADE;

CREATE TABLE service.fact_compras (
    sk_compra SERIAL PRIMARY KEY,
    id_compra INTEGER NOT NULL UNIQUE,
    -- Foreign Keys
    sk_producto INTEGER NOT NULL,
    sk_proveedor INTEGER NOT NULL,
    sk_tiempo INTEGER NOT NULL,
    -- Métricas
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(15, 3) NOT NULL,
    monto_total NUMERIC(15, 3) NOT NULL,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Foreign Key Constraints
    CONSTRAINT fk_fact_compras_producto FOREIGN KEY (sk_producto) REFERENCES service.dim_producto (sk_producto),
    CONSTRAINT fk_fact_compras_proveedor FOREIGN KEY (sk_proveedor) REFERENCES service.dim_proveedor (sk_proveedor),
    CONSTRAINT fk_fact_compras_tiempo FOREIGN KEY (sk_tiempo) REFERENCES service.dim_tiempo (sk_tiempo)
);

CREATE INDEX idx_fact_compras_producto ON service.fact_compras (sk_producto);

CREATE INDEX idx_fact_compras_proveedor ON service.fact_compras (sk_proveedor);

CREATE INDEX idx_fact_compras_tiempo ON service.fact_compras (sk_tiempo);

COMMENT ON TABLE service.fact_compras IS 'Tabla de hechos de compras - Grain: Una compra por registro';

-- ============== HECHO: fact_gastos ==============
DROP TABLE IF EXISTS service.fact_gastos CASCADE;

CREATE TABLE service.fact_gastos (
    sk_gasto SERIAL PRIMARY KEY,
    id_gasto INTEGER NOT NULL UNIQUE,
    -- Foreign Keys
    sk_sucursal INTEGER NOT NULL,
    sk_tiempo INTEGER NOT NULL,
    sk_tipo_gasto INTEGER NOT NULL,
    -- Métricas
    monto NUMERIC(15, 2) NOT NULL,
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Foreign Key Constraints
    CONSTRAINT fk_fact_gastos_sucursal FOREIGN KEY (sk_sucursal) REFERENCES service.dim_sucursal (sk_sucursal),
    CONSTRAINT fk_fact_gastos_tiempo FOREIGN KEY (sk_tiempo) REFERENCES service.dim_tiempo (sk_tiempo),
    CONSTRAINT fk_fact_gastos_tipo_gasto FOREIGN KEY (sk_tipo_gasto) REFERENCES service.dim_tipo_gasto (sk_tipo_gasto)
);

CREATE INDEX idx_fact_gastos_sucursal ON service.fact_gastos (sk_sucursal);

CREATE INDEX idx_fact_gastos_tiempo ON service.fact_gastos (sk_tiempo);

CREATE INDEX idx_fact_gastos_tipo_gasto ON service.fact_gastos (sk_tipo_gasto);

COMMENT ON TABLE service.fact_gastos IS 'Tabla de hechos de gastos - Grain: Un gasto por registro';

-- Verificar creación de hechos
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE
    table_schema = 'service'
    AND table_name LIKE 'fact_%'
ORDER BY table_name;