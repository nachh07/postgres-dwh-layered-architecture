# 🚀 ETL Data Warehousing — PostgreSQL DWH Layered Architecture

Pipeline end-to-end de ingeniería de datos con arquitectura en 4 capas usando PostgreSQL, implementando MERGE con soft deletes y modelo dimensional (Star Schema).

## 📊 Estado del Proyecto

- 🗄️ **70,837 registros** en Staging
- 📦 **8 dimensiones** cargadas
- 📈 **3 hechos** poblados (66,824 transacciones totales)
- ⚡ **Pipeline dockerizado** — `docker compose up --build`
- 🌬️ **Orquestado con Apache Airflow 2.9.1** — DAGs `dwh_init` y `dwh_pipeline`
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
- [Orquestación con Airflow](#️-orquestación-con-airflow)
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

### Primera ejecución

```bash
# 1. Copiar variables de entorno (Docker Compose lee el .env de la RAÍZ)
copy config\.env.example .env
# Editar DB_PASSWORD y las variables AIRFLOW_* en .env

# 2. Levantar toda la infraestructura
docker compose up --build -d
```

Esto levanta:
1. `postgres` — Data Warehouse (PostgreSQL 17, con healthcheck)
2. `pgadmin` — UI de PostgreSQL en http://localhost:5050
3. `airflow-metadata`, `airflow-init`, `airflow-webserver`, `airflow-scheduler` — ver [Orquestación con Airflow](#️-orquestación-con-airflow)

Después, desde la UI de Airflow: ejecutar **`dwh_init`** (crea schemas y tablas) y luego **`dwh_pipeline`** (carga los datos).

### Pipeline sin Airflow (servicio `etl`, ejecución manual)

El servicio `etl` está detrás del profile `manual`, así que `docker compose up` no lo ejecuta.

```bash
# Pipeline completo (sin recrear tablas)
docker compose run --rm etl python -m src.domain.pipeline.pipeline_orchestrator

# ⚠️ Recrear schemas y tablas (DESTRUCTIVO) sin cargar datos
docker compose run --rm etl python -m src.domain.pipeline.pipeline_orchestrator --create-schema --create-tables --only-init
```

### Solo la base de datos (para conectar DBeaver/pgAdmin/Power BI)

```bash
docker compose up postgres
# Conectar en: localhost:5432 / data_engineering / postgres / <DB_PASSWORD>
```

---

## 🌬️ Orquestación con Airflow

Apache Airflow **2.9.1** (LocalExecutor) orquesta el mismo pipeline de `src/`, sin cambiar su lógica: cada paso es un `PythonOperator` y se ve por separado en la UI.

| Qué | Dónde |
|-----|-------|
| UI de Airflow | http://localhost:8080 — usuario `admin` / `admin` (desarrollo; se cambia con `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD`) |
| DAGs | `dags/dwh_init.py`, `dags/dwh_pipeline.py` |
| Callables y configuración | `dags/dwh_common/` (no importa Airflow: se testea en el CI) |
| Imagen | `docker/airflow/Dockerfile` + `docker/airflow/requirements.txt` |
| Metadata DB | contenedor `airflow-metadata` (PostgreSQL 16), **separado del DWH** |

### DAGs

**`dwh_init`** — ⚠️ **DESTRUCTIVO**, solo manual (`schedule=None`). Hace `DROP SCHEMA ... CASCADE` de `landing_zone`, `staging`, `transformation` y `service`, y recrea todas las tablas. Equivale a `--create-schema --create-tables --only-init`.

**`dwh_pipeline`** — diario (`@daily`, `catchup=False`, `max_active_runs=1`, `retries=1`):

```
verificar_csvs → cargar_landing → [staging: 10 MERGE en orden]
              → [dimensiones: 7 MERGE en paralelo]
              → [hechos: 3 MERGE, después de TODAS las dimensiones]
              → validar_conteos
```

- Los nombres y el orden de los scripts salen de las constantes de `staging_service.py` y `service_layer_service.py`: si se agrega un script ahí, aparece como un task nuevo.
- Los servicios de `src/` devuelven `False` ante un error. Cada task convierte ese `False` en una excepción: si no, Airflow lo marcaría en verde aunque haya fallado.
- `validar_conteos` compara `raw_ventas` con las `stg_ventas` activas, y cada hecho con los valores esperados de `dags/dwh_common/config.py` (`EXPECTED_FACT_COUNTS`).

### Primera ejecución

1. `docker compose up --build -d` y esperar a que `airflow-webserver` esté *healthy* (`docker compose ps`).
2. En la UI, activar y ejecutar **`dwh_init`** (▶ Trigger DAG).
3. Activar y ejecutar **`dwh_pipeline`**. Al activarlo, Airflow también lanza sola la corrida del último día (`catchup=False`).

Los DAGs se crean pausados. Si se activa `dwh_pipeline` antes de correr `dwh_init`, falla en `cargar_landing` porque las tablas no existen.

Por CLI:

```bash
docker exec dwh_airflow_scheduler airflow dags list-import-errors
docker exec dwh_airflow_scheduler airflow dags unpause dwh_init
docker exec dwh_airflow_scheduler airflow dags trigger dwh_init
docker exec dwh_airflow_scheduler airflow dags unpause dwh_pipeline
docker exec dwh_airflow_scheduler airflow dags trigger dwh_pipeline
```

### Variables de entorno de Airflow

Están en `config/.env.example` (copiar al `.env` de la raíz): `AIRFLOW_ADMIN_USER`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_METADATA_PASSWORD`, `AIRFLOW_FERNET_KEY` y `AIRFLOW_WEBSERVER_SECRET_KEY`. Las credenciales del DWH (`DB_*`) llegan a Airflow como variables de entorno; no se usan Connections de Airflow.

Generar la Fernet key:

```bash
docker run --rm apache/airflow:2.9.1-python3.11 python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Detalles de la integración

- La raíz del proyecto dentro del contenedor es `/opt/dwh` (`PYTHONPATH=/opt/dwh`). `src/`, `sql/` y `data/` se montan como solo lectura; `/opt/dwh/logs` es un volumen escribible, porque `Settings` crea `logs/` al importarse.
- Los logs de `src/` aparecen dentro del log de cada task en la UI.
- El mensaje `[WARN] No se encontró .env en: /opt/dwh/config/.env` es esperable: dentro del contenedor las credenciales llegan por variables de entorno.
- `docker compose down -v` borra **todos** los volúmenes, incluido el historial de Airflow. Para conservarlo, usar `docker compose down` sin `-v`.

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
├── dags/                         ← DAGs de Airflow
│   ├── dwh_init.py               ← ⚠️ Init destructivo (manual)
│   ├── dwh_pipeline.py           ← Pipeline diario
│   └── dwh_common/               ← Callables + config (sin Airflow)
│
├── tests/                        ← Suite de tests unitarios
│   ├── conftest.py               ← Fixtures compartidas (mocks)
│   ├── shared/
│   ├── infrastructure/
│   ├── domain/
│   └── dags/                     ← Estructura de DAGs (sin instalar Airflow)
│
├── data/                         ← CSVs fuente (10 archivos)
├── docker/
│   ├── init-db/01_init.sql       ← Init de PostgreSQL
│   └── airflow/                  ← Imagen de Airflow (Dockerfile + requirements)
│
├── config/
│   ├── .env                      ← Variables de entorno (no en Git)
│   ├── .env.example
│   └── requirements.txt
│
├── Dockerfile                    ← Imagen Python del pipeline
├── docker-compose.yml            ← postgres + pgadmin + Airflow (+ etl manual)
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
