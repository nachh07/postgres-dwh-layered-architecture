-- Verificar empleados duplicados
SELECT
    id_empleado,
    COUNT(*) as cantidad,
    STRING_AGG(DISTINCT sucursal, ', ') as sucursales
FROM landing_zone.raw_empleados
GROUP BY
    id_empleado
HAVING
    COUNT(*) > 1
ORDER BY cantidad DESC;