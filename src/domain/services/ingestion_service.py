"""
Capa de dominio — Servicio de Ingesta (CSV → Landing Zone).

La clase `IngestionService` encapsula toda la lógica de negocio
relacionada con la carga de archivos CSV a la capa landing_zone.
Delega las operaciones de I/O de base de datos a `SQLRepository`
y `DatabaseConnection`.
"""

import csv
from pathlib import Path

from src.infrastructure.database.connection import DatabaseConnection, default_db
from src.infrastructure.repositories.sql_repository import SQLRepository, default_repo
from src.shared.config.settings import Settings, settings
from src.shared.logger import get_logger

logger = get_logger(__name__, "csv_ingestion.log")


class IngestionService:
    """
    Servicio de ingesta masiva de CSVs hacia la capa Landing Zone.

    Responsabilidades:
        - Detectar el delimitador de cada CSV.
        - Cargar cada CSV a su tabla `raw_*` correspondiente usando COPY.
        - Reportar el resultado por archivo.

    Uso:
        svc = IngestionService()
        results = svc.load_all(truncate=True)
    """

    def __init__(
        self,
        db: DatabaseConnection = default_db,
        repo: SQLRepository = default_repo,
        app_settings: Settings = settings,
    ) -> None:
        """
        Args:
            db:           Conexión a la base de datos.
            repo:         Repositorio SQL para utilidades de tabla.
            app_settings: Configuración del proyecto.
        """
        self._db = db
        self._repo = repo
        self._settings = app_settings

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def load_all(self, truncate: bool = True) -> dict[str, bool]:
        """
        Carga todos los CSVs configurados a landing_zone.

        Args:
            truncate: Si True, trunca cada tabla antes de insertar.

        Returns:
            Diccionario {csv_filename: success} con el resultado por archivo.
        """
        logger.info("🚀 Iniciando carga masiva de CSVs a Landing Zone")
        logger.info("   Directorio de datos: %s", self._settings.data_dir)

        results: dict[str, bool] = {}

        for csv_filename, table_name in self._settings.csv_table_mapping.items():
            csv_path = self._settings.data_dir / csv_filename

            if not csv_path.exists():
                logger.warning("⚠️  Archivo no encontrado: %s", csv_filename)
                results[csv_filename] = False
                continue

            success = self.load_csv(csv_path, table_name, truncate)
            results[csv_filename] = success

        # --- Resumen -------------------------------------------------------
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info("=" * 60)
        logger.info("📊 Resumen: %d/%d archivos cargados exitosamente", successful, total)
        logger.info("=" * 60)

        return results

    def load_csv(self, csv_path: Path, table_name: str, truncate: bool = True) -> bool:
        """
        Carga un único CSV a su tabla landing_zone correspondiente.

        Args:
            csv_path:   Path absoluto al archivo CSV.
            table_name: Nombre de la tabla destino en landing_zone.
            truncate:   Si True, trunca la tabla antes de insertar.

        Returns:
            True si la carga fue exitosa.
        """
        logger.info("📥 Cargando %s → landing_zone.%s", csv_path.name, table_name)

        try:
            if truncate:
                self._repo.truncate_table("landing_zone", table_name)

            delimiter = self._detect_delimiter(csv_path)
            logger.info("   Delimitador detectado: '%s'", delimiter)

            columns = self._settings.table_columns.get(table_name, [])
            if not columns:
                raise ValueError(f"No se encontraron columnas configuradas para '{table_name}'")

            columns_str = ", ".join(columns)

            with self._db.connection() as conn:
                with conn.cursor() as cur:
                    with csv_path.open("r", encoding="latin1") as f:
                        next(f)  # saltar header
                        cur.copy_expert(
                            f"""
                            COPY landing_zone.{table_name} ({columns_str})
                            FROM STDIN
                            WITH (
                                FORMAT CSV,
                                DELIMITER '{delimiter}',
                                QUOTE '"',
                                ESCAPE '"',
                                NULL '',
                                ENCODING 'LATIN1'
                            )
                            """,
                            f,
                        )

            count = self._repo.get_table_count("landing_zone", table_name)
            logger.info("✅ %s cargado: %s registros", csv_path.name, f"{count:,}")
            return True

        except Exception as exc:
            logger.error("❌ Error cargando %s: %s", csv_path.name, exc)
            return False

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _detect_delimiter(self, csv_path: Path) -> str:
        """
        Detecta el delimitador de un CSV.

        Primero revisa `special_delimiters` en la configuración;
        si no está, usa csv.Sniffer sobre la primera línea.

        Args:
            csv_path: Path al archivo CSV.

        Returns:
            Carácter delimitador detectado.
        """
        filename = csv_path.name

        if filename in self._settings.special_delimiters:
            return self._settings.special_delimiters[filename]

        with csv_path.open("r", encoding="latin1") as f:
            first_line = f.readline()

        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(first_line)
        return dialect.delimiter
