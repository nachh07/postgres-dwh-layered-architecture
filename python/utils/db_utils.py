"""
Utilidades para base de datos
"""
from pathlib import Path
from python.config.database import get_cursor
from python.utils.logger import setup_logger

logger = setup_logger(__name__)


def execute_sql_file(sql_file_path: Path, description: str = None) -> bool:
    """
    Ejecuta un archivo SQL
    
    Args:
        sql_file_path: Path al archivo SQL
        description: Descripción de la operación (para logging)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
    desc = description or f"Ejecutando {sql_file_path.name}"
    logger.info(f"🔄 {desc}")
    
    try:
        with sql_file_path.open('r', encoding='utf-8') as f:
            sql = f.read()
        
        with get_cursor() as cur:
            cur.execute(sql)
        
        logger.info(f"✅ {desc} - Completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ {desc} - Error: {e}")
        return False


def execute_sql(sql: str, description: str = None) -> bool:
    """
    Ejecuta una sentencia SQL
    
    Args:
        sql: Sentencia SQL a ejecutar
        description: Descripción de la operación
    
    Returns:
        bool: True si se ejecutó correctamente
    """
    desc = description or "Ejecutando SQL"
    logger.info(f"🔄 {desc}")
    
    try:
        with get_cursor() as cur:
            cur.execute(sql)
        
        logger.info(f"✅ {desc} - Completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ {desc} - Error: {e}")
        return False


def get_table_count(schema: str, table: str) -> int:
    """
    Obtiene el conteo de registros de una tabla
    
    Args:
        schema: Nombre del schema
        table: Nombre de la tabla
    
    Returns:
        int: Cantidad de registros
    """
    sql = f"SELECT COUNT(*) FROM {schema}.{table};"
    
    try:
        with get_cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error al obtener conteo de {schema}.{table}: {e}")
        return -1


def truncate_table(schema: str, table: str) -> bool:
    """
    Trunca una tabla
    
    Args:
        schema: Nombre del schema
        table: Nombre de la tabla
    
    Returns:
        bool: True si se truncó correctamente
    """
    sql = f"TRUNCATE TABLE {schema}.{table} CASCADE;"
    return execute_sql(sql, f"Truncando {schema}.{table}")
