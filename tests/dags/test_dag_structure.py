"""
Tests de estructura de los DAGs (dags/dwh_init.py y dags/dwh_pipeline.py).

No requieren Airflow: usan los dobles de tests/dags/conftest.py.

Cubre:
- Parámetros de cada DAG (schedule, catchup, max_active_runs, retries)
- dwh_init advierte que es destructivo
- dwh_pipeline: un task por script, en el orden de las constantes de src/
- Dependencias: CSVs → landing → staging (secuencial) → dimensiones (paralelo)
  → hechos (después de TODAS las dimensiones) → validación
- Cada script referenciado existe en sql/
"""

from dwh_common import tasks
from src.domain.services.service_layer_service import (
    DIMENSION_MERGE_SCRIPTS,
    FACT_MERGE_SCRIPTS,
)
from src.domain.services.staging_service import STAGING_MERGE_SCRIPTS
from src.shared.config.settings import settings


def _ids(group: str, scripts: list[str]) -> list[str]:
    return [f"{group}.{s.removeprefix('merge_').removesuffix('.sql')}" for s in scripts]


STAGING_IDS = _ids("staging", STAGING_MERGE_SCRIPTS)
DIM_IDS = _ids("dimensiones", DIMENSION_MERGE_SCRIPTS)
FACT_IDS = _ids("hechos", FACT_MERGE_SCRIPTS)


# ---------------------------------------------------------------------------
# dwh_init
# ---------------------------------------------------------------------------


class TestDwhInit:
    def test_es_manual_y_sin_catchup(self, load_dag):
        dag = load_dag("dwh_init.py")
        assert dag.dag_id == "dwh_init"
        assert dag.kwargs["schedule"] is None
        assert dag.kwargs["catchup"] is False
        assert dag.kwargs["max_active_runs"] == 1

    def test_advierte_que_es_destructivo(self, load_dag):
        dag = load_dag("dwh_init.py")
        assert "BORRA TODO" in dag.kwargs["doc_md"]
        assert "destructivo" in dag.kwargs["tags"]

    def test_un_task_que_llama_al_orquestador(self, load_dag):
        dag = load_dag("dwh_init.py")
        assert list(dag.tasks) == ["crear_schemas_y_tablas"]
        assert dag.tasks["crear_schemas_y_tablas"].python_callable is tasks.inicializar_dwh


# ---------------------------------------------------------------------------
# dwh_pipeline
# ---------------------------------------------------------------------------


class TestDwhPipelineParams:
    def test_parametros_del_dag(self, load_dag):
        dag = load_dag("dwh_pipeline.py")
        assert dag.dag_id == "dwh_pipeline"
        assert dag.kwargs["schedule"] == "@daily"
        assert dag.kwargs["catchup"] is False
        assert dag.kwargs["max_active_runs"] == 1
        assert dag.kwargs["default_args"]["retries"] == 1

    def test_task_ids(self, load_dag):
        dag = load_dag("dwh_pipeline.py")
        expected = {"verificar_csvs", "cargar_landing", "validar_conteos"}
        expected |= set(STAGING_IDS) | set(DIM_IDS) | set(FACT_IDS)
        assert set(dag.tasks) == expected

    def test_scripts_referenciados_existen(self, load_dag):
        dag = load_dag("dwh_pipeline.py")
        dirs = {
            tasks.ejecutar_merge_staging: settings.sql_dir / "02_staging" / "dml",
            tasks.ejecutar_merge_service: settings.sql_dir / "04_service" / "dml",
        }
        merge_tasks = [t for t in dag.tasks.values() if "script_name" in t.op_kwargs]
        assert len(merge_tasks) == len(STAGING_IDS) + len(DIM_IDS) + len(FACT_IDS)
        for task in merge_tasks:
            assert (dirs[task.python_callable] / task.op_kwargs["script_name"]).is_file()


class TestDwhPipelineDependencias:
    def test_inicio_del_pipeline(self, load_dag):
        t = load_dag("dwh_pipeline.py").tasks
        assert t["verificar_csvs"].upstream == set()
        assert t["cargar_landing"].upstream == {"verificar_csvs"}
        assert t[STAGING_IDS[0]].upstream == {"cargar_landing"}

    def test_staging_es_secuencial_en_orden(self, load_dag):
        t = load_dag("dwh_pipeline.py").tasks
        for up, down in zip(STAGING_IDS, STAGING_IDS[1:], strict=False):
            assert t[down].upstream == {up}

    def test_dimensiones_en_paralelo_despues_de_staging(self, load_dag):
        t = load_dag("dwh_pipeline.py").tasks
        for dim in DIM_IDS:
            assert t[dim].upstream == {STAGING_IDS[-1]}

    def test_hechos_despues_de_todas_las_dimensiones(self, load_dag):
        t = load_dag("dwh_pipeline.py").tasks
        assert t[FACT_IDS[0]].upstream == set(DIM_IDS)
        for up, down in zip(FACT_IDS, FACT_IDS[1:], strict=False):
            assert t[down].upstream == {up}

    def test_validacion_al_final(self, load_dag):
        t = load_dag("dwh_pipeline.py").tasks
        assert t["validar_conteos"].upstream == {FACT_IDS[-1]}
        assert t["validar_conteos"].downstream == set()
