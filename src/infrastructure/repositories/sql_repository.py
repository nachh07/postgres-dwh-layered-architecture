"""
Capa de infraestructura — Repositorio SQL.

La clase `SQLRepository` abstrae la ejecución de archivos .sql y
sentencias SQL sueltas, delegando la conexión a `DatabaseConnection`.
"""
from pathlib import Path

from src.infrastructure.database.connection import DatabaseConnection, default_db
from src.shared.logger import get_logger

logger = get_logger(__name__)


class SQLRepository:
    """
    Repositorio para operaciones SQL de bajo nivel.

    Responsabilidades:
        - Ejecutar archivos .sql
        - Ejecutar sentencias SQL en texto
        - Contar registros de una tabla
        - Truncar tablas
    """

    def __init__(self, db: DatabaseConnection = default_db) -> None:
        """
        Args:
            db: Instancia de DatabaseConnection a usar. Por defecto
                usa la instancia global.
        """
        self._db = db

    # ------------------------------------------------------------------
    # Ejecución de SQL
    # ------------------------------------------------------------------

    def execute_file(self, sql_file_path: Path, description: str | None = None) -> bool:
        """
        Lee y ejecuta un archivo .sql completo en una sola transacción.

        Args:
            sql_file_path: Path absoluto al archivo .sql.
            description:   Texto descriptivo para los logs.

        Returns:
            True si se ejecutó sin errores, False en caso contrario.
        """
        desc = description or f"Ejecutando {sql_file_path.name}"
        logger.info("🔄 %s", desc)

        if not sql_file_path.exists():
            logger.error("❌ %s — Archivo no encontrado: %s", desc, sql_file_path)
            return False

        try:
            sql = sql_file_path.read_text(encoding="utf-8")
            with self._db.cursor() as cur:
                cur.execute(sql)
            logger.info("✅ %s — Completado", desc)
            return True
        except Exception as exc:
            logger.error("❌ %s — Error: %s", desc, exc)
            return False

    def execute(self, sql: str, description: str | None = None) -> bool:
        """
        Ejecuta una sentencia SQL en texto.

        Args:
            sql:         Sentencia SQL a ejecutar.
            description: Texto descriptivo para los logs.

        Returns:
            True si se ejecutó sin errores, False en caso contrario.
        """
        desc = description or "Ejecutando SQL"
        logger.info("🔄 %s", desc)

        try:
            with self._db.cursor() as cur:
                cur.execute(sql)
            logger.info("✅ %s — Completado", desc)
            return True
        except Exception as exc:
            logger.error("❌ %s — Error: %s", desc, exc)
            return False

    # ------------------------------------------------------------------
    # Utilidades de tabla
    # ------------------------------------------------------------------

    def get_table_count(self, schema: str, table: str) -> int:
        """
        Retorna el número de registros de una tabla.

        Args:
            schema: Nombre del schema (ej. 'landing_zone').
            table:  Nombre de la tabla (ej. 'raw_clientes').

        Returns:
            Número de registros, o -1 si ocurre un error.
        """
        sql = f"SELECT COUNT(*) FROM {schema}.{table};"
        try:
            with self._db.cursor() as cur:
                cur.execute(sql)
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception as exc:
            logger.error("Error al obtener conteo de %s.%s: %s", schema, table, exc)
            return -1

    def truncate_table(self, schema: str, table: str) -> bool:
        """
        Trunca una tabla con CASCADE.

        Args:
            schema: Nombre del schema.
            table:  Nombre de la tabla.

        Returns:
            True si se truncó correctamente.
        """
        sql = f"TRUNCATE TABLE {schema}.{table} CASCADE;"
        return self.execute(sql, f"Truncando {schema}.{table}")


# Instancia global reutilizable
default_repo = SQLRepository()
