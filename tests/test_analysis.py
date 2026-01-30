from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl
import pytest

from scripts import analysis


def _write_month_parquet(path: Path, start: datetime) -> None:
    df = pl.DataFrame(
        {
            "genero": ["H", "M"],
            "edad": [28, 35],
            "bici_id": [101, 102],
            "estacion_origen_id": [11, 12],
            "estacion_destino_id": [21, 22],
            "fecha_hora_retiro": [start, start + timedelta(minutes=30)],
            "fecha_hora_arribo": [start + timedelta(minutes=12), start + timedelta(minutes=52)],
        }
    )
    df.write_parquet(path)


def test_generar_reporte_mensual_sintetico(temp_data_dir: Path) -> None:
    _write_month_parquet(temp_data_dir / "ecobici_2024-06.parquet", datetime(2024, 6, 1, 7, 0))
    _write_month_parquet(temp_data_dir / "ecobici_2024-07.parquet", datetime(2024, 7, 1, 7, 0))

    # Test del wrapper (compatibilidad)
    reporte = analysis.generar_reporte_mensual(temp_data_dir)
    assert "REPORTE AUTOMÁTICO ECOBICI" in reporte
    assert "Total de viajes" in reporte
    assert "Viajes por mes" in reporte


def test_ecobici_engine_sintetico(temp_data_dir: Path) -> None:
    """Prueba la nueva API de EcobiciEngine."""
    _write_month_parquet(temp_data_dir / "ecobici_2024-06.parquet", datetime(2024, 6, 1, 7, 0))
    _write_month_parquet(temp_data_dir / "ecobici_2024-07.parquet", datetime(2024, 7, 1, 7, 0))

    engine = analysis.EcobiciEngine(temp_data_dir)
    results = engine.run_full_analysis()

    # Verificar estructura de resultados
    assert "metrics" in results
    assert "viajes_por_mes" in results
    assert "base_data" in results
    
    # Verificar métricas
    metrics = results["metrics"]
    assert metrics["total_viajes"] == 4  # 2 viajes por archivo
    assert metrics["promedio_minutos"] > 0
    assert metrics["mediana_edad"] > 0
    
    # Verificar DataFrame de viajes por mes
    viajes_mes = results["viajes_por_mes"]
    assert len(viajes_mes) == 2  # Dos meses
    assert "mes_anio" in viajes_mes.columns
    assert "viajes" in viajes_mes.columns


@pytest.mark.integration
def test_generar_reporte_mensual_real_file(temp_data_dir: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    real_parquet = repo_root / "data" / "ecobici_2025-12.parquet"

    if not real_parquet.exists():
        pytest.skip("Parquet real no disponible en el repositorio")

    shutil.copy(real_parquet, temp_data_dir / real_parquet.name)

    reporte = analysis.generar_reporte_mensual(temp_data_dir)

    assert "Total de viajes" in reporte
    assert "Periodo analizado" in reporte
