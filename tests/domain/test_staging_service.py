"""
Tests unitarios para src/domain/services/staging_service.py

Cubre:
- run_merges(): todos los scripts exitosos
- run_merges(): script faltante (skip, no falla)
- run_merges(): un script falla → retorna False
- run_merges(): resumen de tablas se loguea (sin error)
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from src.domain.services.staging_service import StagingService, _MERGE_ORDER, _STAGING_TABLES
from src.shared.config.settings import Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(mock_repo, tmp_path) -> tuple[StagingService, Settings]:
    sql_dir = tmp_path / "sql"
    merge_dir = sql_dir / "02_staging" / "dml"
    merge_dir.mkdir(parents=True)

    s = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        sql_dir=sql_dir,
        logs_dir=tmp_path / "logs",
    )
    svc = StagingService(repo=mock_repo, app_settings=s)
    return svc, s


def _create_all_merge_scripts(merge_dir: Path) -> None:
    """Crea archivos .sql vacíos para cada script del orden."""
    for name in _MERGE_ORDER:
        (merge_dir / name).write_text("SELECT 1;", encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests de run_merges
# ---------------------------------------------------------------------------

class TestStagingServiceRunMerges:

    def test_run_merges_returns_true_when_all_succeed(self, mock_repo, tmp_path):
        svc, s = _make_service(mock_repo, tmp_path)
        merge_dir = s.sql_dir / "02_staging" / "dml"
        _create_all_merge_scripts(merge_dir)

        mock_repo.execute_file.return_value = True
        result = svc.run_merges()
        assert result is True

    def test_run_merges_calls_execute_file_for_each_script(self, mock_repo, tmp_path):
        svc, s = _make_service(mock_repo, tmp_path)
        merge_dir = s.sql_dir / "02_staging" / "dml"
        _create_all_merge_scripts(merge_dir)

        mock_repo.execute_file.return_value = True
        svc.run_merges()

        assert mock_repo.execute_file.call_count == len(_MERGE_ORDER)

    def test_run_merges_skips_missing_scripts(self, mock_repo, tmp_path):
        """Si un script no existe, se loguea warning y se continúa."""
        svc, s = _make_service(mock_repo, tmp_path)
        # No crear NINGÚN script → todos se saltarán
        mock_repo.execute_file.return_value = True
        result = svc.run_merges()
        # Si todos se saltaron, all_success sigue True
        assert result is True
        mock_repo.execute_file.assert_not_called()

    def test_run_merges_returns_false_when_one_fails(self, mock_repo, tmp_path):
        svc, s = _make_service(mock_repo, tmp_path)
        merge_dir = s.sql_dir / "02_staging" / "dml"
        _create_all_merge_scripts(merge_dir)

        # El tercer script falla
        def _side_effect(path, desc):
            if "merge_sucursales" in str(path):
                return False
            return True

        mock_repo.execute_file.side_effect = _side_effect
        result = svc.run_merges()
        assert result is False

    def test_run_merges_logs_summary_for_all_tables(self, mock_repo, tmp_path):
        """Verifica que se consulta el conteo de todas las tablas de staging."""
        svc, s = _make_service(mock_repo, tmp_path)
        mock_repo.execute_file.return_value = True

        svc.run_merges()

        for table in _STAGING_TABLES:
            mock_repo.get_table_count.assert_any_call("staging", table)

    def test_run_merges_executes_in_order(self, mock_repo, tmp_path):
        """Los scripts se ejecutan en el orden definido en _MERGE_ORDER."""
        svc, s = _make_service(mock_repo, tmp_path)
        merge_dir = s.sql_dir / "02_staging" / "dml"
        _create_all_merge_scripts(merge_dir)

        mock_repo.execute_file.return_value = True
        svc.run_merges()

        called_paths = [str(call.args[0]) for call in mock_repo.execute_file.call_args_list]
        for i, script_name in enumerate(_MERGE_ORDER):
            assert script_name in called_paths[i]
