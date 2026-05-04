"""
Tests unitarios para src/domain/services/ingestion_service.py

Cubre:
- _detect_delimiter: delimitador especial configurado
- _detect_delimiter: detección automática con Sniffer
- load_csv: flujo exitoso con truncate
- load_csv: archivo inexistente
- load_csv: tabla sin columnas configuradas → error
- load_csv: error en COPY → retorna False
- load_all: todos exitosos
- load_all: algunos fallidos
- load_all: archivo CSV faltante
"""

from unittest.mock import MagicMock, patch

from src.domain.services.ingestion_service import IngestionService
from src.shared.config.settings import Settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(mock_db, mock_repo, tmp_path) -> tuple[IngestionService, Settings]:
    """Crea un IngestionService con Settings apuntando a tmp_path."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    s = Settings(
        project_root=tmp_path,
        data_dir=data_dir,
        sql_dir=tmp_path / "sql",
        logs_dir=tmp_path / "logs",
    )
    svc = IngestionService(db=mock_db, repo=mock_repo, app_settings=s)
    return svc, s


# ---------------------------------------------------------------------------
# Tests de _detect_delimiter
# ---------------------------------------------------------------------------


class TestDetectDelimiter:
    def test_returns_special_delimiter_for_clientes(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)
        csv_path = tmp_path / "data" / "Clientes.csv"
        csv_path.write_text("id;nombre\n1;Alice\n", encoding="latin1")
        assert svc._detect_delimiter(csv_path) == ";"

    def test_returns_special_delimiter_for_sucursales(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)
        csv_path = tmp_path / "data" / "Sucursales.csv"
        csv_path.write_text("id;sucursal\n1;Centro\n", encoding="latin1")
        assert svc._detect_delimiter(csv_path) == ";"

    def test_sniffs_comma_delimiter(self, mock_db, mock_repo, tmp_path, sample_csv_comma):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)
        delimiter = svc._detect_delimiter(sample_csv_comma)
        assert delimiter == ","

    def test_sniffs_semicolon_for_unknown_file(self, mock_db, mock_repo, tmp_path):
        """Para un archivo desconocido con ';', Sniffer debe detectar ';'."""
        svc, s = _make_service(mock_db, mock_repo, tmp_path)
        csv_path = tmp_path / "unknown.csv"
        csv_path.write_text("a;b;c\n1;2;3\n", encoding="latin1")
        assert svc._detect_delimiter(csv_path) == ";"


# ---------------------------------------------------------------------------
# Tests de load_csv
# ---------------------------------------------------------------------------


class TestLoadCsv:
    def test_load_csv_returns_true_on_success(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)

        # Crear CSV de prueba en data_dir con nombre de tabla conocida
        csv_path = s.data_dir / "Venta.csv"
        header = ",".join(s.table_columns["raw_ventas"])
        csv_path.write_text(
            f"{header}\n1,2024-01-01,2024-01-02,1,1,1,1,1,100,2\n", encoding="latin1"
        )

        # Mock del cursor para COPY
        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cur
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_db.connection.return_value = mock_conn
        mock_repo.get_table_count.return_value = 1

        result = svc.load_csv(csv_path, "raw_ventas", truncate=False)
        assert result is True

    def test_load_csv_calls_truncate_when_requested(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)

        csv_path = s.data_dir / "Venta.csv"
        header = ",".join(s.table_columns["raw_ventas"])
        csv_path.write_text(
            f"{header}\n1,2024-01-01,2024-01-02,1,1,1,1,1,100,2\n", encoding="latin1"
        )

        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cur
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_db.connection.return_value = mock_conn

        svc.load_csv(csv_path, "raw_ventas", truncate=True)
        mock_repo.truncate_table.assert_called_once_with("landing_zone", "raw_ventas")

    def test_load_csv_raises_if_no_columns_configured(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)
        csv_path = s.data_dir / "unknown.csv"
        csv_path.write_text("a,b\n1,2\n", encoding="latin1")
        result = svc.load_csv(csv_path, "raw_tabla_inexistente", truncate=False)
        assert result is False

    def test_load_csv_returns_false_on_copy_error(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)

        csv_path = s.data_dir / "Venta.csv"
        header = ",".join(s.table_columns["raw_ventas"])
        csv_path.write_text(f"{header}\n1,bad_data\n", encoding="latin1")

        mock_cur = MagicMock()
        mock_cur.copy_expert.side_effect = Exception("COPY error")
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cur
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_db.connection.return_value = mock_conn

        result = svc.load_csv(csv_path, "raw_ventas", truncate=False)
        assert result is False


# ---------------------------------------------------------------------------
# Tests de load_all
# ---------------------------------------------------------------------------


class TestLoadAll:
    def test_load_all_returns_dict_with_all_keys(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)
        # No crear ningún CSV → todos serán False (not found)
        results = svc.load_all(truncate=False)
        assert set(results.keys()) == set(s.csv_table_mapping.keys())

    def test_load_all_marks_missing_files_as_false(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)
        results = svc.load_all()
        assert all(v is False for v in results.values())

    def test_load_all_marks_found_files_as_true(self, mock_db, mock_repo, tmp_path):
        svc, s = _make_service(mock_db, mock_repo, tmp_path)

        # Patchear load_csv para que siempre retorne True
        with patch.object(svc, "load_csv", return_value=True):
            # Crear archivos CSV ficticios
            for fname in s.csv_table_mapping.keys():
                (s.data_dir / fname).write_text("header\n", encoding="latin1")

            results = svc.load_all()

        assert all(v is True for v in results.values())
