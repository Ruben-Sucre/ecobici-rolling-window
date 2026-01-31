import pytest
import importlib

def test_dashboard_imports():
    try:
        importlib.import_module("scripts.dashboard")
    except Exception as e:
        pytest.fail(f"El dashboard no debe fallar al importar: {e}")

# Para pruebas más avanzadas de integración UI, se recomienda usar streamlit-testing o selenium.
