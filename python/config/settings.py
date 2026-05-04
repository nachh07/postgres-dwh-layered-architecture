"""
Configuración general del proyecto
"""

import os
from pathlib import Path

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Rutas de datos
DATA_DIR = PROJECT_ROOT / "data"
SQL_DIR = PROJECT_ROOT / "sql"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorio de logs si no existe
LOGS_DIR.mkdir(exist_ok=True)

# Configuración de CSV
CSV_ENCODING = "latin1"  # Encoding por defecto para CSVs
CSV_DELIMITER = ","
CSV_DELIMITER_ALT = ";"  # Delimiter alternativo para algunos archivos

# Mapeo de archivos CSV a tablas de landing
CSV_TABLE_MAPPING = {
    "Clientes.csv": "raw_clientes",
    "Venta.csv": "raw_ventas",
    "Productos.csv": "raw_productos",
    "Compra.csv": "raw_compras",
    "Gasto.csv": "raw_gastos",
    "Empleados.csv": "raw_empleados",
    "Sucursales.csv": "raw_sucursales",
    "Proveedores.csv": "raw_proveedores",
    "CanalDeVenta.csv": "raw_canal_venta",
    "TiposDeGasto.csv": "raw_tipo_gasto",
}

# Configuración de delimitadores especiales por archivo
SPECIAL_DELIMITERS = {
    "Clientes.csv": ";",
    "Sucursales.csv": ";",
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
