# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

End-to-end ETL pipeline implementing a 4-layer Data Warehouse using Python and PostgreSQL. Data flows from CSV files through Landing → Staging → DWH (Star Schema with 8 dimensions and 3 facts). The pipeline is containerized with Docker Compose and orchestrated with Apache Airflow 2.9.1 (LocalExecutor). This is a teaching project: DAG clarity in the UI beats optimization.

## Commands

### Docker (primary workflow)
```bash
# Start everything: DWH postgres, pgAdmin, Airflow (metadata DB, init, webserver, scheduler)
docker compose up --build -d

# Airflow UI: http://localhost:8080  (dev credentials admin / admin)
# pgAdmin:    http://localhost:5050  (admin@admin.com / admin)

# Order on a fresh DB: dwh_init FIRST, then dwh_pipeline
docker exec dwh_airflow_scheduler airflow dags unpause dwh_init
docker exec dwh_airflow_scheduler airflow dags trigger dwh_init       # ⚠️ DROPS the whole DWH
docker exec dwh_airflow_scheduler airflow dags unpause dwh_pipeline
docker exec dwh_airflow_scheduler airflow dags trigger dwh_pipeline

# DAG import errors (must be empty)
docker exec dwh_airflow_scheduler airflow dags list-import-errors

# Pipeline without Airflow — `etl` service is behind the "manual" profile (not started by `up`)
docker compose run --rm etl python -m src.domain.pipeline.pipeline_orchestrator

# Start only the database (for local Python dev)
docker compose up postgres
```

`docker compose down -v` wipes ALL volumes (DWH, Airflow metadata/history, logs).

### Local Python development
```bash
pip install -r config/requirements.txt

# Copy and fill in DB credentials
cp config/.env.example config/.env

# First run: create schemas + tables + load data
python -m src.domain.pipeline.pipeline_orchestrator --create-schema --create-tables

# Subsequent runs (schema exists)
python -m src.domain.pipeline.pipeline_orchestrator

# Only initialize schema/tables, skip data load
python -m src.domain.pipeline.pipeline_orchestrator --only-init
```

### Testing
```bash
# All tests with coverage report (minimum 80% enforced)
python -m pytest

# Single test file
python -m pytest tests/domain/test_ingestion_service.py -v

# Open HTML coverage report (Windows)
start htmlcov/index.html
```

## Architecture

### Code layers (src/)
Three layers with one-way dependencies (`domain → infrastructure → shared`):

