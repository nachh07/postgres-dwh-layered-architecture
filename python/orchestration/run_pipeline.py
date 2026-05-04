"""
Orquestador Principal del Pipeline de Data Engineering
Ejecuta el pipeline completo: CSV → Landing → Staging → Transformation → Service
"""
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from python.utils.logger import setup_logger
from python.utils.db_utils import execute_sql_file
from python.config.settings import SQL_DIR
from python.ingestion.csv_to_landing import load_all_csvs
from python.etl.landing_to_staging import run_staging_merges

logger = setup_logger(__name__, 'pipeline_run.log')


def create_schemas() -> bool:
    """
    Crea los schemas del proyecto (landing_zone, staging, transformation, service)
    
    Returns:
        bool: True si se crearon correctamente
    """
    logger.info("PASO 0: Creando schemas")
    
    schema_script = SQL_DIR / '00_schemas' / 'create_schemas.sql'
    return execute_sql_file(schema_script, "Creando schemas")


def create_landing_tables() -> bool:
    """
    Crea las tablas de landing_zone
    
    Returns:
        bool: True si se crearon correctamente
    """
    logger.info("PASO 1a: Creando tablas de Landing Zone")
    
    landing_ddl = SQL_DIR / '01_landing' / 'ddl' / 'create_tables.sql'
    return execute_sql_file(landing_ddl, "Creando tablas de landing_zone")


def create_staging_tables() -> bool:
    """
    Crea las tablas de staging
    
    Returns:
        bool: True si se crearon correctamente
    """
    logger.info("PASO 2a: Creando tablas de Staging")
    
    staging_ddl = SQL_DIR / '02_staging' / 'ddl' / 'create_tables.sql'
    return execute_sql_file(staging_ddl, "Creando tablas de staging")


def create_service_tables() -> bool:
    """
    Crea las dimensiones y hechos del data warehouse
    
    Returns:
        bool: True si se crearon correctamente
    """
    logger.info("PASO 4a: Creando tablas de Service (Data Warehouse)")
    
    service_dir = SQL_DIR / '04_service' / 'ddl'
    
    # Crear dimensiones
    dim_script = service_dir / 'create_dimensions.sql'
    if not execute_sql_file(dim_script, "Creando dimensiones"):
        return False
    
    # Poblar dimensión tiempo
    populate_tiempo = SQL_DIR / '04_service' / 'dml' / 'populate_dim_tiempo.sql'
    if not execute_sql_file(populate_tiempo, "Poblando dim_tiempo"):
        return False
    
    # Crear hechos
    fact_script = service_dir / 'create_facts.sql'
    return execute_sql_file(fact_script, "Creando tablas de hechos")


def load_csvs_to_landing(truncate: bool = True) -> bool:
    """
    Carga CSVs a landing_zone
    
    Args:
        truncate: Si True, trunca las tablas antes de cargar
    
    Returns:
        bool: True si se cargaron todos correctamente
    """
    logger.info("PASO 1b: Cargando CSVs a Landing Zone")
    
    results = load_all_csvs(truncate=truncate)
    return all(results.values())


def merge_landing_to_staging() -> bool:
    """
    Ejecuta MERGEs de landing → staging
    
    Returns:
        bool: True si todos se ejecutaron correctamente
    """
    logger.info("PASO 2b: MERGE Landing -> Staging")
    
    return run_staging_merges()


def merge_staging_to_service() -> bool:
    """
    Ejecuta MERGEs de staging → service (dimensiones y hechos)
    
    Returns:
        bool: True si se ejecutaron correctamente
    """
    logger.info("PASO 4b: MERGE Staging -> Service (Dimensiones y Hechos)")
    
    service_dml_dir = SQL_DIR / '04_service' / 'dml'
    
    # Orden: primero dimensiones, luego hechos
    dimension_merges = [
        'merge_dim_cliente.sql',
        'merge_dim_producto.sql',
        'merge_dim_sucursal.sql',
        'merge_dim_empleado.sql',
        'merge_dim_proveedor.sql',
        'merge_dim_canal.sql',
        'merge_dim_tipo_gasto.sql',
    ]
    
    fact_merges = [
        'merge_fact_ventas.sql',
        'merge_fact_compras.sql',
        'merge_fact_gastos.sql',
    ]
    
    all_success = True
    
    # Ejecutar MERGEs de dimensiones
    logger.info("   Cargando Dimensiones...")
    for script_name in dimension_merges:
        script_path = service_dml_dir / script_name
        if script_path.exists():
            dim_name = script_name.replace('merge_', '').replace('.sql', '')
            success = execute_sql_file(script_path, f"MERGE {dim_name}")
            all_success = all_success and success
        else:
            logger.warning(f"   Script no encontrado: {script_name}")
    
    # Ejecutar MERGEs de hechos
    logger.info("   Cargando Hechos...")
    for script_name in fact_merges:
        script_path = service_dml_dir / script_name
        if script_path.exists():
            fact_name = script_name.replace('merge_', '').replace('.sql', '')
            success = execute_sql_file(script_path, f"MERGE {fact_name}")
            all_success = all_success and success
        else:
            logger.warning(f"   Script no encontrado: {script_name}")
    
    return all_success


def run_full_pipeline(create_schema: bool = False, create_tables: bool = False) -> bool:
    """
    Ejecuta el pipeline completo de data engineering
    
    Args:
        create_schema: Si True, crea los schemas primero
        create_tables: Si True, crea las tablas primero
    
    Returns:
        bool: True si todo se ejecutó correctamente
    """
    start_time = datetime.now()
    
    logger.info("=" * 80)
    logger.info("INICIANDO PIPELINE DE DATA ENGINEERING")
    logger.info("=" * 80)
    
    try:
        # Paso 0: Crear schemas (opcional)
        if create_schema:
            if not create_schemas():
                logger.error("ERROR - Error creando schemas")
                return False
        
        # Paso 1: Crear tablas (opcional)
        if create_tables:
            if not create_landing_tables():
                logger.error("ERROR - Error creando tablas de landing")
                return False
            
            if not create_staging_tables():
                logger.error("ERROR - Error creando tablas de staging")
                return False
            
            if not create_service_tables():
                logger.error("ERROR - Error creando tablas de service")
                return False
        
        # Paso 2: CSV → Landing
        if not load_csvs_to_landing(truncate=True):
            logger.error("ERROR - Error cargando CSVs a landing")
            return False
        
        # Paso 3: Landing → Staging (MERGE con soft deletes)
        if not merge_landing_to_staging():
            logger.error("ERROR - Error en MERGE landing -> staging")
            return False
        
        # Paso 4: Staging → Service (Data Warehouse)
        if not merge_staging_to_service():
            logger.error("ERROR - Error en MERGE staging -> service")
            return False
        
        # Fin
        elapsed = datetime.now() - start_time
        logger.info("=" * 80)
        logger.info(f"OK - PIPELINE COMPLETADO EXITOSAMENTE")
        logger.info(f"   Tiempo de ejecucion: {elapsed}")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR - Error inesperado en el pipeline: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutar pipeline de data engineering')
    parser.add_argument('--create-schema', action='store_true', help='Crear schemas antes de ejecutar')
    parser.add_argument('--create-tables', action='store_true', help='Crear tablas antes de ejecutar')
    
    args = parser.parse_args()
    
    success = run_full_pipeline(
        create_schema=args.create_schema,
        create_tables=args.create_tables
    )
    
    exit(0 if success else 1)
