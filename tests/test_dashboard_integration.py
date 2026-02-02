import pytest
import importlib

import polars as pl


def test_render_dashboard_minimal(monkeypatch):
    # Dobles para evitar dependencias pesadas: init_engine, cargar_metadata, ejecutar_analisis
    import scripts.dashboard as dashboard

    monkeypatch.setattr(dashboard, "init_engine", lambda: object())
    monkeypatch.setattr(dashboard, "cargar_metadata", lambda engine: {"anios_disponibles": [2024]})

    dummy_results = {
        "metrics": {"total_viajes": 1, "promedio_minutos": 10.0, "mediana_edad": 30},
        "viajes_por_mes": pl.DataFrame({"mes_anio": ["2024-01"], "viajes": [1], "viajes_rolling_3m": [1.0]}),
        "horas_pico": pl.DataFrame({"hora_retiro": [7], "viajes": [1]}),
        "viajes_por_hora": pl.DataFrame({"hora_retiro": [7], "viajes": [1]}),
        "top_estaciones_origen": pl.DataFrame({"estacion_origen_id": [1], "viajes": [1]}),
        "top_estaciones_destino": pl.DataFrame({"estacion_destino_id": [2], "viajes": [1]}),
        "top_bicis_viajes": pl.DataFrame({"bici_id": [101], "viajes": [1]}),
        "top_bicis_viajes_cortos": pl.DataFrame(),
        "distribucion_genero": pl.DataFrame({"genero": ["M"], "viajes": [1]}),
    }

    monkeypatch.setattr(dashboard, "ejecutar_analisis", lambda engine, filtros: dummy_results)

    # Llamar a la función principal; el test pasa si no lanza excepción
    dashboard.render_dashboard()

def test_dashboard_imports():
    try:
        importlib.import_module("scripts.dashboard")
    except Exception as e:
        pytest.fail(f"El dashboard no debe fallar al importar: {e}")

# Para pruebas más avanzadas de integración UI, se recomienda usar streamlit-testing o selenium.
