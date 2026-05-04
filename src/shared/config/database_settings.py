"""
Configuración de base de datos.

Lee las variables de entorno (desde config/.env o entorno del contenedor)
y expone la clase `DatabaseSettings` con los parámetros de conexión.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """
    Carga el archivo .env desde config/.env relativo a la raíz del proyecto.
    Si no existe, intenta cargar del directorio de trabajo actual.
    """
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / "config" / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        print(
            f"[WARN] No se encontró .env en: {env_path}. Usando variables de entorno del sistema."
        )
        load_dotenv()


# Cargar en tiempo de importación
_load_env()


@dataclass(frozen=True)
class DatabaseSettings:
    """
    Parámetros de conexión a PostgreSQL.

    Se instancia a partir de variables de entorno cargadas desde config/.env
    o desde el entorno del sistema (Docker, CI, etc.).
    """

    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("DB_NAME", "data_engineering"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    def as_dict(self) -> dict:
        """Retorna los parámetros como dict listo para psycopg2.connect(**...)."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }

    def __repr__(self) -> str:
        """Oculta la contraseña en representaciones de texto."""
        return (
            f"DatabaseSettings(host={self.host!r}, port={self.port}, "
            f"database={self.database!r}, user={self.user!r}, password='***')"
        )


# Instancia global
db_settings = DatabaseSettings()
