"""
ETL: Landing Zone → Staging
Ejecuta scripts MERGE para todas las tablas de staging
"""
from pathlib import Path
from python.config.settings import SQL_DIR
from python.utils.logger import setup_logger
from python.utils.db_utils import execute_sql_file, get_table_count

logger = setup_logger(__name__, 'landing_to_staging.log')

# Orden de ejecución de MERGEs
MERGE_SCRIPTS_ORDER = [
    'merge_canal_venta.sql',
    'merge_tipo_gasto.sql',
    'merge_sucursales.sql',
    'merge_proveedores.sql',
    'merge_productos.sql',
    'merge_clientes.sql',
    'merge_empleados.sql',
    'merge_ventas.sql',
    'merge_compras.sql',
    'merge_gastos.sql',
]


def run_staging_merges() -> bool:
    """
    Ejecuta todos los scripts MERGE de landing → staging
    
    Returns:
        bool: True si todos se ejecutaron correctamente
    """
    logger.info("🔄 Iniciando MERGE de Landing → Staging")
    
    merge_dir = SQL_DIR / '02_staging' / 'dml'
    all_success = True
    
    for script_name in MERGE_SCRIPTS_ORDER:
        script_path = merge_dir / script_name
        
        if not script_path.exists():
            logger.warning(f"⚠️  Script no encontrado: {script_name}")
            continue
        
        # Ejecutar MERGE
        success = execute_sql_file(
            script_path,
            f"MERGE {script_name.replace('merge_', '').replace('.sql', '')}"
        )
        
        all_success = all_success and success
    
    # Resumen de tablas staging
    logger.info("=" * 60)
    logger.info("📊 Resumen de tablas Staging:")
    
    staging_tables = [
        'stg_clientes', 'stg_ventas', 'stg_productos',
        'stg_compras', 'stg_gastos', 'stg_empleados',
        'stg_sucursales', 'stg_proveedores',
        'stg_canal_venta', 'stg_tipo_gasto'
    ]
    
    for table in staging_tables:
        count = get_table_count('staging', table)
        logger.info(f"   {table}: {count:,} registros")
    
    logger.info("=" * 60)
    
    return all_success


if __name__ == "__main__":
    success = run_staging_merges()
    exit(0 if success else 1)
