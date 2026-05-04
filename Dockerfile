# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Etapa única: Python + dependencias + código fuente
# ---------------------------------------------------------------------------
FROM python:3.11-slim

LABEL maintainer="Nachh07"
LABEL description="ETL Pipeline — PostgreSQL DWH Layered Architecture"

# Variables de entorno del sistema
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# --- Dependencias del sistema (psycopg2 binaries) -------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Dependencias Python --------------------------------------------------
# Copiar solo requirements primero para aprovechar la caché de Docker
COPY config/requirements.txt /app/config/requirements.txt
RUN pip install --no-cache-dir -r /app/config/requirements.txt

# --- Código fuente --------------------------------------------------------
COPY src/       /app/src/
COPY sql/       /app/sql/

# El directorio data/ y logs/ se montan como volúmenes en docker-compose
# para no empaquetar los CSVs dentro de la imagen.

# --- Punto de entrada por defecto -----------------------------------------
# Se puede sobreescribir en docker-compose con `command:`
CMD ["python", "-m", "src.domain.pipeline.pipeline_orchestrator"]
