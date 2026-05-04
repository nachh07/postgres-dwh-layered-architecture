# 📝 Guía Paso a Paso - Pipeline Data Engineering

Esta guía te llevará desde cero hasta tener el pipeline completamente funcional.

---

## ✅ Pre-requisitos

Antes de comenzar, asegúrate de tener:

- [x] PostgreSQL 12+ instalado y corriendo
- [x] Python 3.8+ instalado
- [x] Git instalado (opcional, para control de versiones)
- [x] Editor de código (VS Code, PyCharm, etc.)

---

## 📋 Paso 1: Preparar el Entorno

### 1.1 Verificar PostgreSQL

Abre una terminal y ejecuta:

```bash
psql --version
```

Deberías ver algo como: `psql (PostgreSQL) 15.x`

### 1.2 Verificar Python

```bash
python --version
```

Deberías ver: `Python 3.8.x` o superior

---

## 📋 Paso 2: Configurar la Base de Datos

### 2.1 Crear la base de datos

Conéctate a PostgreSQL y ejecuta:

```sql
CREATE DATABASE data_engineering;
```

### 2.2 Verificar conexión

```bash
psql -U postgres -d data_engineering
```

Si te conectas exitosamente, escribe `\q` para salir.

---

## 📋 Paso 3: Configurar el Proyecto

### 3.1 Instalar dependencias Python

Desde el directorio raíz del proyecto:

```bash
pip install -r config/requirements.txt
```

**Dependencias instaladas**:
- `psycopg2-binary` - Driver PostgreSQL
- `python-dotenv` - Manejo de variables de entorno

### 3.2 Configurar variables de entorno

1. Copiar el archivo de ejemplo:

```bash
copy config\.env.example config\.env
```

2. Editar `config/.env` con tus credenciales:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=data_engineering
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_AQUI
```

⚠️ **IMPORTANTE**: Reemplaza `TU_PASSWORD_AQUI` con tu contraseña de PostgreSQL.

### 3.3 Verificar archivos CSV

Asegúrate de que el directorio `data/` contenga los 10 archivos:

- ✅ Clientes.csv
- ✅ Venta.csv
- ✅ Productos.csv
- ✅ Compra.csv
- ✅ Gasto.csv
- ✅ Empleados.csv
- ✅ Sucursales.csv
- ✅ Proveedores.csv
- ✅ CanalDeVenta.csv
- ✅ TiposDeGasto.csv

---

## 📋 Paso 4: Ejecutar el Pipeline (Primera vez)

### 4.1 Ejecución completa

Desde el directorio raíz del proyecto:

```bash
python python\orchestration\run_pipeline.py --create-schema --create-tables
```

### 4.2 ¿Qué hace este comando?

El pipeline ejecutará automáticamente:

1. **Creación de Schemas** (5 segundos)
   - `landing_zone`
   - `staging`
   - `transformation`
   - `service`

2. **Creación de Tablas** (10 segundos)
   - 10 tablas en `landing_zone`
   - 10 tablas en `staging`
   - 8 dimensiones + 3 hechos en `service`

3. **Población de dim_tiempo** (5 segundos)
   - 4,018 fechas desde 2015 hasta 2025

4. **Carga de CSVs** (15 segundos)
   - 70,837 registros en total

5. **MERGE a Staging** (20 segundos)
   - 10 MERGEs con INSERT/UPDATE/Soft Delete

6. **MERGE a Service** (30 segundos)
   - 7 MERGEs de dimensiones
   - 3 MERGEs de hechos

**⏱️ Tiempo total**: ~1-2 minutos

### 4.3 Salida esperada

Deberías ver logs como:

```
================================================================================
INICIANDO PIPELINE DE DATA ENGINEERING
================================================================================
PASO 0: Creando schemas
✅ Creando schemas - Completado
PASO 1a: Creando tablas de Landing Zone
✅ Creando tablas de landing_zone - Completado
...
✅ PIPELINE COMPLETADO EXITOSAMENTE
   Tiempo de ejecucion: 0:01:23
================================================================================
```

---

## 📋 Paso 5: Verificar la Carga

### 5.1 Conectarse a PostgreSQL

```bash
psql -U postgres -d data_engineering
```

### 5.2 Verificar schemas creados

```sql
\dn
```

Deberías ver:
```
        List of schemas
       Name        |  Owner   
-------------------+----------
 landing_zone      | postgres
 public            | postgres
 service           | postgres
 staging           | postgres
 transformation    | postgres
```

### 5.3 Verificar tablas en staging

```sql
SELECT 
    table_name,
    (SELECT COUNT(*) FROM staging."stg_" || substring(table_name from 5)) as registros
FROM information_schema.tables
WHERE table_schema = 'staging'
ORDER BY table_name;
```

### 5.4 Verificar conteos

```sql
-- Staging
SELECT 'stg_clientes' AS tabla, COUNT(*) AS registros FROM staging.stg_clientes WHERE is_deleted = FALSE
UNION ALL
SELECT 'stg_ventas', COUNT(*) FROM staging.stg_ventas WHERE is_deleted = FALSE
UNION ALL
SELECT 'stg_productos', COUNT(*) FROM staging.stg_productos WHERE is_deleted = FALSE;

