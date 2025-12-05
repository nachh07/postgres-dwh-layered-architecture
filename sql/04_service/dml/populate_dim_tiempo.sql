-- =====================================================
-- Script: populate_dim_tiempo.sql
-- Description: Poblar dimensión tiempo con fechas desde 2015 hasta 2025
-- =====================================================

-- Función para generar dimensión tiempo
CREATE OR REPLACE FUNCTION service.populate_dim_tiempo(
    fecha_inicio DATE,
    fecha_fin DATE
)
RETURNS VOID AS $$
DECLARE
    fecha_actual DATE;
BEGIN
    fecha_actual := fecha_inicio;
    
    WHILE fecha_actual <= fecha_fin LOOP
        INSERT INTO service.dim_tiempo (
            fecha,
            anio,
            mes,
            dia,
            trimestre,
            semana,
            dia_nombre,
            mes_nombre,
            es_fin_semana
        )
        VALUES (
            fecha_actual,
            EXTRACT(YEAR FROM fecha_actual),
            EXTRACT(MONTH FROM fecha_actual),
            EXTRACT(DAY FROM fecha_actual),
            EXTRACT(QUARTER FROM fecha_actual),
            EXTRACT(WEEK FROM fecha_actual),
            TO_CHAR(fecha_actual, 'TMDay'),
            TO_CHAR(fecha_actual, 'TMMonth'),
            CASE WHEN EXTRACT(DOW FROM fecha_actual) IN (0, 6) THEN TRUE ELSE FALSE END
        )
        ON CONFLICT (fecha) DO NOTHING;
        
        fecha_actual := fecha_actual + INTERVAL '1 day';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Ejecutar población de dimensión tiempo
SELECT service.populate_dim_tiempo('2015-01-01'::DATE, '2025-12-31'::DATE);

-- Verificar
SELECT 
    MIN(fecha) AS fecha_min,
    MAX(fecha) AS fecha_max,
    COUNT(*) AS total_dias
FROM service.dim_tiempo;
