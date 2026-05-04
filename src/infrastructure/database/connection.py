"""
Capa de infraestructura — Conexión a PostgreSQL.

La clase `DatabaseConnection` encapsula toda la lógica de apertura,
commit, rollback y cierre de conexiones a PostgreSQL, exponiendo
context managers seguros para conexión y cursor.
"""

from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
import psycopg2.extensions
from psycopg2.extras import RealDictCursor

from src.shared.config.database_settings import DatabaseSettings, db_settings
from src.shared.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """
    Gestiona conexiones a PostgreSQL de forma segura.

    Uso típico:
        db = DatabaseConnection()
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

        # O directamente con cursor:
        with db.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
    """

    def __init__(self, db_settings: DatabaseSettings = db_settings) -> None:
        """
        Args:
            db_settings: Configuración de conexión. Por defecto usa la
                         instancia global cargada desde el .env.
        """
        self._settings = db_settings

    # ------------------------------------------------------------------
    # Context managers
    # ------------------------------------------------------------------

    @contextmanager
    def connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Context manager que provee una conexión con auto-commit/rollback.

        Yields:
            psycopg2.connection activa.

        Raises:
            psycopg2.OperationalError: Si no se puede establecer la conexión.
        """
        conn: psycopg2.extensions.connection | None = None
        try:
            conn = psycopg2.connect(**self._settings.as_dict())
            yield conn
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def cursor(
        self, dict_cursor: bool = False
    ) -> Generator[psycopg2.extensions.cursor, None, None]:
        """
        Context manager que provee un cursor listo para usar.

        Args:
            dict_cursor: Si True, los resultados se retornan como dicts.

        Yields:
            psycopg2.cursor (o RealDictCursor si `dict_cursor=True`).
        """
        with self.connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cur = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cur
            finally:
                cur.close()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """
        Verifica que la base de datos sea alcanzable.

        Returns:
            True si la conexión es exitosa, False en caso contrario.
        """
        try:
            with self.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            logger.info("✅ Conexión a PostgreSQL exitosa: %s", self._settings)
            return True
        except Exception as exc:
            logger.error("❌ No se pudo conectar a PostgreSQL: %s", exc)
            return False


# Instancia global reutilizable
default_db = DatabaseConnection()
