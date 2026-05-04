"""
Tests unitarios para src/shared/config/settings.py

Cubre:
- Tipos y valores por defecto de Settings
- Paths calculados desde project_root
- Mapeo CSV → tabla landing_zone
- Delimitadores especiales
- Columnas por tabla
- Creación automática del directorio de logs
"""
import pytest
from pathlib import Path
from src.shared.config.settings import Settings, settings


class TestSettingsDefaults:
    """Tests sobre los valores por defecto del singleton `settings`."""

    def test_project_root_is_path(self):
        assert isinstance(settings.project_root, Path)

    def test_data_dir_resolves_correctly(self):
        assert settings.data_dir == settings.project_root / "data"

    def test_sql_dir_resolves_correctly(self):
        assert settings.sql_dir == settings.project_root / "sql"

    def test_logs_dir_resolves_correctly(self):
        assert settings.logs_dir == settings.project_root / "logs"

    def test_csv_encoding_default(self):
        assert settings.csv_encoding == "latin1"

    def test_default_delimiter(self):
        assert settings.csv_default_delimiter == ","

    def test_alt_delimiter(self):
        assert settings.csv_alt_delimiter == ";"

    def test_log_format_contains_levelname(self):
        assert "%(levelname)s" in settings.log_format


class TestCsvTableMapping:
    """Tests del mapeo CSV → tabla."""

    def test_mapping_has_ten_entries(self):
        assert len(settings.csv_table_mapping) == 10

    def test_clientes_maps_to_raw_clientes(self):
        assert settings.csv_table_mapping["Clientes.csv"] == "raw_clientes"

    def test_venta_maps_to_raw_ventas(self):
        assert settings.csv_table_mapping["Venta.csv"] == "raw_ventas"

    def test_all_values_start_with_raw(self):
        for table in settings.csv_table_mapping.values():
            assert table.startswith("raw_"), f"{table!r} no empieza con 'raw_'"


class TestSpecialDelimiters:
    """Tests de los delimitadores especiales."""

    def test_clientes_has_semicolon(self):
        assert settings.special_delimiters["Clientes.csv"] == ";"

    def test_sucursales_has_semicolon(self):
        assert settings.special_delimiters["Sucursales.csv"] == ";"

    def test_venta_not_in_special(self):
        assert "Venta.csv" not in settings.special_delimiters


class TestTableColumns:
    """Tests de las columnas por tabla."""

    def test_raw_ventas_has_idventa(self):
        assert "idventa" in settings.table_columns["raw_ventas"]

    def test_raw_clientes_has_id(self):
        assert "id" in settings.table_columns["raw_clientes"]

    def test_all_tables_have_columns(self):
        for table, cols in settings.table_columns.items():
            assert len(cols) > 0, f"Tabla {table!r} sin columnas"

    def test_ten_tables_configured(self):
        assert len(settings.table_columns) == 10


class TestSettingsCustomization:
    """Tests de Settings con valores personalizados (tmp_path)."""

    def test_custom_project_root(self, tmp_path):
        custom = Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            sql_dir=tmp_path / "sql",
            logs_dir=tmp_path / "logs",
        )
        assert custom.project_root == tmp_path

    def test_logs_dir_created_on_init(self, tmp_path):
        logs = tmp_path / "new_logs"
        assert not logs.exists()
        Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            sql_dir=tmp_path / "sql",
            logs_dir=logs,
        )
        assert logs.exists()

    def test_settings_is_frozen(self):
        """Settings no se puede mutar en tiempo de ejecución."""
        with pytest.raises((AttributeError, TypeError)):
            settings.csv_encoding = "utf-8"  # type: ignore
