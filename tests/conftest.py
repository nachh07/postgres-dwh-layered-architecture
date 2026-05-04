"""
conftest.py — Fixtures compartidas para toda la suite de tests.

Provee mocks y stubs de las dependencias externas (DB, filesystem)
para que los tests unitarios no requieran una base de datos real.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Fixtures de base de datos
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_cursor():
    """Cursor de psycopg2 completamente mockeado."""
    cursor = MagicMock()
    cursor.fetchone.return_value = (42,)
    cursor.fetchall.return_value = []
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    """
    Conexión de psycopg2 completamente mockeada.
    El context manager de cursor retorna mock_cursor.
    """
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture
def mock_db(mock_cursor):
    """
    DatabaseConnection mockeada cuyos context managers
    retornan los mocks de cursor y connection.
    """
    from src.infrastructure.database.connection import DatabaseConnection

    db = MagicMock(spec=DatabaseConnection)

    # connection() context manager
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    db.connection.return_value = mock_conn

    # cursor() context manager
    mock_cur_ctx = MagicMock()
    mock_cur_ctx.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cur_ctx.__exit__ = MagicMock(return_value=False)
    db.cursor.return_value = mock_cur_ctx

    return db


@pytest.fixture
def mock_repo():
    """SQLRepository completamente mockeado (todos los métodos retornan True/count)."""
    from src.infrastructure.repositories.sql_repository import SQLRepository

    repo = MagicMock(spec=SQLRepository)
    repo.execute_file.return_value = True
    repo.execute.return_value = True
    repo.get_table_count.return_value = 100
    repo.truncate_table.return_value = True
    return repo


# ---------------------------------------------------------------------------
# Fixtures de settings
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_settings(tmp_path):
    """
    Settings con directorios temporales para no tocar el filesystem real.
    """
    from src.shared.config.settings import Settings

    data_dir = tmp_path / "data"
    sql_dir = tmp_path / "sql"
    logs_dir = tmp_path / "logs"
    data_dir.mkdir()
    sql_dir.mkdir()
    logs_dir.mkdir()

    return Settings(
        project_root=tmp_path,
        data_dir=data_dir,
        sql_dir=sql_dir,
        logs_dir=logs_dir,
    )


# ---------------------------------------------------------------------------
# Fixtures de archivos CSV de prueba
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_csv_comma(tmp_path) -> Path:
    """CSV de prueba con delimitador coma."""
    csv_file = tmp_path / "test_comma.csv"
    csv_file.write_text(
        "id,nombre,valor\n1,Alice,100\n2,Bob,200\n",
        encoding="latin1",
    )
    return csv_file


@pytest.fixture
def sample_csv_semicolon(tmp_path) -> Path:
    """CSV de prueba con delimitador punto y coma."""
    csv_file = tmp_path / "Clientes.csv"
    csv_file.write_text(
        "id;nombre;valor\n1;Alice;100\n2;Bob;200\n",
        encoding="latin1",
    )
    return csv_file


@pytest.fixture
def sample_sql_file(tmp_path) -> Path:
    """Archivo .sql de prueba con una sentencia válida."""
    sql_file = tmp_path / "test_query.sql"
    sql_file.write_text("SELECT 1;", encoding="utf-8")
    return sql_file
