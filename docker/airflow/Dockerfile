# =============================================================================
# Imagen de Airflow para orquestar el pipeline del DWH
#
# - Base oficial apache/airflow (misma versión que whale-alert-el).
# - El código (src/, sql/, dags/) y los datos (data/) NO se copian:
#   se montan como volúmenes en docker-compose.yml.
# =============================================================================
ARG AIRFLOW_VERSION=2.9.1
ARG PYTHON_VERSION=3.11
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

ARG AIRFLOW_VERSION
ARG PYTHON_VERSION

# Raíz del proyecto dentro del contenedor.
# Settings calcula la raíz como 4 niveles arriba de src/shared/config/settings.py
# (→ /opt/dwh) y crea /opt/dwh/logs al importarse, así que el usuario airflow
# debe poder escribir ahí. data/ queda en /opt/dwh/data.
ENV PYTHONPATH=/opt/dwh \
    PYTHONDONTWRITEBYTECODE=1

USER root
RUN mkdir -p /opt/dwh/logs /opt/dwh/data \
    && chown -R airflow:root /opt/dwh \
    && chmod -R g+rwX /opt/dwh
USER airflow

# Instala solo lo que falte, respetando el constraints file oficial de Airflow
# (evita que pip actualice dependencias de Airflow a versiones incompatibles).
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir \
        "apache-airflow==${AIRFLOW_VERSION}" \
        -r /requirements.txt \
        --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
