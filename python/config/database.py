"""
Configuración de conexión a PostgreSQL
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager
from pathlib import Path

# Cargar variables de entorno desde config/.env
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / 'config' / '.env'

# Debug: mostrar si encontró el archivo
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    print(f"ADVERTENCIA: No se encontro el archivo .env en: {ENV_PATH}")
    load_dotenv()  # Intentar cargar del directorio actual

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'data_engineering'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}


@contextmanager
def get_connection():
    """
    Context manager para conexiones a PostgreSQL
    
    Uso:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tabla")
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


@contextmanager
def get_cursor(dict_cursor=False):
    """
    Context manager para obtener un cursor directamente
    
    Args:
        dict_cursor: Si True, retorna resultados como diccionarios
    
    Uso:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM tabla")
            results = cur.fetchall()
    """
    with get_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()


def test_connection():
    """
    Prueba la conexión a la base de datos
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                print(f"OK - Conexion exitosa a PostgreSQL")
                print(f"   Version: {version[0]}")
                return True
    except Exception as e:
        print(f"ERROR - Error de conexion: {e}")
        return False


if __name__ == "__main__":
    test_connection()
