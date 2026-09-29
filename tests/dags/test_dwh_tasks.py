"""
Tests unitarios para dags/dwh_common/tasks.py (callables de los PythonOperator).

El punto crítico: los servicios de src/ devuelven False en vez de lanzar
excepción, y Airflow solo marca un task en rojo si hay excepción.

Cubre:
- ensure(): False → PipelineStepError
- initialize_dwh(): llama al orquestador con only_init y falla si devuelve False
- check_csv_files(): lista los CSV faltantes
- load_landing(): falla si algún CSV no se cargó
- run_*_merge(): ruta correcta del script y falla si execute_file devuelve False
- validate_counts(): pasa con conteos correctos y falla con diferencias o errores
"""

from unittest.mock import MagicMock

import pytest

from dwh_common import tasks
from dwh_common.config import EXPECTED_FACT_COUNTS
from src.shared.config.settings import Settings


@pytest.fixture
def patched_settings(sample_settings, monkeypatch):
    monkeypatch.setattr(tasks, "settings", sample_settings)
    return sample_settings


@pytest.fixture
def patched_repo(mock_repo, monkeypatch):
    monkeypatch.setattr(tasks, "default_repo", mock_repo)
    return mock_repo


class TestEnsure:
    def test_true_does_not_raise(self):
        tasks.ensure(True, "no debería fallar")

    def test_false_raises(self):
        with pytest.raises(tasks.PipelineStepError, match="mensaje"):
            tasks.ensure(False, "mensaje")


class TestInitializeDwh:
    @pytest.mark.parametrize("result", [True, False])
    def test_uses_orchestrator(self, monkeypatch, result):
        orchestrator_cls = MagicMock()
        orchestrator_cls.return_value.run.return_value = result
        monkeypatch.setattr(tasks, "PipelineOrchestrator", orchestrator_cls)

        if result:
            tasks.initialize_dwh()
        else:
            with pytest.raises(tasks.PipelineStepError):
                tasks.initialize_dwh()

        orchestrator_cls.return_value.run.assert_called_once_with(
            create_schema=True, create_tables=True, only_init=True
        )


class TestCheckCsvFiles:
    def test_all_present(self, patched_settings: Settings):
        for name in patched_settings.csv_table_mapping:
            (patched_settings.data_dir / name).write_text("x", encoding="latin1")
        tasks.check_csv_files()

    def test_missing_files_are_listed(self, patched_settings: Settings):
        (patched_settings.data_dir / "Venta.csv").write_text("x", encoding="latin1")
        with pytest.raises(FileNotFoundError) as exc:
            tasks.check_csv_files()
        assert "Clientes.csv" in str(exc.value)
        assert "Faltan 9 CSV" in str(exc.value)


class TestLoadLanding:
    def _patch(self, monkeypatch, results):
        svc_cls = MagicMock()
        svc_cls.return_value.load_all.return_value = results
        monkeypatch.setattr(tasks, "IngestionService", svc_cls)
        return svc_cls

    def test_all_ok(self, monkeypatch):
        svc_cls = self._patch(monkeypatch, {"a.csv": True, "b.csv": True})
        tasks.load_landing()
        svc_cls.return_value.load_all.assert_called_once_with(truncate=True)

    def test_one_csv_fails(self, monkeypatch):
        self._patch(monkeypatch, {"a.csv": True, "b.csv": False})
        with pytest.raises(tasks.PipelineStepError, match="b.csv"):
            tasks.load_landing()

    def test_no_results_fails(self, monkeypatch):
        self._patch(monkeypatch, {})
        with pytest.raises(tasks.PipelineStepError):
            tasks.load_landing()


class TestRunMerge:
    def test_staging_path_and_ok(self, patched_settings, patched_repo):
        tasks.run_staging_merge("merge_ventas.sql")
        path, desc = patched_repo.execute_file.call_args.args
        assert path == patched_settings.sql_dir / "02_staging" / "dml" / "merge_ventas.sql"
        assert desc == "MERGE ventas"

    def test_service_path(self, patched_settings, patched_repo):
        tasks.run_service_merge("merge_dim_cliente.sql")
        path, _ = patched_repo.execute_file.call_args.args
        assert path == patched_settings.sql_dir / "04_service" / "dml" / "merge_dim_cliente.sql"

    @pytest.mark.parametrize("func", [tasks.run_staging_merge, tasks.run_service_merge])
    def test_false_raises(self, patched_settings, patched_repo, func):
        patched_repo.execute_file.return_value = False
        with pytest.raises(tasks.PipelineStepError, match="merge_x.sql"):
            func("merge_x.sql")


class TestValidateCounts:
    def _setup(self, monkeypatch, mock_repo, mock_db, mock_cursor, active_stg, counts):
        mock_cursor.fetchone.return_value = (active_stg,)
        mock_repo.get_table_count.side_effect = lambda schema, table: counts[table]
        monkeypatch.setattr(tasks, "default_repo", mock_repo)
        monkeypatch.setattr(tasks, "default_db", mock_db)

    def test_counts_match(self, monkeypatch, mock_repo, mock_db, mock_cursor):
        counts = {"raw_ventas": 100, **EXPECTED_FACT_COUNTS}
        self._setup(monkeypatch, mock_repo, mock_db, mock_cursor, 100, counts)
        tasks.validate_counts()

    def test_stg_differs_from_raw(self, monkeypatch, mock_repo, mock_db, mock_cursor):
        counts = {"raw_ventas": 100, **EXPECTED_FACT_COUNTS}
        self._setup(monkeypatch, mock_repo, mock_db, mock_cursor, 99, counts)
        with pytest.raises(tasks.PipelineStepError, match="stg_ventas"):
            tasks.validate_counts()

    def test_fact_differs_from_expected(self, monkeypatch, mock_repo, mock_db, mock_cursor):
        counts = {"raw_ventas": 100, **EXPECTED_FACT_COUNTS, "fact_gastos": 1}
        self._setup(monkeypatch, mock_repo, mock_db, mock_cursor, 100, counts)
        with pytest.raises(tasks.PipelineStepError, match="fact_gastos"):
            tasks.validate_counts()

    def test_count_error_fails(self, monkeypatch, mock_repo, mock_db, mock_cursor):
        # get_table_count devuelve -1 ante error; si raw y stg dan -1 no debe pasar
        counts = {"raw_ventas": -1, **EXPECTED_FACT_COUNTS}
        self._setup(monkeypatch, mock_repo, mock_db, mock_cursor, 0, counts)
        mock_db.cursor.side_effect = RuntimeError("sin conexión")
        with pytest.raises(tasks.PipelineStepError, match="real=-1"):
            tasks.validate_counts()
