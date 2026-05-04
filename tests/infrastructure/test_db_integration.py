import pytest

from src.infrastructure.database.connection import DatabaseConnection


@pytest.mark.integration
def test_database_connection_real():
    """Valida que la conexión a Postgres sea exitosa en el entorno de CI."""
    db = DatabaseConnection()
    assert db.ping() is True


@pytest.mark.integration
def test_database_write_operation():
    """Valida operaciones de DDL y DML básicas en la base de datos de CI."""
    db = DatabaseConnection()
    with db.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS ci_metadata (id SERIAL PRIMARY KEY, step TEXT);")
        cur.execute("INSERT INTO ci_metadata (step) VALUES ('CI_RUNNING') RETURNING id;")
        row_id = cur.fetchone()[0]
        assert row_id > 0
        cur.execute("SELECT step FROM ci_metadata WHERE id = %s;", (row_id,))
        assert cur.fetchone()[0] == "CI_RUNNING"
        cur.execute("DROP TABLE ci_metadata;")
