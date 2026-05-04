"""
Script para configurar automaticamente el archivo .env
"""

from pathlib import Path

# Configuración
DB_PASSWORD = "root"  # CAMBIAR AQUI si es necesario

# Ruta del proyecto
project_root = Path(__file__).parent.parent.parent
env_file = project_root / "config" / ".env"

# Contenido del .env
env_content = f"""# Configuracion de PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=data_engineering
DB_USER=postgres
DB_PASSWORD={DB_PASSWORD}

# Configuracion de rutas
DATA_DIR=./data
LOG_LEVEL=INFO

# Configuracion de CSV
CSV_ENCODING=latin1
"""

# Escribir archivo
print(f"Creando archivo: {env_file}")
with open(env_file, "w", encoding="utf-8") as f:
    f.write(env_content)

print("Archivo .env creado exitosamente!")
print()
print("Contenido:")
print("-" * 50)
# Mostrar contenido ocultando password
for line in env_content.split("\n"):
    if "PASSWORD" in line and "=" in line:
        parts = line.split("=")
        print(f"{parts[0]}=***oculto***")
    else:
        print(line)
print("-" * 50)
