"""
Script para ingestar CSVs a la capa Landing Zone usando COPY de PostgreSQL
"""

import csv
from pathlib import Path

from python.config.database import get_connection
from python.config.settings import CSV_TABLE_MAPPING, DATA_DIR, SPECIAL_DELIMITERS
from python.utils.db_utils import get_table_count, truncate_table
from python.utils.logger import setup_logger

logger = setup_logger(__name__, "csv_ingestion.log")

# Mapeo de columnas para cada tabla (excluyendo created_at que tiene DEFAULT)
TABLE_COLUMNS = {
    "raw_clientes": [
        "id",
        "provincia",
        "nombre_y_apellido",
        "domicilio",
        "telefono",
        "edad",
        "localidad",
        "x",
        "y",
        "fecha_alta",
        "usuario_alta",
        "fecha_ultima_modificacion",
        "usuario_ultima_modificacion",
        "marca_baja",
        "col10",
    ],
    "raw_ventas": [
        "idventa",
        "fecha",
        "fecha_entrega",
        "idcanal",
        "idcliente",
        "idsucursal",
        "idempleado",
        "idproducto",
        "precio",
        "cantidad",
    ],
    "raw_productos": ["id_producto", "concepto", "tipo", "precio"],
    "raw_compras": ["idcompra", "fecha", "idproducto", "cantidad", "precio", "idproveedor"],
    "raw_gastos": ["idgasto", "idsucursal", "idtipogasto", "fecha", "monto"],
    "raw_empleados": [
        "id_empleado",
        "apellido",
        "nombre",
        "sucursal",
        "sector",
        "cargo",
        "salario",
    ],
    "raw_sucursales": [
        "id",
        "sucursal",
        "direccion",
        "localidad",
        "provincia",
        "latitud",
        "longitud",
    ],
    "raw_proveedores": [
        "idproveedor",
        "nombre",
        "address",
        "city",
        "state",
        "country",
        "departamen",
    ],
    "raw_canal_venta": ["codigo", "descripcion"],
    "raw_tipo_gasto": ["idtipogasto", "descripcion", "monto_aproximado"],
}


def detect_delimiter(csv_path: Path, filename: str) -> str:
    """
    Detecta el delimitador del CSV

    Args:
        csv_path: Path al archivo CSV
        filename: Nombre del archivo

    Returns:
        str: Delimitador detectado
    """
    # Primero verificar si tiene delimitador especial configurado
    if filename in SPECIAL_DELIMITERS:
        return SPECIAL_DELIMITERS[filename]

    # Detectar automáticamente
    with csv_path.open("r", encoding="latin1") as f:
        first_line = f.readline()
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(first_line).delimiter
        return delimiter


def load_csv_to_landing(csv_path: Path, table_name: str, truncate: bool = True) -> bool:
    """
    Carga un CSV a una tabla de landing_zone usando COPY

    Args:
        csv_path: Path al archivo CSV
        table_name: Nombre de la tabla en landing_zone
        truncate: Si True, trunca la tabla antes de cargar

    Returns:
        bool: True si se cargó correctamente
    """
    logger.info(f"📥 Cargando {csv_path.name} → landing_zone.{table_name}")

    try:
        # Truncar tabla si se solicita
        if truncate:
            truncate_table("landing_zone", table_name)

        # Detectar delimitador
        delimiter = detect_delimiter(csv_path, csv_path.name)
        logger.info(f"   Delimitador detectado: '{delimiter}'")

        # Obtener columnas de la tabla
        columns = TABLE_COLUMNS.get(table_name, [])
        if not columns:
            raise ValueError(f"No se encontraron columnas configuradas para {table_name}")

        columns_str = ", ".join(columns)

        # Cargar con COPY
        with get_connection() as conn:
            with conn.cursor() as cur:
                with csv_path.open("r", encoding="latin1") as f:
                    # Saltar header
                    next(f)

                    # COPY desde archivo especificando columnas
                    cur.copy_expert(
                        f"""
                        COPY landing_zone.{table_name} ({columns_str})
                        FROM STDIN
                        WITH (
                            FORMAT CSV,
                            DELIMITER '{delimiter}',
                            QUOTE '"',
                            ESCAPE '"',
                            NULL '',
                            ENCODING 'LATIN1'
                        )
                        """,
                        f,
                    )

        # Verificar conteo
        count = get_table_count("landing_zone", table_name)
        logger.info(f"✅ {csv_path.name} cargado: {count:,} registros")
        return True

    except Exception as e:
        logger.error(f"❌ Error cargando {csv_path.name}: {e}")
        return False


def load_all_csvs(truncate: bool = True) -> dict:
    """
    Carga todos los CSVs configurados a landing_zone

    Args:
        truncate: Si True, trunca las tablas antes de cargar

    Returns:
        dict: Resumen de la carga {filename: success}
    """
    logger.info("🚀 Iniciando carga masiva de CSVs a Landing Zone")
    logger.info(f"   Directorio de datos: {DATA_DIR}")

    results = {}

    for csv_filename, table_name in CSV_TABLE_MAPPING.items():
        csv_path = DATA_DIR / csv_filename

        if not csv_path.exists():
            logger.warning(f"⚠️  Archivo no encontrado: {csv_filename}")
            results[csv_filename] = False
            continue

        success = load_csv_to_landing(csv_path, table_name, truncate)
        results[csv_filename] = success

    # Resumen
    successful = sum(1 for v in results.values() if v)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"📊 Resumen: {successful}/{total} archivos cargados exitosamente")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    load_all_csvs(truncate=True)
