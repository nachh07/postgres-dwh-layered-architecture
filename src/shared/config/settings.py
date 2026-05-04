"""
Configuración general del proyecto.

Este módulo centraliza todas las rutas, constantes y mapeos del proyecto.
Expone la clase `Settings` como punto único de verdad para la configuración.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


# ---------------------------------------------------------------------------
# Raíz del proyecto (calculada en tiempo de importación)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@dataclass(frozen=True)
class Settings:
    """
    Configuración inmutable del proyecto.

    Todos los paths son absolutos y se calculan a partir de `project_root`.
    El frozen=True garantiza que no se modifiquen en tiempo de ejecución.
    """

    # ---- Directorios principales ------------------------------------------
    project_root: Path = field(default_factory=lambda: _PROJECT_ROOT)
    data_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "data")
    sql_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "sql")
    logs_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "logs")

    # ---- Configuración de CSV ---------------------------------------------
    csv_encoding: str = "latin1"
    csv_default_delimiter: str = ","
    csv_alt_delimiter: str = ";"

    # ---- Logging ----------------------------------------------------------
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ---- Mapeo CSV → tabla landing_zone ----------------------------------
    csv_table_mapping: Dict[str, str] = field(
        default_factory=lambda: {
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
    )

    # ---- Delimitadores especiales por archivo ----------------------------
    special_delimiters: Dict[str, str] = field(
        default_factory=lambda: {
            "Clientes.csv": ";",
            "Sucursales.csv": ";",
        }
    )

    # ---- Columnas por tabla (para COPY sin created_at) ------------------
    table_columns: Dict[str, list] = field(
        default_factory=lambda: {
            "raw_clientes": [
                "id", "provincia", "nombre_y_apellido", "domicilio",
                "telefono", "edad", "localidad", "x", "y", "fecha_alta",
                "usuario_alta", "fecha_ultima_modificacion",
                "usuario_ultima_modificacion", "marca_baja", "col10",
            ],
            "raw_ventas": [
                "idventa", "fecha", "fecha_entrega", "idcanal",
                "idcliente", "idsucursal", "idempleado", "idproducto",
                "precio", "cantidad",
            ],
            "raw_productos": ["id_producto", "concepto", "tipo", "precio"],
            "raw_compras": [
                "idcompra", "fecha", "idproducto", "cantidad",
                "precio", "idproveedor",
            ],
            "raw_gastos": ["idgasto", "idsucursal", "idtipogasto", "fecha", "monto"],
            "raw_empleados": [
                "id_empleado", "apellido", "nombre", "sucursal",
                "sector", "cargo", "salario",
            ],
            "raw_sucursales": [
                "id", "sucursal", "direccion", "localidad",
                "provincia", "latitud", "longitud",
            ],
            "raw_proveedores": [
                "idproveedor", "nombre", "address", "city",
                "state", "country", "departamen",
            ],
            "raw_canal_venta": ["codigo", "descripcion"],
            "raw_tipo_gasto": ["idtipogasto", "descripcion", "monto_aproximado"],
        }
    )

    def __post_init__(self) -> None:
        """Crea el directorio de logs si no existe."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Instancia global (singleton de módulo)
settings = Settings()
