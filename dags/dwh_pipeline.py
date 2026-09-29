"""
# dwh_pipeline — Carga diaria del Data Warehouse

Orquesta el pipeline existente (`src/`) paso a paso:

1. **verificar_csvs**: comprueba que estén todos los CSV de `data/`.
2. **cargar_landing**: CSV → `landing_zone` (TRUNCATE + COPY).
3. **staging**: un task por script MERGE, en orden de dependencia.
4. **dimensiones**: un task por dimensión, en paralelo (son independientes).
5. **hechos**: arrancan cuando terminaron TODAS las dimensiones (por las FK).
6. **validar_conteos**: compara conteos reales contra los esperados.

Requisito: haber ejecutado antes el DAG **`dwh_init`** (crea schemas y tablas).

Los nombres y el orden de los scripts salen de las constantes de
`staging_service.py` y `service_layer_service.py`: si se agrega un script ahí,
aparece solo como un task nuevo.
"""

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from dwh_common import tasks
from dwh_common.config import DEFAULT_ARGS, START_DATE
from src.domain.services.service_layer_service import (
    DIMENSION_MERGE_SCRIPTS,
    FACT_MERGE_SCRIPTS,
)
from src.domain.services.staging_service import STAGING_MERGE_SCRIPTS


def _task_id(script_name: str) -> str:
    """'merge_dim_cliente.sql' → 'dim_cliente'."""
    return script_name.removeprefix("merge_").removesuffix(".sql")


def _merge_task(script_name: str, callable_, sql_dir: str) -> PythonOperator:
    """Crea un PythonOperator que ejecuta un script MERGE."""
    return PythonOperator(
        task_id=_task_id(script_name),
        python_callable=callable_,
        op_kwargs={"script_name": script_name},
        doc_md=f"Ejecuta `sql/{sql_dir}/{script_name}`.",
    )


with DAG(
    dag_id="dwh_pipeline",
    description="CSV → landing → staging → DWH (estrella) + validación de conteos",
    doc_md=__doc__,
    schedule="@daily",
    start_date=START_DATE,
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["dwh", "etl"],
) as dag:
    verificar_csvs = PythonOperator(
        task_id="verificar_csvs",
        python_callable=tasks.verificar_csvs,
    )

    cargar_landing = PythonOperator(
        task_id="cargar_landing",
        python_callable=tasks.cargar_landing,
    )

    # ---- Landing → Staging (secuencial: respeta dependencias entre entidades)
    with TaskGroup(group_id="staging", tooltip="Landing → Staging (MERGE)") as staging:
        chain(
            *[
                _merge_task(script, tasks.ejecutar_merge_staging, "02_staging/dml")
                for script in STAGING_MERGE_SCRIPTS
            ]
        )

    # ---- Staging → Dimensiones (en paralelo: no dependen entre sí)
    with TaskGroup(group_id="dimensiones", tooltip="Staging → dimensiones") as dimensiones:
        for script in DIMENSION_MERGE_SCRIPTS:
            _merge_task(script, tasks.ejecutar_merge_service, "04_service/dml")

    # ---- Staging → Hechos (después de TODAS las dimensiones, por las FK)
    with TaskGroup(group_id="hechos", tooltip="Staging → hechos") as hechos:
        chain(
            *[
                _merge_task(script, tasks.ejecutar_merge_service, "04_service/dml")
                for script in FACT_MERGE_SCRIPTS
            ]
        )

    validar_conteos = PythonOperator(
        task_id="validar_conteos",
        python_callable=tasks.validar_conteos,
    )

    verificar_csvs >> cargar_landing >> staging >> dimensiones >> hechos >> validar_conteos
