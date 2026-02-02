from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

from scripts import quality_check


def test_detectar_columnas_denormalizadas_simple() -> None:
    schema = {
        "estacion_id": pl.Int64,
        "estacion_nombre": pl.Utf8,
        "usuario_id": pl.Int64,
        "otro_campo": pl.Int64,
    }

    denorm = quality_check._detectar_columnas_denormalizadas(schema)
    assert "estacion_nombre" in denorm
    assert "usuario_id" not in denorm


def test_resolver_columnas_fecha_varios_casos() -> None:
    s1 = {"fecha_origen": pl.Datetime, "fecha_destino": pl.Datetime}
    assert quality_check._resolver_columnas_fecha(s1) == ("fecha_origen", "fecha_destino")

    s2 = {"fecha_hora_retiro": pl.Datetime, "fecha_hora_arribo": pl.Datetime}
    assert quality_check._resolver_columnas_fecha(s2) == ("fecha_hora_retiro", "fecha_hora_arribo")

    s3 = {"inicio_viaje": pl.Datetime, "fin_viaje": pl.Datetime}
    assert quality_check._resolver_columnas_fecha(s3) == ("inicio_viaje", "fin_viaje")


def test_chequear_integridad_referencial_detecta_fallos(tmp_path: Path) -> None:
    # Crear fact con estaciones 1..3
    base = datetime(2024, 1, 1, 7, 0)
    df_fact = pl.DataFrame(
        {
            "estacion_origen_id": [1, 2, 3],
            "fecha_origen": [base, base + timedelta(minutes=10), base + timedelta(minutes=20)],
        }
    )
    fact_path = tmp_path / "ecobici_2024-01.parquet"
    df_fact.write_parquet(fact_path)

    # Crear dimensión estaciones que sólo contiene 1..2 (falta 3)
    df_dim = pl.DataFrame({"id": [1, 2], "nombre": ["A", "B"]})
    dim_path = tmp_path / "estaciones.parquet"
    df_dim.write_parquet(dim_path)

    schema = pl.scan_parquet(fact_path).collect_schema()

    issues = quality_check._chequear_integridad_referencial(fact_path, schema, tmp_path)
    # Debe detectar fallo referencial para estacion_origen_id
    assert any("Fallo referencial" in s for s in issues)
