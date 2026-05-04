"""
Tests unitarios para src/domain/pipeline/pipeline_orchestrator.py

Cubre:
- run() completo exitoso (sin flags)
- run() con create_schema=True
- run() con create_tables=True
- run() falla en carga de CSVs → False
- run() falla en staging → False
- run() falla en service → False
- run() con excepción inesperada → False
- _create_schemas() delega al repositorio
- _create_all_tables() ejecuta los 5 pasos DDL
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from src.domain.pipeline.pipeline_orchestrator import PipelineOrchestrator
from src.shared.config.settings import Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(tmp_path, mock_repo, ingestion=None, staging=None, service_layer=None):
    """Crea un orquestador con todas las dependencias mockeadas."""
    sql_dir = tmp_path / "sql"

    # Crear estructura de dirs SQL vacíos
    (sql_dir / "00_schemas").mkdir(parents=True)
    (sql_dir / "01_landing" / "ddl").mkdir(parents=True)
    (sql_dir / "02_staging" / "ddl").mkdir(parents=True)
    (sql_dir / "04_service" / "ddl").mkdir(parents=True)
    (sql_dir / "04_service" / "dml").mkdir(parents=True)

    # Crear archivos SQL ficticios
    for p in [
        sql_dir / "00_schemas" / "create_schemas.sql",
        sql_dir / "01_landing" / "ddl" / "create_tables.sql",
        sql_dir / "02_staging" / "ddl" / "create_tables.sql",
        sql_dir / "04_service" / "ddl" / "create_dimensions.sql",
        sql_dir / "04_service" / "dml" / "populate_dim_tiempo.sql",
        sql_dir / "04_service" / "ddl" / "create_facts.sql",
    ]:
        p.write_text("SELECT 1;", encoding="utf-8")

    s = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        sql_dir=sql_dir,
        logs_dir=tmp_path / "logs",
    )

    mock_ingestion = ingestion or MagicMock()
    mock_ingestion.load_all.return_value = {"a.csv": True}

    mock_staging = staging or MagicMock()
    mock_staging.run_merges.return_value = True

    mock_service = service_layer or MagicMock()
    mock_service.run_merges.return_value = True

    return PipelineOrchestrator(
        repo=mock_repo,
        ingestion=mock_ingestion,
        staging=mock_staging,
        service_layer=mock_service,
        app_settings=s,
    ), mock_ingestion, mock_staging, mock_service


# ---------------------------------------------------------------------------
# Tests de run() — flujo completo
# ---------------------------------------------------------------------------

class TestPipelineOrchestratorRun:

    def test_run_returns_true_on_full_success(self, mock_repo, tmp_path):
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo)
        result = orch.run()
        assert result is True

    def test_run_calls_load_all_once(self, mock_repo, tmp_path):
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo)
        orch.run()
        ing.load_all.assert_called_once_with(truncate=True)

    def test_run_calls_staging_run_merges(self, mock_repo, tmp_path):
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo)
        orch.run()
        stg.run_merges.assert_called_once()

    def test_run_calls_service_run_merges(self, mock_repo, tmp_path):
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo)
        orch.run()
        svc.run_merges.assert_called_once()

    def test_run_returns_false_when_csv_load_fails(self, mock_repo, tmp_path):
        mock_ingestion = MagicMock()
        mock_ingestion.load_all.return_value = {"a.csv": False}
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo, ingestion=mock_ingestion)
        result = orch.run()
        assert result is False

    def test_run_returns_false_when_staging_fails(self, mock_repo, tmp_path):
        mock_staging = MagicMock()
        mock_staging.run_merges.return_value = False
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo, staging=mock_staging)
        result = orch.run()
        assert result is False

    def test_run_returns_false_when_service_fails(self, mock_repo, tmp_path):
        mock_service = MagicMock()
        mock_service.run_merges.return_value = False
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo, service_layer=mock_service)
        result = orch.run()
        assert result is False

    def test_run_returns_false_on_unexpected_exception(self, mock_repo, tmp_path):
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo)
        ing.load_all.side_effect = RuntimeError("Unexpected crash")
        result = orch.run()
        assert result is False

    def test_run_skips_staging_if_csv_fails(self, mock_repo, tmp_path):
        """Si CSV falla, el staging no debe ejecutarse (fail-fast)."""
        mock_ingestion = MagicMock()
        mock_ingestion.load_all.return_value = {"a.csv": False}
        orch, ing, stg, svc = _make_orchestrator(tmp_path, mock_repo, ingestion=mock_ingestion)
        orch.run()
        stg.run_merges.assert_not_called()


# ---------------------------------------------------------------------------
# Tests de run() con flags opcionales
# ---------------------------------------------------------------------------

class TestPipelineOrchestratorWithFlags:

    def test_run_with_create_schema_calls_execute_file(self, mock_repo, tmp_path):
        orch, _, _, _ = _make_orchestrator(tmp_path, mock_repo)
        mock_repo.execute_file.return_value = True
        orch.run(create_schema=True)
        # Debe haberse llamado al menos una vez (schemas)
        assert mock_repo.execute_file.called

    def test_run_with_create_schema_returns_false_on_fail(self, mock_repo, tmp_path):
        orch, _, _, _ = _make_orchestrator(tmp_path, mock_repo)
        mock_repo.execute_file.return_value = False
        result = orch.run(create_schema=True)
        assert result is False

    def test_run_with_create_tables_calls_five_ddl_steps(self, mock_repo, tmp_path):
        orch, _, _, _ = _make_orchestrator(tmp_path, mock_repo)
        mock_repo.execute_file.return_value = True
        orch.run(create_tables=True)
        assert mock_repo.execute_file.call_count == 5

    def test_run_with_create_tables_returns_false_on_ddl_fail(self, mock_repo, tmp_path):
        orch, _, _, _ = _make_orchestrator(tmp_path, mock_repo)
        # El primer DDL falla
        mock_repo.execute_file.return_value = False
        result = orch.run(create_tables=True)
        assert result is False
