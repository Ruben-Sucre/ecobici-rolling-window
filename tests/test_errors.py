import polars as pl
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from scripts import analysis

def _write_parquet_with_errors(path: Path):
    df = pl.DataFrame({
        "genero": ["M", "F", "?", None],
        "edad": [28, None, 150, -5],
        "bici_id": [101, 102, 103, 104],
        "estacion_origen_id": [11, 12, 13, 14],
        "estacion_destino_id": [21, 22, 23, 24],
        "fecha_origen": [datetime(2024, 6, 1, 7, 0), datetime(2024, 6, 1, 8, 0), None, datetime(2024, 6, 1, 9, 0)],
        "fecha_destino": [datetime(2024, 6, 1, 7, 12), datetime(2024, 6, 1, 8, 12), datetime(2024, 6, 1, 8, 30), None],
    })
    df.write_parquet(path)

def test_engine_handles_invalid_data(tmp_path):
    parquet_path = tmp_path / "ecobici_invalid.parquet"
    _write_parquet_with_errors(parquet_path)
    engine = analysis.EcobiciEngine(data_dir=tmp_path)
    # Debe poder inicializar y procesar sin lanzar excepción
    try:
        results = engine.get_filtered_query().collect()
    except Exception as e:
        pytest.fail(f"Engine failed with invalid data: {e}")
    # Verifica que los géneros desconocidos se mapean a 'O'
    genero_vals = results["genero"].unique().to_list()
    assert set(genero_vals).issubset({"M", "F", "O"})

def test_engine_handles_corrupt_file(tmp_path):
    corrupt_path = tmp_path / "corrupt.parquet"
    corrupt_path.write_bytes(b"not a parquet file")
    with pytest.raises(Exception):
        analysis.EcobiciEngine(data_dir=tmp_path).get_filtered_query().collect()
