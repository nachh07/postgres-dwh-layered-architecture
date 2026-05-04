"""
Capa de dominio — Servicio de Staging (Landing → Staging).

La clase `StagingService` encapsula la lógica de ejecución de los
scripts MERGE que transforman datos de landing_zone a staging.
"""

from src.infrastructure.repositories.sql_repository import SQLRepository, default_repo
from src.shared.config.settings import Settings, settings
from src.shared.logger import get_logger

logger = get_logger(__name__, "landing_to_staging.log")

# Orden de ejecución de MERGEs (respeta dependencias entre entidades)
_MERGE_ORDER = [
    "merge_canal_venta.sql",
    "merge_tipo_gasto.sql",
    "merge_sucursales.sql",
    "merge_proveedores.sql",
    "merge_productos.sql",
    "merge_clientes.sql",
    "merge_empleados.sql",
    "merge_ventas.sql",
    "merge_compras.sql",
    "merge_gastos.sql",
]

_STAGING_TABLES = [
    "stg_clientes",
    "stg_ventas",
    "stg_productos",
    "stg_compras",
    "stg_gastos",
    "stg_empleados",
    "stg_sucursales",
    "stg_proveedores",
    "stg_canal_venta",
    "stg_tipo_gasto",
]


class StagingService:
    """
    Servicio de transformación Landing → Staging.

    Ejecuta los scripts MERGE en el orden correcto y reporta
    el conteo de registros resultante en cada tabla de staging.

    Uso:
        svc = StagingService()
        success = svc.run_merges()
    """

    def __init__(
        self,
        repo: SQLRepository = default_repo,
        app_settings: Settings = settings,
    ) -> None:
        """
        Args:
            repo:         Repositorio SQL.
            app_settings: Configuración del proyecto.
        """
        self._repo = repo
        self._settings = app_settings

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run_merges(self) -> bool:
        """
        Ejecuta todos los scripts MERGE de landing_zone → staging.

        Returns:
            True si todos los scripts se ejecutaron sin errores.
        """
        logger.info("🔄 Iniciando MERGE de Landing → Staging")

        merge_dir = self._settings.sql_dir / "02_staging" / "dml"
        all_success = True

        for script_name in _MERGE_ORDER:
            script_path = merge_dir / script_name

            if not script_path.exists():
                logger.warning("⚠️  Script no encontrado: %s", script_name)
                continue

            entity = script_name.replace("merge_", "").replace(".sql", "")
            success = self._repo.execute_file(script_path, f"MERGE {entity}")
            all_success = all_success and success

        self._log_summary()
        return all_success

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _log_summary(self) -> None:
        """Registra el conteo de registros de cada tabla de staging."""
        logger.info("=" * 60)
        logger.info("📊 Resumen de tablas Staging:")
        for table in _STAGING_TABLES:
            count = self._repo.get_table_count("staging", table)
            logger.info("   %s: %s registros", table, f"{count:,}")
        logger.info("=" * 60)
