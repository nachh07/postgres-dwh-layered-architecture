# PR: Implementación de CI/CD Pipeline Automático (GitHub Actions) 🚀

## 📝 Descripción
Este Pull Request introduce un flujo de trabajo de Integración Continua y Entrega Continua (CI/CD) completamente funcional para el proyecto DWH. A partir de ahora, cada cambio en el código pasará por rigurosos controles de calidad (Linting, Unit Testing y Testing de Integración reales contra bases de datos en contenedores), y será automáticamente construido y publicado en Docker Hub cuando se incorpore a la rama principal (`main`).

## ✨ Cambios Realizados

### 1. 🤖 GitHub Actions Workflow (`.github/workflows/main_pipeline.yml`)
- Se agregó el flujo de trabajo principal que se activa en `push` y `pull_request` sobre `main` y `develop`.
- **Job `test`**:
  - Implementación de un **Service Container de PostgreSQL 17 Alpine** para ejecutar tests reales.
  - Verificación de formato y sintaxis con `ruff check .`.
  - Ejecución de la suite de Tests Unitarios de Pytest, fallando si la **cobertura es menor al 80%**.
  - Ejecución de los nuevos **Tests de Integración** excluyéndolos de los cálculos de cobertura para evitar el falso negativo.
- **Job `deploy`**:
  - Conexión e inicio de sesión seguro contra **Docker Hub** usando Secrets en GitHub (`DB_PASSWORD`, `DOCKER_HUB_USERNAME`, `DOCKER_HUB_TOKEN`).
  - Construcción y empuje condicional automático a Docker Hub con tags de versión `latest` y hash del commit.
  - Se configuró la estrategia de cacheo de GHA (GitHub Actions Cache) para agilizar dramáticamente la compilación de la imagen.

### 2. 🐳 Refactor del Dockerfile (Multi-stage Build)
- El archivo `Dockerfile` fue reescrito de cero utilizando una arquitectura de multi-etapas (*multi-stage build*).
  - **Stage 1 (`builder`)**: Instala herramientas de compilación pesadas como `gcc` y herramientas de desarrollo como `ruff` y dependencias de testeo.
  - **Stage 2 (`runtime`)**: Genera una imagen limpia y compacta construida desde `python:3.11-slim`, usando las librerías binarias estrictamente necesarias, ignorando todo lo de compilación o testeo. 

### 3. 🧪 Tests de Integración (`tests/infrastructure/test_db_integration.py`)
- Se implementaron los tests para comprobar el funcionamiento final del workflow de GitHub y la conectividad a la base real.
- `test_database_connection_real`: Verifica si hay "ping" y el contenedor responde correctamente de forma asíncrona en el pipeline.
- `test_database_write_operation`: Crea, inserta registros (CRUD), hace asserts y limpia una tabla llamada `ci_metadata` directo sobre la DB dinámica efímera para certificar el acceso DML.

### 4. 🛠️ Configuración (Pyproject.toml y Requirements)
- Adición de `ruff` dentro de `config/requirements.txt` a fin de estandarizar su instalación.
- Creación de perfiles `[tool.ruff]` en `pyproject.toml` definiendo línea en 100 caracteres, target de Python 3.11 y validaciones comunes (isort automático).
- Se registró un custom mark llamado `integration` en Pytest para independizar tests reales y unitarios (mockeados).

### 5. 🧹 Correcciones de Linting a Nivel Global
- Re-formateo exhaustivo de archivos antiguos bajo `python/` y ajustes en `src/` aplicando auto-fixes para solucionar 156 observaciones de lint (espacios en blancos y largas líneas que rompían el límite de `E501`).

## 🛑 Pruebas Realizadas
- [X] Pipeline completo corriendo satisfactoriamente en GitHub Actions sin romper.
- [X] Los tests Unitarios reportan cobertura > 80%.
- [X] Los tests de Integración acceden exitosamente a PostgreSQL e interactúan con él sin mezclar la cobertura del repo general (`--no-cov`).
- [X] El linter (`ruff`) retorna exitoso (`All checks passed!`).
- [X] Docker build completado en multi-stage subiendo un contenedor de menor tamaño y más eficiente.

## 🔗 Asignación y Review
Listo para merge. Solicito revisión y merge en `main`.
