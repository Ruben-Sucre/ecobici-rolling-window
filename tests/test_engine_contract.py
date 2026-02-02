from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

from scripts import analysis


def _write_month_parquet(path: Path, start: datetime) -> None:
    df = pl.DataFrame(
        {
            "genero": ["M", "F"],
            "edad": [28, 35],
            "bici_id": [101, 102],
            "estacion_origen_id": [11, 12],
            "estacion_destino_id": [21, 22],
            "fecha_origen": [start, start + timedelta(minutes=30)],
            "fecha_destino": [start + timedelta(minutes=12), start + timedelta(minutes=52)],
        }
    )
    df.write_parquet(path)


def test_run_full_analysis_contract(temp_data_dir: Path) -> None:
    # Crear datos mínimos
    _write_month_parquet(temp_data_dir / "ecobici_2024-06.parquet", datetime(2024, 6, 1, 7, 0))

    engine = analysis.EcobiciEngine(temp_data_dir)
    results = engine.run_full_analysis()

    # Claves esperadas por el dashboard
    expected_keys = {
        "metrics",
        "viajes_por_mes",
        "horas_pico",
        "viajes_por_hora",
        "top_estaciones_origen",
        "top_estaciones_destino",
        "top_bicis_viajes",
        "top_bicis_viajes_cortos",
        "distribucion_genero",
    }

    assert expected_keys.issubset(set(results.keys()))

    # Verificar que viajes_por_mes tenga columnas mínimas
    vpm = results["viajes_por_mes"]
    assert "mes_anio" in vpm.columns
    assert "viajes" in vpm.columns
