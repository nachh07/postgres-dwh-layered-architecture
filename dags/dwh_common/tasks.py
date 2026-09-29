"""
Callables de los tasks de Airflow.

Cada función envuelve un paso del pipeline existente (src/) sin cambiar su
lógica. Los servicios de src/ devuelven False y loguean cuando algo falla;
Airflow, en cambio, solo marca un task en rojo si se lanza una excepción.
Por eso cada callable convierte un resultado False en `PipelineStepError`.
"""

import logging

from dwh_common.config import EXPECTED_FACT_COUNTS
from src.domain.pipeline.pipeline_orchestrator import PipelineOrchestrator
from src.domain.services.ingestion_service import IngestionService
from src.infrastructure.database.connection import default_db
from src.infrastructure.repositories.sql_repository import default_repo
from src.shared.config.settings import settings

logger = logging.getLogger(__name__)

# Carpetas de los scripts MERGE (las mismas que usan StagingService y ServiceLayerService)
STAGING_DML_DIR = ("02_staging", "dml")
SERVICE_DML_DIR = ("04_service", "dml")


class PipelineStepError(RuntimeError):
    """Un paso del pipeline devolvió False (el detalle está en el log del task)."""


def ensure(success: bool, message: str) -> None:
    """
    Lanza `PipelineStepError` si `success` es False.

    Args:
        success: Resultado devuelto por un servicio o repositorio de src/.
        message: Mensaje de error que se mostrará en Airflow.
    """
    if not success:
        raise PipelineStepError(message)


# ---------------------------------------------------------------------------
# DAG dwh_init
# ---------------------------------------------------------------------------


def initialize_dwh() -> None:
    """Recrea schemas y tablas del DWH (DESTRUCTIVO: DROP SCHEMA ... CASCADE)."""
    success = PipelineOrchestrator().run(create_schema=True, create_tables=True, only_init=True)
    ensure(success, "Falló la creación de schemas/tablas. Revisá el log del task.")


# ---------------------------------------------------------------------------
# DAG dwh_pipeline
# ---------------------------------------------------------------------------


def check_csv_files() -> None:
    """Verifica que existan todos los CSV esperados (`Settings.csv_table_mapping`)."""
    missing = [
        csv_name
        for csv_name in settings.csv_table_mapping
        if not (settings.data_dir / csv_name).is_file()
    ]
    if missing:
        raise FileNotFoundError(
            f"Faltan {len(missing)} CSV en {settings.data_dir}: {', '.join(missing)}"
        )
    logger.info("✅ %d CSV encontrados en %s", len(settings.csv_table_mapping), settings.data_dir)


def load_landing() -> None:
    """Carga todos los CSV a landing_zone (TRUNCATE + COPY)."""
    results = IngestionService().load_all(truncate=True)
    failed = [csv_name for csv_name, ok in results.items() if not ok]
    ensure(
        bool(results) and not failed,
        f"Falló la carga a landing de: {', '.join(failed) or 'ningún CSV procesado'}. "
        "¿Se ejecutó el DAG dwh_init?",
    )


def run_staging_merge(script_name: str) -> None:
    """Ejecuta un script MERGE de landing_zone → staging."""
    _run_script(STAGING_DML_DIR, script_name)


def run_service_merge(script_name: str) -> None:
    """Ejecuta un script MERGE de staging → service (dimensión o hecho)."""
    _run_script(SERVICE_DML_DIR, script_name)


def validate_counts() -> None:
    """
    Compara conteos reales contra los esperados y falla si alguno no coincide.

    - raw_ventas == stg_ventas activas (is_deleted = FALSE)
    - cada tabla de hechos == EXPECTED_FACT_COUNTS
    """
    checks: list[tuple[str, int, int]] = [
        (
            "staging.stg_ventas (activas) vs landing_zone.raw_ventas",
            _count_active_stg_ventas(),
            default_repo.get_table_count("landing_zone", "raw_ventas"),
        )
    ]
    for table, expected in EXPECTED_FACT_COUNTS.items():
        checks.append(
            (f"service.{table}", default_repo.get_table_count("service", table), expected)
        )

    errors = []
    for description, actual, expected in checks:
        ok = actual == expected and actual >= 0
        logger.info(
            "%s %s: real=%s esperado=%s", "✅" if ok else "❌", description, actual, expected
        )
        if not ok:
            errors.append(f"{description}: real={actual} esperado={expected}")

    ensure(not errors, "Validación de conteos fallida: " + "; ".join(errors))


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _run_script(subdirs: tuple[str, ...], script_name: str) -> None:
    script_path = settings.sql_dir.joinpath(*subdirs, script_name)
    entity = script_name.removeprefix("merge_").removesuffix(".sql")
    success = default_repo.execute_file(script_path, f"MERGE {entity}")
    ensure(success, f"Falló {script_path.name}. Revisá el log del task.")


def _count_active_stg_ventas() -> int:
    """Cuenta ventas no borradas en staging (-1 si hay error, como get_table_count)."""
    try:
        with default_db.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM staging.stg_ventas WHERE is_deleted = FALSE;")
            return cur.fetchone()[0]
    except Exception as exc:
        logger.error("Error al contar staging.stg_ventas activas: %s", exc)
        return -1
