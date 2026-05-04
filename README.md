# 🚀 ETL Data Warehousing — PostgreSQL DWH Layered Architecture

Pipeline end-to-end de ingeniería de datos con arquitectura en 4 capas usando PostgreSQL, implementando MERGE con soft deletes y modelo dimensional (Star Schema).

## 📊 Estado del Proyecto

- 🗄️ **70,837 registros** en Staging
- 📦 **8 dimensiones** cargadas
- 📈 **3 hechos** poblados (66,824 transacciones totales)
- ⚡ **Pipeline dockerizado** — `docker compose up --build`
- 🔄 **Soft deletes** implementados
- 📝 **Auditoría completa** en todas las tablas
- 🧪 **85%+ test coverage** con pytest
- 🤖 **CI/CD Automatizado** en GitHub Actions (Lint, Test, Docker Deploy)

---

## 📋 Tabla de Contenidos

- [Arquitectura de Código](#️-arquitectura-de-código)
- [Arquitectura de Datos](#️-arquitectura-de-datos)
- [Características Principales](#-características-principales)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Requisitos](#-requisitos)
- [Inicio Rápido con Docker](#-inicio-rápido-con-docker)
- [Desarrollo Local](#️-desarrollo-local)
- [Tests](#-tests)
- [Estructura del Proyecto](#-estructura-del-proyecto)

---

## 🏗️ Arquitectura de Código

El código Python sigue una arquitectura en 3 capas dentro de `src/`:

```
src/
├── shared/              ← Configuración, logger (sin dependencias de dominio)
│   ├── config/
│   │   ├── settings.py          ← Settings (frozen dataclass)
│   │   └── database_settings.py ← DatabaseSettings (frozen dataclass)
│   └── logger.py
│
├── infrastructure/      ← I/O externo: DB, archivos SQL
│   ├── database/
│   │   └── connection.py        ← DatabaseConnection (psycopg2 wrapping)
│   └── repositories/
│       └── sql_repository.py    ← SQLRepository (execute_file, truncate, count)
│
└── domain/              ← Lógica de negocio pura
    ├── models/
    │   └── pipeline_result.py   ← StepResult, PipelineResult (value objects)
    ├── services/
    │   ├── ingestion_service.py      ← CSV → Landing Zone
    │   ├── staging_service.py        ← Landing → Staging (MERGE)
    │   └── service_layer_service.py  ← Staging → DWH (MERGE dims + facts)
    └── pipeline/
        └── pipeline_orchestrator.py  ← Orquestador end-to-end
```

### Principios de diseño

- **Inyección de dependencias**: cada clase recibe sus dependencias por constructor
- **Inversión de dependencias**: `domain` no importa de `infrastructure` directamente (usa interfaces)
- **Inmutabilidad**: `Settings` y `DatabaseSettings` son `frozen=True`
- **Fail-fast**: el pipeline detiene la ejecución ante el primer error crítico

---

## 🏗️ Arquitectura de Datos

```
CSV FILES (10 archivos)
        │ COPY de PostgreSQL
        ▼
┌────────────────────────────────┐
│  CAPA 1: LANDING ZONE          │  10 tablas raw_* (tipos TEXT)
└───────────────┬────────────────┘
                │ MERGE (INSERT / UPDATE / Soft Delete)
                ▼
┌────────────────────────────────┐
│  CAPA 2: STAGING               │  10 tablas stg_* + auditoría
└───────────────┬────────────────┘
                │ Transformaciones
                ▼
┌────────────────────────────────┐
│  CAPA 3: TRANSFORMATION        │  (reservada para futuras transformaciones)
└───────────────┬────────────────┘
                │ MERGE a Star Schema
                ▼
┌────────────────────────────────┐
│  CAPA 4: SERVICE / DWH         │  8 dimensiones + 3 hechos (Star Schema)
└────────────────────────────────┘
```

---

## ✨ Características Principales

### 🔄 MERGE con 3 Casos

```sql
WHEN MATCHED                   → UPDATE (actualizar y reactivar)
WHEN NOT MATCHED               → INSERT (nuevos registros)
WHEN NOT MATCHED BY SOURCE     → Soft Delete (is_deleted = TRUE)
```

### 📝 Auditoría Completa

Todas las tablas de staging y service incluyen: `created_at`, `updated_at`, `is_deleted`, `deleted_at`

### 🧪 Tests unitarios

- **78 tests** con mocks (sin base de datos real)
- **85%+ de cobertura**
- Ejecutables con `python -m pytest`

---

## 🤖 CI/CD Pipeline

El proyecto cuenta con un flujo completo de Integración Continua y Despliegue Continuo usando **GitHub Actions**.

### Workflows Automatizados

1. **Linting & Code Quality**: Validación de formato y estilo con `ruff` en cada Push/PR.
2. **Testing (Unit + Integration)**:
   - Tests Unitarios con +80% de code coverage forzado.
   - Tests de Integración utilizando un contenedor `postgres:17-alpine` dinámico en GitHub Actions.
3. **Docker Build & Push**: Al hacer push a la rama `main`, si pasan los tests, se construye y pushea automáticamente una imagen multi-stage (`builder` -> `runtime`) optimizada hacia **Docker Hub**.

---

## 📦 Requisitos

Para **Docker** (recomendado): Docker Desktop  
Para **local**: Python 3.11+, PostgreSQL 12+

---

## 🐳 Inicio Rápido con Docker

### Primera ejecución (crea schemas, tablas y carga datos)

```bash
# 1. Copiar variables de entorno
copy config\.env.example config\.env
# Editar DB_PASSWORD en config/.env

# 2. Levantar toda la infraestructura
docker compose up --build
```

Esto levanta:
1. `postgres` — PostgreSQL 15 (con healthcheck)
2. `etl` — Pipeline Python (espera a que Postgres esté listo)

### Ejecuciones incrementales

```bash
# Solo el pipeline (sin recrear tablas)
docker compose run --rm etl python -m src.domain.pipeline.pipeline_orchestrator
```

### Solo la base de datos (para conectar DBeaver/pgAdmin/Power BI)

```bash
docker compose up postgres
# Conectar en: localhost:5432 / data_engineering / postgres / <DB_PASSWORD>
```

---

## 🛠️ Desarrollo Local

### 1. Instalar dependencias

```bash
pip install -r config/requirements.txt
```

### 2. Configurar variables de entorno

```bash
copy config\.env.example config\.env
# Editar config/.env con tus credenciales de PostgreSQL
```

### 3. Ejecutar pipeline (primera vez)

```bash
python -m src.domain.pipeline.pipeline_orchestrator --create-schema --create-tables
```

### 4. Ejecuciones incrementales

```bash
python -m src.domain.pipeline.pipeline_orchestrator
```

---

## 🧪 Tests

```bash
# Ejecutar todos los tests con reporte de cobertura
python -m pytest

# Solo un módulo
python -m pytest tests/domain/test_ingestion_service.py -v

# Ver reporte HTML de cobertura
start htmlcov/index.html
```

**Cobertura actual**: 85%+ (umbral mínimo: 80%)

| Módulo | Cobertura |
|--------|-----------|
| `infrastructure/database/connection.py` | 100% |
| `infrastructure/repositories/sql_repository.py` | 100% |
| `domain/services/ingestion_service.py` | 100% |
| `domain/services/staging_service.py` | 100% |
| `shared/config/settings.py` | 100% |

---

## 📁 Estructura del Proyecto

```
postgres-dwh-layered-architecture/
│
├── src/                          ← Código Python refactorizado
│   ├── shared/                   ← Configuración compartida
│   ├── infrastructure/           ← Conexión DB y repositorios SQL
│   └── domain/                   ← Lógica de negocio y orquestador
│
├── sql/                          ← Scripts SQL (DDL + DML MERGE)
│   ├── 00_schemas/
│   ├── 01_landing/
│   ├── 02_staging/
│   └── 04_service/
│
├── tests/                        ← Suite de tests unitarios
│   ├── conftest.py               ← Fixtures compartidas (mocks)
│   ├── shared/
│   ├── infrastructure/
│   └── domain/
│
├── data/                         ← CSVs fuente (10 archivos)
├── docker/
│   └── init-db/01_init.sql       ← Init de PostgreSQL
│
├── config/
│   ├── .env                      ← Variables de entorno (no en Git)
│   ├── .env.example
│   └── requirements.txt
│
├── Dockerfile                    ← Imagen Python del pipeline
├── docker-compose.yml            ← Orquesta postgres + etl
├── pyproject.toml                ← Configuración de pytest + coverage
├── .dockerignore
└── README.md
```

---

## 📊 Datos Cargados

| Tabla | Registros |
|-------|-----------|
| stg_clientes | 3,407 |
| stg_ventas | 46,645 |
| stg_productos | 291 |
| stg_compras | 11,539 |
| stg_gastos | 8,640 |
| stg_empleados | 267 |
| stg_sucursales | 31 |
| stg_proveedores | 14 |
| stg_canal_venta | 3 |
| stg_tipo_gasto | 4 |

**DWH**: 8 dimensiones + 3 hechos (66,824 transacciones totales)

---

## 🔍 Queries de Ejemplo

### Top 10 Productos más vendidos

```sql
SELECT p.producto, SUM(fv.cantidad) AS total_vendido, SUM(fv.monto_total) AS ingresos_totales
FROM service.fact_ventas fv
JOIN service.dim_producto p ON fv.sk_producto = p.sk_producto
GROUP BY p.producto
ORDER BY ingresos_totales DESC
LIMIT 10;
```

### Ventas por Mes

```sql
SELECT t.anio, t.mes_nombre, COUNT(*) AS cantidad_ventas, SUM(fv.monto_total) AS monto_total
FROM service.fact_ventas fv
JOIN service.dim_tiempo t ON fv.sk_tiempo_venta = t.sk_tiempo
GROUP BY t.anio, t.mes, t.mes_nombre
ORDER BY t.anio, t.mes;
```

---

## 👥 Autor

**Nachh07** — Data Engineering Team  
Educación IT - Curso Data Engineering
