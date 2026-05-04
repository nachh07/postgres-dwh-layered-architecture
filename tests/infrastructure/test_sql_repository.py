"""
Tests unitarios para src/infrastructure/repositories/sql_repository.py

Cubre:
- execute_file() exitoso
- execute_file() con archivo inexistente
- execute_file() con error de SQL
- execute() exitoso y con error
- get_table_count() exitoso y con error
- truncate_table()
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.infrastructure.repositories.sql_repository import SQLRepository


# ---------------------------------------------------------------------------
# Tests de execute_file
# ---------------------------------------------------------------------------

class TestSQLRepositoryExecuteFile:

    def test_execute_file_returns_true_on_success(self, mock_db, sample_sql_file):
        repo = SQLRepository(db=mock_db)
        result = repo.execute_file(sample_sql_file, "Test query")
        assert result is True

    def test_execute_file_calls_cursor_execute(self, mock_db, sample_sql_file, mock_cursor):
        repo = SQLRepository(db=mock_db)
        repo.execute_file(sample_sql_file)
        mock_cursor.execute.assert_called_once_with("SELECT 1;")

    def test_execute_file_returns_false_when_file_not_found(self, mock_db, tmp_path):
        repo = SQLRepository(db=mock_db)
        missing = tmp_path / "nonexistent.sql"
        result = repo.execute_file(missing, "Missing file")
        assert result is False

    def test_execute_file_returns_false_on_sql_error(self, mock_db, sample_sql_file, mock_cursor):
        mock_cursor.execute.side_effect = Exception("SQL syntax error")
        repo = SQLRepository(db=mock_db)
        result = repo.execute_file(sample_sql_file)
        assert result is False

    def test_execute_file_uses_filename_as_default_description(self, mock_db, sample_sql_file):
        """Si no se pasa description, usa el nombre del archivo en los logs."""
        repo = SQLRepository(db=mock_db)
        # Sólo verificamos que no falla
        result = repo.execute_file(sample_sql_file)
        assert result is True


# ---------------------------------------------------------------------------
# Tests de execute
# ---------------------------------------------------------------------------

class TestSQLRepositoryExecute:

    def test_execute_returns_true_on_success(self, mock_db, mock_cursor):
        repo = SQLRepository(db=mock_db)
        result = repo.execute("SELECT 1;")
        assert result is True

    def test_execute_runs_the_sql(self, mock_db, mock_cursor):
        repo = SQLRepository(db=mock_db)
        repo.execute("SELECT 42;", "Test")
        mock_cursor.execute.assert_called_once_with("SELECT 42;")

    def test_execute_returns_false_on_error(self, mock_db, mock_cursor):
        mock_cursor.execute.side_effect = Exception("DB error")
        repo = SQLRepository(db=mock_db)
        result = repo.execute("INVALID SQL;")
        assert result is False


# ---------------------------------------------------------------------------
# Tests de get_table_count
# ---------------------------------------------------------------------------

class TestSQLRepositoryGetTableCount:

    def test_get_table_count_returns_count(self, mock_db, mock_cursor):
        mock_cursor.fetchone.return_value = (999,)
        repo = SQLRepository(db=mock_db)
        count = repo.get_table_count("staging", "stg_clientes")
        assert count == 999

    def test_get_table_count_returns_zero_when_no_result(self, mock_db, mock_cursor):
        mock_cursor.fetchone.return_value = None
        repo = SQLRepository(db=mock_db)
        count = repo.get_table_count("staging", "stg_clientes")
        assert count == 0

    def test_get_table_count_returns_minus_one_on_error(self, mock_db, mock_cursor):
        mock_cursor.execute.side_effect = Exception("Table not found")
        repo = SQLRepository(db=mock_db)
        count = repo.get_table_count("staging", "nonexistent_table")
        assert count == -1

    def test_get_table_count_queries_correct_table(self, mock_db, mock_cursor):
        repo = SQLRepository(db=mock_db)
        repo.get_table_count("landing_zone", "raw_ventas")
        sql_used = mock_cursor.execute.call_args[0][0]
        assert "landing_zone.raw_ventas" in sql_used


# ---------------------------------------------------------------------------
# Tests de truncate_table
# ---------------------------------------------------------------------------

class TestSQLRepositoryTruncateTable:

    def test_truncate_table_returns_true(self, mock_db, mock_cursor):
        repo = SQLRepository(db=mock_db)
        result = repo.truncate_table("landing_zone", "raw_clientes")
        assert result is True

    def test_truncate_table_uses_cascade(self, mock_db, mock_cursor):
        repo = SQLRepository(db=mock_db)
        repo.truncate_table("landing_zone", "raw_clientes")
        sql_used = mock_cursor.execute.call_args[0][0]
        assert "CASCADE" in sql_used

    def test_truncate_table_returns_false_on_error(self, mock_db, mock_cursor):
        mock_cursor.execute.side_effect = Exception("Permission denied")
        repo = SQLRepository(db=mock_db)
        result = repo.truncate_table("landing_zone", "raw_clientes")
        assert result is False
