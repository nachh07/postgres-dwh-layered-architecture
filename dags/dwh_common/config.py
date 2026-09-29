"""
Configuración de los DAGs del DWH (único lugar para cambiar parámetros).
"""

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Parámetros comunes de los DAGs
# ---------------------------------------------------------------------------

# Fecha "naive": Airflow la interpreta en AIRFLOW__CORE__DEFAULT_TIMEZONE
# (America/Argentina/Buenos_Aires, definido en docker-compose.yml).
START_DATE = datetime(2026, 1, 1)

# Las cargas son idempotentes (TRUNCATE + MERGE), por eso reintentar es seguro.
DEFAULT_ARGS = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

# ---------------------------------------------------------------------------
# Validación final del pipeline
# ---------------------------------------------------------------------------

# Registros esperados en cada tabla de hechos para los CSV actuales de data/.
# Si cambian los CSV, actualizá estos valores.
EXPECTED_FACT_COUNTS: dict[str, int] = {
    "fact_ventas": 46_645,
    "fact_compras": 11_539,
    "fact_gastos": 8_640,
}
