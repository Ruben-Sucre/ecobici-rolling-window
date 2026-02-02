from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

from scripts import analysis


def _write_parquet(path: Path, rows: list[dict]) -> None:
    df = pl.DataFrame(rows)
    df.write_parquet(path)


def test_get_filtered_query_various_filters(tmp_path: Path) -> None:
    # Crear datos con distintas fechas, géneros y duraciones
    base = datetime(2024, 1, 1, 7, 0)
    rows = [
        {
            "genero": "M",
            "edad": 30,
            "bici_id": 101,
            "estacion_origen_id": 1,
            "estacion_destino_id": 10,
            "fecha_origen": base,
            "fecha_destino": base + timedelta(minutes=10),
        },
        {
            "genero": "F",
            "edad": 40,
            "bici_id": 102,
            "estacion_origen_id": 2,
            "estacion_destino_id": 20,
            "fecha_origen": datetime(2023, 1, 1, 7, 0),
            "fecha_destino": datetime(2023, 1, 1, 7, 0) + timedelta(minutes=200),
        },
        {
            "genero": "O",
            "edad": 25,
            "bici_id": 103,
            "estacion_origen_id": 1,
            "estacion_destino_id": 11,
            "fecha_origen": datetime(2024, 2, 1, 7, 0),
            "fecha_destino": datetime(2024, 2, 1, 7, 2),
        },
    ]

    # Escribir un archivo que el engine leerá
    parquet_path = tmp_path / "ecobici_2024-01.parquet"
    _write_parquet(parquet_path, rows)

    engine = analysis.EcobiciEngine(data_dir=tmp_path)

    # Filtrar por año 2024 -> debe devolver 2 filas (las de 2024)
    lf_2024 = engine.get_filtered_query({"anios": [2024]})
    df_2024 = lf_2024.collect()
    assert len(df_2024) == 2

    # Filtrar por género 'F' pero aumentar duracion_max para incluir viaje largo
    lf_f = engine.get_filtered_query({"generos": ["F"], "duracion_max": 1000})
    df_f = lf_f.collect()
    assert len(df_f) == 1
    assert df_f[0, "genero"] == "F"

    # Filtrar por estación origen 1 -> dos viajes
    lf_est1 = engine.get_filtered_query({"estaciones_origen": [1]})
    assert lf_est1.collect().height == 2

    # Rango de edad
    lf_age = engine.get_filtered_query({"rango_edad": (26, 35)})
    assert lf_age.collect().height == 1

    # Test get_filtered_data columnas: solicitar columna inexistente debe lanzar ValueError
    try:
        _ = engine.get_filtered_data(columns=["no_such_column"])
        raise AssertionError("Expected ValueError for nonexistent columns")
    except ValueError:
        pass
