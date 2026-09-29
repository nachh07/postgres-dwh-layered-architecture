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


def inicializar_dwh() -> None:
    """Recrea schemas y tablas del DWH (DESTRUCTIVO: DROP SCHEMA ... CASCADE)."""
    success = PipelineOrchestrator().run(create_schema=True, create_tables=True, only_init=True)
    ensure(success, "Falló la creación de schemas/tablas. Revisá el log del task.")


# ---------------------------------------------------------------------------
# DAG dwh_pipeline
# ---------------------------------------------------------------------------


def verificar_csvs() -> None:
    """Verifica que existan todos los CSV esperados (`Settings.csv_table_mapping`)."""
    faltantes = [
        csv_name
        for csv_name in settings.csv_table_mapping
        if not (settings.data_dir / csv_name).is_file()
    ]
    if faltantes:
        raise FileNotFoundError(
            f"Faltan {len(faltantes)} CSV en {settings.data_dir}: {', '.join(faltantes)}"
        )
    logger.info(
        "✅ %d CSV encontrados en %s", len(settings.csv_table_mapping), settings.data_dir
    )


def cargar_landing() -> None:
    """Carga todos los CSV a landing_zone (TRUNCATE + COPY)."""
    results = IngestionService().load_all(truncate=True)
    fallidos = [csv_name for csv_name, ok in results.items() if not ok]
    ensure(
        bool(results) and not fallidos,
        f"Falló la carga a landing de: {', '.join(fallidos) or 'ningún CSV procesado'}. "
        "¿Se ejecutó el DAG dwh_init?",
    )


def ejecutar_merge_staging(script_name: str) -> None:
    """Ejecuta un script MERGE de landing_zone → staging."""
    _ejecutar_script(STAGING_DML_DIR, script_name)


def ejecutar_merge_service(script_name: str) -> None:
    """Ejecuta un script MERGE de staging → service (dimensión o hecho)."""
    _ejecutar_script(SERVICE_DML_DIR, script_name)


def validar_conteos() -> None:
    """
    Compara conteos reales contra los esperados y falla si alguno no coincide.

    - raw_ventas == stg_ventas activas (is_deleted = FALSE)
    - cada tabla de hechos == EXPECTED_FACT_COUNTS
    """
    checks: list[tuple[str, int, int]] = [
        (
            "staging.stg_ventas (activas) vs landing_zone.raw_ventas",
            _contar_stg_ventas_activas(),
            default_repo.get_table_count("landing_zone", "raw_ventas"),
        )
    ]
    for table, expected in EXPECTED_FACT_COUNTS.items():
        checks.append(
            (f"service.{table}", default_repo.get_table_count("service", table), expected)
        )

    errores = []
    for descripcion, real, esperado in checks:
        ok = real == esperado and real >= 0
        logger.info(
            "%s %s: real=%s esperado=%s", "✅" if ok else "❌", descripcion, real, esperado
        )
        if not ok:
            errores.append(f"{descripcion}: real={real} esperado={esperado}")

    ensure(not errores, "Validación de conteos fallida: " + "; ".join(errores))


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _ejecutar_script(subdirs: tuple[str, ...], script_name: str) -> None:
    script_path = settings.sql_dir.joinpath(*subdirs, script_name)
    entity = script_name.removeprefix("merge_").removesuffix(".sql")
    success = default_repo.execute_file(script_path, f"MERGE {entity}")
    ensure(success, f"Falló {script_path.name}. Revisá el log del task.")


def _contar_stg_ventas_activas() -> int:
    """Cuenta ventas no borradas en staging (-1 si hay error, como get_table_count)."""
    try:
        with default_db.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM staging.stg_ventas WHERE is_deleted = FALSE;")
            return cur.fetchone()[0]
    except Exception as exc:
        logger.error("Error al contar staging.stg_ventas activas: %s", exc)
        return -1