- **shared/** — `config/settings.py` (paths, CSV-to-table mappings), `config/database_settings.py` (loads `.env`), `logger.py`
- **infrastructure/** — `database/connection.py` (psycopg2 wrapper with context managers), `repositories/sql_repository.py` (executes SQL files or strings, counts, truncates)
- **domain/** — pure business logic with no I/O; `services/` contains the three ETL services; `pipeline/pipeline_orchestrator.py` wires them together and owns CLI args

### Data layers (PostgreSQL schemas)
```
CSV files → landing_zone (raw_*)
         → staging (stg_*, MERGE with soft deletes + audit columns)
         → service / dwh (dim_* and fact_* Star Schema)
```
Layer 3 (transformation) is reserved/empty. SQL scripts for each layer live under `sql/01_landing/`, `sql/02_staging/`, `sql/04_service/`.

### Pipeline execution order
`PipelineOrchestrator` always runs: create schemas → create tables → `IngestionService` (CSV → landing via COPY) → `StagingService` (landing → staging, 10 MERGEs in dependency order) → `ServiceLayerService` (staging → DWH, 7 dimension MERGEs then 3 fact MERGEs).

Fail-fast: any step failure stops the pipeline; exit code 1.

### Key implementation details
- CSV ingestion uses PostgreSQL `COPY` for bulk load; `IngestionService` auto-detects delimiters (comma vs. semicolon) and handles Latin1 encoding.
- All staging MERGEs implement three-case logic: INSERT new, UPDATE changed, soft-delete missing (sets `is_deleted`, `deleted_at`).
- `DatabaseConnection` uses context managers (`with conn:`, `with conn.cursor()`) for automatic commit/rollback.
- `SQLRepository.execute_file()` reads and runs arbitrary `.sql` files; services call it in a fixed order to respect FK constraints.

### Airflow orchestration
- **`dwh_init`** (`dags/dwh_init.py`): manual only (`schedule=None`). ⚠️ DESTRUCTIVE — runs `create_schemas.sql` (`DROP SCHEMA ... CASCADE` on all 4 schemas) and recreates all tables via `PipelineOrchestrator().run(create_schema=True, create_tables=True, only_init=True)`.
- **`dwh_pipeline`** (`dags/dwh_pipeline.py`): `@daily`, `catchup=False`, `max_active_runs=1`, `retries=1`. `verificar_csvs → cargar_landing → TaskGroup staging (sequential) → TaskGroup dimensiones (parallel) → TaskGroup hechos (after ALL dims) → validar_conteos`. One task per MERGE script, built from the public aliases `STAGING_MERGE_SCRIPTS`, `DIMENSION_MERGE_SCRIPTS`, `FACT_MERGE_SCRIPTS` in the service modules.
- **`dags/dwh_common/`** holds the callables (`tasks.py`) and config (`config.py`, incl. `EXPECTED_FACT_COUNTS` for the final validation). It must NOT import Airflow so it stays testable in CI; it is excluded from DAG parsing via `dags/.airflowignore`.
- **Error semantics (critical):** `src/` services and `SQLRepository.execute_file` return `False` instead of raising. Every callable must turn `False` into an exception (`ensure()` → `PipelineStepError`), otherwise Airflow marks the task green.
- **Container layout:** image `docker/airflow/Dockerfile` (`apache/airflow:2.9.1-python3.11`, own `docker/airflow/requirements.txt` installed with the official constraints file — never add Airflow to `config/requirements.txt`). Project root is `/opt/dwh` (`PYTHONPATH=/opt/dwh`): `src/`, `sql/`, `data/` mounted read-only, `/opt/dwh/logs` is a writable volume because `Settings.__post_init__` creates `logs/`. DAGs mounted at `/opt/airflow/dags`.
- Airflow metadata lives in its own `airflow-metadata` container (Postgres 16), separate from the DWH. DWH credentials reach Airflow as `DB_*` env vars (no Airflow Connections). Timezone: America/Argentina/Buenos_Aires.

### Testing approach
All tests mock at the psycopg2 level — no real database needed. `conftest.py` in each test subdirectory provides shared fixtures. Coverage is tracked by module; `pytest-cov` enforces the 80% minimum via `pyproject.toml`. `tests/dags/` tests DAG structure WITHOUT installing Airflow: `tests/dags/conftest.py` puts `dags/` on `sys.path` and installs minimal fakes of `DAG`/`PythonOperator`/`TaskGroup`/`chain` into `sys.modules`. Integration tests (`-m integration`) need a running Postgres.

Lint: CI runs `ruff check .` (line-length 100; E,W,F,I,B,UP). isort treats `airflow` as third-party and `src`, `dwh_common` as first-party.

## Environment
Docker Compose reads the **root** `.env` (copy from `config/.env.example`). It holds `DB_*` plus `AIRFLOW_ADMIN_USER`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_METADATA_PASSWORD`, `AIRFLOW_FERNET_KEY`, `AIRFLOW_WEBSERVER_SECRET_KEY`. For local runs, `database_settings.py` loads `config/.env` first, falling back to the root `.env`, via `python-dotenv`. Generate a Fernet key with:
`docker run --rm apache/airflow:2.9.1-python3.11 python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

Repo files are CRLF in the working tree (Windows, `core.autocrlf=true`); any shell script/entrypoint must be LF.