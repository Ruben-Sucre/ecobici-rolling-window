from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import polars as pl
import pytest

from scripts import quality_check


def _write_quality_parquet(path: Path, rows: int = 3) -> Path:
    base_start = datetime(2024, 1, 1, 7, 0, 0)
    df = pl.DataFrame(
        {
            "genero": ["H", "M", "-"][:rows],
            "edad": [29, 34, 0][:rows],
            "bici_id": [111, 222, 333][:rows],
            "estacion_origen_id": [10, 11, 12][:rows],
            "estacion_destino_id": [20, 21, 22][:rows],
            "fecha_hora_retiro": [base_start + timedelta(minutes=i * 15) for i in range(rows)],
            "fecha_hora_arribo": [base_start + timedelta(minutes=i * 15 + 12) for i in range(rows)],
        }
    )
    df.write_parquet(path)
    return path


def test_ejecutar_control_calidad_ok(temp_data_dir: Path) -> None:
    parquet_path = temp_data_dir / "ecobici_2024-04.parquet"
    _write_quality_parquet(parquet_path)

    assert quality_check.ejecutar_control_calidad(parquet_path.name, temp_data_dir)


def test_ejecutar_control_calidad_detecta_inconsistencias(temp_data_dir: Path) -> None:
    parquet_path = temp_data_dir / "ecobici_2024-05.parquet"

    rows = 10
    base_start = datetime(2024, 2, 1, 7, 0, 0)
    df = pl.DataFrame(
        {
            "genero": ["H"] * 8 + [None, None],
            "edad": [30] * rows,
            "bici_id": list(range(500, 510)),
            "estacion_origen_id": [50] * rows,
            "estacion_destino_id": [60] * rows,
            "fecha_hora_retiro": [base_start + timedelta(minutes=i * 10) for i in range(rows)],
            "fecha_hora_arribo": [base_start + timedelta(minutes=i * 10 + 100) for i in range(rows)],
        }
    )
    df.write_parquet(parquet_path)

    assert not quality_check.ejecutar_control_calidad(parquet_path.name, temp_data_dir)
