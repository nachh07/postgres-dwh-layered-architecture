# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 — builder: instala deps, ejecuta linter
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

LABEL maintainer="Nachh07"
LABEL description="ETL Pipeline — Builder Stage (DWH Layered Architecture)"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependencias del sistema necesarias para compilar psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar TODAS las dependencias (incluyendo ruff, pytest)
COPY config/requirements.txt /app/config/requirements.txt
RUN pip install --no-cache-dir -r /app/config/requirements.txt \
    && pip install --no-cache-dir ruff

# Copiar código fuente
COPY src/ /app/src/
COPY sql/ /app/sql/

# Ejecutar linter — falla el build si hay errores de calidad de código
RUN ruff check /app/src/

# ---------------------------------------------------------------------------
# Stage 2 — runtime: imagen limpia solo con lo esencial para producción
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="Nachh07"
LABEL description="ETL Pipeline — Runtime Stage (DWH Layered Architecture)"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Solo las dependencias de sistema necesarias en runtime (psycopg2 binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo las dependencias de producción ya instaladas desde builder
# (excluye ruff, pytest y herramientas de dev)
COPY config/requirements.txt /app/config/requirements.txt
RUN pip install --no-cache-dir \
        psycopg2-binary==2.9.9 \
        python-dotenv==1.0.0

# Copiar artefactos de código desde el builder
COPY --from=builder /app/src/ /app/src/
COPY --from=builder /app/sql/ /app/sql/

# El directorio data/ y logs/ se montan como volúmenes en docker-compose
# para no empaquetar los CSVs dentro de la imagen.

# Punto de entrada — puede sobreescribirse en docker-compose con `command:`
CMD ["python", "-m", "src.domain.pipeline.pipeline_orchestrator"]
