"""
# ⚠️ dwh_init — Inicialización DESTRUCTIVA del Data Warehouse

**Este DAG BORRA TODO el DWH.** Ejecuta `sql/00_schemas/create_schemas.sql`,
que hace `DROP SCHEMA ... CASCADE` sobre `landing_zone`, `staging`,
`transformation` y `service`, y luego recrea todas las tablas (DDL) y
puebla `dim_tiempo`.

- Se ejecuta **solo manualmente** (`schedule=None`).
- Usalo la primera vez, o cuando quieras empezar de cero.
- Después ejecutá el DAG **`dwh_pipeline`** para cargar los datos.

Equivale a:
`python -m src.domain.pipeline.pipeline_orchestrator --create-schema --create-tables --only-init`
"""

from airflow import DAG
from airflow.operators.python import PythonOperator

from dwh_common import tasks
from dwh_common.config import DEFAULT_ARGS, START_DATE

with DAG(
    dag_id="dwh_init",
    description="⚠️ DESTRUCTIVO: borra y recrea schemas y tablas del DWH",
    doc_md=__doc__,
    schedule=None,
    start_date=START_DATE,
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["dwh", "init", "destructivo"],
) as dag:
    crear_schemas_y_tablas = PythonOperator(
        task_id="crear_schemas_y_tablas",
        python_callable=tasks.inicializar_dwh,
        doc_md="DROP + CREATE de los 4 schemas, DDL de todas las tablas y carga de dim_tiempo.",
    )
