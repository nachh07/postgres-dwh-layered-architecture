"""
Capa de dominio — Orquestador del Pipeline.

La clase `PipelineOrchestrator` coordina la ejecución end-to-end del ETL:
    CSV → Landing Zone → Staging → Service (Data Warehouse)

Delega cada etapa a su servicio correspondiente e implementa
la política de fallo rápido (fail-fast) ante errores críticos.

Ejecución CLI:
    python -m src.domain.pipeline.pipeline_orchestrator [--create-schema] [--create-tables]
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.domain.services.ingestion_service import IngestionService
from src.domain.services.service_layer_service import ServiceLayerService
from src.domain.services.staging_service import StagingService
from src.infrastructure.repositories.sql_repository import SQLRepository, default_repo
from src.shared.config.settings import Settings, settings
from src.shared.logger import get_logger

logger = get_logger(__name__, "pipeline_run.log")


class PipelineOrchestrator:
    """
    Orquestador principal del pipeline de Data Engineering.

    Coordina la ejecución de todas las etapas del ETL, manteniendo
    el estado de cada paso y generando logs detallados de progreso.

    Uso básico:
        orchestrator = PipelineOrchestrator()
        success = orchestrator.run(create_schema=True, create_tables=True)
    """

    def __init__(
        self,
        repo: SQLRepository = default_repo,
        ingestion: IngestionService | None = None,
        staging: StagingService | None = None,
        service_layer: ServiceLayerService | None = None,
        app_settings: Settings = settings,
    ) -> None:
        """
        Args:
            repo:          Repositorio SQL (para DDL y schemas).
            ingestion:     Servicio de ingesta. Si None, se crea con defaults.
            staging:       Servicio de staging. Si None, se crea con defaults.
            service_layer: Servicio de DWH. Si None, se crea con defaults.
            app_settings:  Configuración del proyecto.
        """
        self._repo = repo
        self._ingestion = ingestion or IngestionService(app_settings=app_settings)
        self._staging = staging or StagingService(repo=repo, app_settings=app_settings)
        self._service_layer = service_layer or ServiceLayerService(
            repo=repo, app_settings=app_settings
        )
        self._settings = app_settings

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run(self, create_schema: bool = False, create_tables: bool = False) -> bool:
        """
        Ejecuta el pipeline completo end-to-end.

        Args:
            create_schema: Si True, crea los schemas antes de ejecutar.
            create_tables: Si True, crea/recrea las tablas antes de ejecutar.

        Returns:
            True si todos los pasos se completaron sin errores.
        """
        start_time = datetime.now()
        self._log_header("INICIANDO PIPELINE DE DATA ENGINEERING")

        try:
            # Paso 0: Schemas (opcional)
            if create_schema:
                if not self._create_schemas():
                    return self._fail("Error creando schemas", start_time)

            # Paso 1: DDL (opcional)
            if create_tables:
                if not self._create_all_tables():
                    return self._fail("Error creando tablas", start_time)

            # Paso 2: CSV → Landing
            if not self._load_csvs():
                return self._fail("Error cargando CSVs a landing", start_time)

            # Paso 3: Landing → Staging
            if not self._run_staging():
                return self._fail("Error en MERGE landing → staging", start_time)

            # Paso 4: Staging → Service
            if not self._run_service():
                return self._fail("Error en MERGE staging → service", start_time)

            # Éxito
            elapsed = datetime.now() - start_time
            self._log_header(
                f"✅ PIPELINE COMPLETADO EXITOSAMENTE  |  Tiempo: {elapsed}"
            )
            return True

        except Exception as exc:
            logger.error("❌ Error inesperado en el pipeline: %s", exc, exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Pasos privados
    # ------------------------------------------------------------------

    def _create_schemas(self) -> bool:
        logger.info("PASO 0: Creando schemas")
        script = self._settings.sql_dir / "00_schemas" / "create_schemas.sql"
        return self._repo.execute_file(script, "Creando schemas")

    def _create_all_tables(self) -> bool:
        sql_dir = self._settings.sql_dir

        steps: list[tuple[Path, str]] = [
            (sql_dir / "01_landing" / "ddl" / "create_tables.sql", "DDL landing_zone"),
            (sql_dir / "02_staging" / "ddl" / "create_tables.sql", "DDL staging"),
            (sql_dir / "04_service" / "ddl" / "create_dimensions.sql", "DDL dimensiones"),
            (sql_dir / "04_service" / "dml" / "populate_dim_tiempo.sql", "Poblando dim_tiempo"),
            (sql_dir / "04_service" / "ddl" / "create_facts.sql", "DDL hechos"),
        ]

        for path, desc in steps:
            logger.info("PASO DDL: %s", desc)
            if not self._repo.execute_file(path, desc):
                return False

        return True

    def _load_csvs(self) -> bool:
        logger.info("PASO 1: CSV → Landing Zone")
        results = self._ingestion.load_all(truncate=True)
        return all(results.values())

    def _run_staging(self) -> bool:
        logger.info("PASO 2: Landing → Staging (MERGE con soft deletes)")
        return self._staging.run_merges()

    def _run_service(self) -> bool:
        logger.info("PASO 3: Staging → Service (Data Warehouse)")
        return self._service_layer.run_merges()

    # ------------------------------------------------------------------
    # Utilidades de logging
    # ------------------------------------------------------------------

    def _log_header(self, msg: str) -> None:
        logger.info("=" * 80)
        logger.info(msg)
        logger.info("=" * 80)

    def _fail(self, msg: str, start_time: datetime) -> bool:
        elapsed = datetime.now() - start_time
        logger.error("❌ PIPELINE FALLIDO: %s  |  Tiempo: %s", msg, elapsed)
        return False


# ---------------------------------------------------------------------------
# Punto de entrada CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecutar pipeline de Data Engineering end-to-end"
    )
    parser.add_argument(
        "--create-schema",
        action="store_true",
        help="Crear schemas antes de ejecutar el pipeline",
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Crear/recrear tablas antes de ejecutar el pipeline",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    orchestrator = PipelineOrchestrator()
    success = orchestrator.run(
        create_schema=args.create_schema,
        create_tables=args.create_tables,
    )
    sys.exit(0 if success else 1)
