"""
Capa de dominio — Servicio de carga al Data Warehouse (Staging → Service).

La clase `ServiceLayerService` orquesta los MERGEs de dimensiones
y hechos que construyen el Star Schema en el schema `service`.
"""

from src.infrastructure.repositories.sql_repository import SQLRepository, default_repo
from src.shared.config.settings import Settings, settings
from src.shared.logger import get_logger

logger = get_logger(__name__, "staging_to_service.log")

# Orden: dimensiones primero, luego hechos (respeta FK)
_DIMENSION_MERGES = [
    "merge_dim_cliente.sql",
    "merge_dim_producto.sql",
    "merge_dim_sucursal.sql",
    "merge_dim_empleado.sql",
    "merge_dim_proveedor.sql",
    "merge_dim_canal.sql",
    "merge_dim_tipo_gasto.sql",
]

_FACT_MERGES = [
    "merge_fact_ventas.sql",
    "merge_fact_compras.sql",
    "merge_fact_gastos.sql",
]


class ServiceLayerService:
    """
    Servicio de carga al Data Warehouse (schema `service`).

    Ejecuta los MERGEs de dimensiones y hechos en el orden correcto.

    Uso:
        svc = ServiceLayerService()
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
        Ejecuta los MERGEs de dimensiones y hechos en el orden correcto.

        Returns:
            True si todos los scripts se ejecutaron sin errores.
        """
        logger.info("⭐ Iniciando MERGE Staging → Service (DWH)")
        service_dml = self._settings.sql_dir / "04_service" / "dml"
        all_success = True

        # ---- Dimensiones -------------------------------------------------
        logger.info("   Cargando Dimensiones...")
        for script_name in _DIMENSION_MERGES:
            script_path = service_dml / script_name
            dim_name = script_name.replace("merge_", "").replace(".sql", "")
            if script_path.exists():
                success = self._repo.execute_file(script_path, f"MERGE {dim_name}")
                all_success = all_success and success
            else:
                logger.warning("⚠️  Script no encontrado: %s", script_name)

        # ---- Hechos ------------------------------------------------------
        logger.info("   Cargando Hechos...")
        for script_name in _FACT_MERGES:
            script_path = service_dml / script_name
            fact_name = script_name.replace("merge_", "").replace(".sql", "")
            if script_path.exists():
                success = self._repo.execute_file(script_path, f"MERGE {fact_name}")
                all_success = all_success and success
            else:
                logger.warning("⚠️  Script no encontrado: %s", script_name)

        return all_success