-- Service
SELECT 'dim_cliente' AS tabla, COUNT(*) AS registros FROM service.dim_cliente
UNION ALL
SELECT 'fact_ventas', COUNT(*) FROM service.fact_ventas;
```

**Conteos esperados**:
- `stg_clientes`: 3,407
- `stg_ventas`: 46,645
- `stg_productos`: 291
- `dim_cliente`: 3,407
- `fact_ventas`: 46,645

---

## 📋 Paso 6: Ejecuciones Incrementales

Una vez que las tablas están creadas, las siguientes ejecuciones son más rápidas:

```bash
python python\orchestration\run_pipeline.py
```

Este comando:
- ✅ Trunca tablas de landing
- ✅ Carga CSVs
- ✅ Ejecuta MERGEs a staging
- ✅ Ejecuta MERGEs a service

⏱️ **Tiempo**: ~30 segundos

---

## 📋 Paso 7: Probar Soft Deletes

### 7.1 Ejecutar carga inicial

```bash
python python\orchestration\run_pipeline.py
```

### 7.2 Modificar un CSV

Abre `data/Clientes.csv` y **elimina las últimas 5 filas**.

### 7.3 Re-ejecutar el pipeline

```bash
python python\orchestration\run_pipeline.py
```

### 7.4 Verificar soft deletes

```sql
SELECT 
    id_cliente,
    nombre_apellido,
    is_deleted,
    deleted_at,
    updated_at
FROM staging.stg_clientes
WHERE is_deleted = TRUE
ORDER BY deleted_at DESC
LIMIT 10;
```

**Resultado esperado**: Verás 5 registros con:
- `is_deleted = TRUE`
- `deleted_at` con timestamp reciente
- `updated_at` = `deleted_at`

---

## 📋 Paso 8: Ejecutar Consultas Analíticas

### 8.1 Top 10 productos más vendidos

```sql
SELECT 
    p.producto,
    p.tipo_producto,
    SUM(fv.cantidad) AS total_vendido,
    ROUND(SUM(fv.monto_total), 2) AS ingresos_totales
FROM service.fact_ventas fv
JOIN service.dim_producto p ON fv.sk_producto = p.sk_producto
GROUP BY p.producto, p.tipo_producto
ORDER BY ingresos_totales DESC
LIMIT 10;
```

### 8.2 Ventas por mes y año

```sql
SELECT 
    t.anio,
    t.mes_nombre,
    COUNT(*) AS cantidad_ventas,
    ROUND(SUM(fv.monto_total), 2) AS monto_total
FROM service.fact_ventas fv
JOIN service.dim_tiempo t ON fv.sk_tiempo_venta = t.sk_tiempo
GROUP BY t.anio, t.mes, t.mes_nombre
ORDER BY t.anio, t.mes;
```

### 8.3 Ventas por sucursal y provincia

```sql
SELECT 
    s.provincia,
    s.sucursal,
    COUNT(*) AS cantidad_ventas,
    ROUND(SUM(fv.monto_total), 2) AS monto_total
FROM service.fact_ventas fv
JOIN service.dim_sucursal s ON fv.sk_sucursal = s.sk_sucursal
GROUP BY s.provincia, s.sucursal
ORDER BY monto_total DESC;
```

---

## 🐛 Troubleshooting Común

### Error: "fe_sendauth: no password supplied"

**Causa**: El archivo `.env` no existe o está mal configurado.

**Solución**:
```bash
# Verificar que existe
dir config\.env

# Si no existe, crear desde el ejemplo
copy config\.env.example config\.env

# Editar y agregar password
notepad config\.env
```

### Error: "psycopg2.OperationalError: could not connect"

**Causa**: PostgreSQL no está corriendo o las credenciales son incorrectas.

**Solución**:
```bash
# Verificar que PostgreSQL está corriendo
pg_ctl status

# Verificar conexión manual
psql -U postgres -d data_engineering
```

### Error: "relation does not exist"

**Causa**: Las tablas no se han creado.

**Solución**:
```bash
# Ejecutar con flags de creación
python python\orchestration\run_pipeline.py --create-schema --create-tables
```

### Error: "duplicate key value violates unique constraint"

**Causa**: Intentando insertar un registro que ya existe.

**Solución**:
```sql
-- Truncar tablas de service y re-ejecutar
TRUNCATE TABLE service.fact_ventas CASCADE;
TRUNCATE TABLE service.dim_cliente CASCADE;
```

---

## ✅ Checklist Final

Antes de considerar el proyecto completo, verifica:

- [ ] PostgreSQL instalado y corriendo
- [ ] Python 3.8+ instalado
- [ ] Dependencias instaladas (`pip install -r`)
- [ ] Archivo `.env` configurado con credenciales
- [ ] 10 archivos CSV en `data/`
- [ ] Pipeline ejecutado exitosamente
- [ ] 4 schemas creados en PostgreSQL
- [ ] 70,837 registros en staging
- [ ] 8 dimensiones pobladas en service
- [ ] 3 hechos poblados en service
- [ ] Queries analíticas funcionando
- [ ] Soft deletes probados y funcionando

---

## 🎉 ¡Felicitaciones!

Has completado exitosamente el pipeline de Data Engineering end-to-end.

**Próximos pasos sugeridos**:
- Conectar Power BI / Tableau al DWH
- Crear dashboards analíticos
- Implementar más transformaciones en la capa `transformation`
- Agregar testing automatizado
- Documentar business logic

---

## 📚 Recursos Adicionales

- [Documentación PostgreSQL](https://www.postgresql.org/docs/)
- [Psycopg2 Tutorial](https://www.psycopg.org/docs/)
- [Star Schema Design](https://en.wikipedia.org/wiki/Star_schema)
- [Slowly Changing Dimensions](https://en.wikipedia.org/wiki/Slowly_changing_dimension)
