"""
Tests unitarios para src/infrastructure/database/connection.py

Cubre:
- DatabaseConnection.ping() exitoso
- DatabaseConnection.ping() con error de conexión
- connection() context manager (commit y rollback)
- cursor() context manager
"""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.database.connection import DatabaseConnection
from src.shared.config.database_settings import DatabaseSettings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db_settings(**kwargs) -> DatabaseSettings:
    """Crea un DatabaseSettings con valores de prueba."""
    defaults = dict(
        host="localhost", port=5432, database="test_db", user="test_user", password="test_pass"
    )
    defaults.update(kwargs)
    return DatabaseSettings(**defaults)


# ---------------------------------------------------------------------------
# Tests de ping
# ---------------------------------------------------------------------------


class TestDatabaseConnectionPing:
    def test_ping_returns_true_on_success(self):
        """ping() retorna True cuando la conexión es exitosa."""
        db = DatabaseConnection(db_settings=_make_db_settings())

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (1,)
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        with patch("psycopg2.connect", return_value=mock_conn):
            result = db.ping()

        assert result is True

    def test_ping_returns_false_on_connection_error(self):
        """ping() retorna False cuando psycopg2 lanza una excepción."""
        import psycopg2

        db = DatabaseConnection(db_settings=_make_db_settings())

        with patch("psycopg2.connect", side_effect=psycopg2.OperationalError("Connection refused")):
            result = db.ping()

        assert result is False


# ---------------------------------------------------------------------------
# Tests de connection() context manager
# ---------------------------------------------------------------------------


class TestDatabaseConnectionContextManager:
    def test_connection_commits_on_success(self):
        """connection() hace commit si no hay excepciones."""
        db = DatabaseConnection(db_settings=_make_db_settings())

        mock_conn = MagicMock()
        mock_conn.commit = MagicMock()
        mock_conn.rollback = MagicMock()

        with patch("psycopg2.connect", return_value=mock_conn):
            with db.connection() as conn:
                assert conn is mock_conn

        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

    def test_connection_rollbacks_on_exception(self):
        """connection() hace rollback si se lanza una excepción dentro del bloque."""
        db = DatabaseConnection(db_settings=_make_db_settings())

        mock_conn = MagicMock()
        mock_conn.commit = MagicMock()
        mock_conn.rollback = MagicMock()

        with patch("psycopg2.connect", return_value=mock_conn):
            with pytest.raises(ValueError):
                with db.connection():
                    raise ValueError("algo salió mal")

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_connection_closes_on_exit(self):
        """connection() cierra la conexión al salir del bloque."""
        db = DatabaseConnection(db_settings=_make_db_settings())

        mock_conn = MagicMock()

        with patch("psycopg2.connect", return_value=mock_conn):
            with db.connection():
                pass

        mock_conn.close.assert_called_once()

    def test_connection_raises_on_connect_failure(self):
        """connection() propaga excepciones de psycopg2.connect."""
        import psycopg2

        db = DatabaseConnection(db_settings=_make_db_settings())

        with patch("psycopg2.connect", side_effect=psycopg2.OperationalError("failed")):
            with pytest.raises(psycopg2.OperationalError):
                with db.connection():
                    pass


# ---------------------------------------------------------------------------
# Tests de cursor() context manager
# ---------------------------------------------------------------------------


class TestDatabaseConnectionCursor:
    def test_cursor_yields_cursor_object(self):
        """cursor() proporciona un objeto cursor."""
        db = DatabaseConnection(db_settings=_make_db_settings())

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        with patch("psycopg2.connect", return_value=mock_conn):
            with db.cursor() as cur:
                assert cur is mock_cur

    def test_cursor_closes_on_exit(self):
        """cursor() cierra el cursor al salir del bloque."""
        db = DatabaseConnection(db_settings=_make_db_settings())

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        with patch("psycopg2.connect", return_value=mock_conn):
            with db.cursor():
                pass

        mock_cur.close.assert_called_once()

    def test_cursor_uses_real_dict_cursor_when_requested(self):
        """cursor(dict_cursor=True) pasa RealDictCursor como factory."""
        from psycopg2.extras import RealDictCursor

        db = DatabaseConnection(db_settings=_make_db_settings())
        mock_conn = MagicMock()

        with patch("psycopg2.connect", return_value=mock_conn):
            with db.cursor(dict_cursor=True):
                pass

        mock_conn.cursor.assert_called_once_with(cursor_factory=RealDictCursor)


# ---------------------------------------------------------------------------
# Tests de DatabaseSettings repr
# ---------------------------------------------------------------------------


class TestDatabaseSettings:
    def test_repr_hides_password(self):
        ds = _make_db_settings(password="supersecret")
        assert "supersecret" not in repr(ds)
        assert "***" in repr(ds)

    def test_as_dict_returns_all_keys(self):
        ds = _make_db_settings()
        d = ds.as_dict()
        assert set(d.keys()) == {"host", "port", "database", "user", "password"}
