from __future__ import annotations

from pathlib import Path

import pytest
import polars as pl

from scripts import process_data


def test_obtener_csv_pendientes_filters_processed(temp_data_dir: Path) -> None:
    csv_a = temp_data_dir / "2024-01.csv"
    csv_b = temp_data_dir / "2024-02.csv"
    csv_a.write_text("sample")
    csv_b.write_text("sample")

    (temp_data_dir / "ecobici_2024-02.parquet").touch()

    pendientes = process_data.obtener_csv_pendientes(temp_data_dir)

    assert pendientes == [csv_a]


def test_procesar_csv_a_parquet_generates_expected_schema(
    temp_data_dir: Path,
    sample_raw_df: pl.DataFrame,
) -> None:
    csv_path = temp_data_dir / "2024-03.csv"
    sample_raw_df.write_csv(csv_path)

    assert process_data.procesar_csv_a_parquet(csv_path, temp_data_dir)

    parquet_path = temp_data_dir / "ecobici_2024-03.parquet"
    assert parquet_path.exists()

    df = pl.read_parquet(parquet_path)
    assert df.columns == [
        "genero",
        "edad",
        "bici_id",
        "estacion_origen_id",
        "estacion_destino_id",
        "fecha_origen",
        "fecha_destino",
    ]
    assert df.height == sample_raw_df.height
    assert df["edad"].dtype == pl.Int64
    assert df["genero"].to_list() == ["M", "M", "O"]


def test_procesar_raises_on_missing_columns(tmp_path: Path):
    csv_path = tmp_path / "2024-04.csv"
    # Header that doesn't map to required columns
    csv_path.write_text("a,b,c\n1,2,3\n")
    from scripts.utils.exceptions import DataValidationError

    with pytest.raises(DataValidationError):
        process_data.procesar_csv_a_parquet(csv_path, tmp_path)


def test_procesar_raises_on_empty_csv(tmp_path: Path):
    csv_path = tmp_path / "2024-05.csv"
    # Header with correct columns but no data
    header = ",".join([
        "Genero_Usuario",
        "Edad_Usuario",
        "Bici",
        "Ciclo_Estacion_Retiro",
        "Ciclo_EstacionArribo",
        "Fecha_Retiro",
        "Hora_Retiro",
        "Fecha_Arribo",
        "Hora_Arribo",
    ])
    csv_path.write_text(header + "\n")
    from scripts.utils.exceptions import DataValidationError

    with pytest.raises(DataValidationError):
        process_data.procesar_csv_a_parquet(csv_path, tmp_path)


def test_procesar_raises_on_all_invalid_dates(tmp_path: Path):
    csv_path = tmp_path / "2024-06.csv"
    header = "Genero_Usuario,Edad_Usuario,Bici,Ciclo_Estacion_Retiro,Ciclo_EstacionArribo,Fecha_Retiro,Hora_Retiro,Fecha_Arribo,Hora_Arribo\n"
    # Row with invalid dates and times; Edad_Usuario is empty to be treated as null
    row = "-,,1,1,2,invalid,::,invalid,::\n"
    csv_path.write_text(header + row)
    from scripts.utils.exceptions import DataValidationError

    with pytest.raises(DataValidationError):
        process_data.procesar_csv_a_parquet(csv_path, tmp_path)
