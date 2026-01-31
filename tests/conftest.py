from __future__ import annotations

from pathlib import Path
import sys

# Ensure the repository root is on PYTHONPATH so tests can import `scripts`.
# This is a minimal, safe adjustment for CI/test environments where top-level
# package imports may fail.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from typing import Iterator

try:
    import polars as pl
except Exception:  # pragma: no cover - entorno sin polars
    pl = None
import pytest

from scripts.utils.paths import get_data_dir


@pytest.fixture(autouse=True)
def clear_data_dir_cache() -> Iterator[None]:
    get_data_dir.cache_clear()
    yield
    get_data_dir.cache_clear()


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    base = tmp_path / "data"
    base.mkdir()
    return base


@pytest.fixture
def sample_raw_df():
    if pl is None:
        pytest.skip("polars no está instalado en el entorno", allow_module_level=False)
    return pl.DataFrame(
        {
            "Genero_Usuario": ["H", "M", "-"],
            "Edad_Usuario": [29, 34, None],
            "Bici": [101, 202, 303],
            "Ciclo_Estacion_Retiro": [12, 18, 21],
            "Ciclo_EstacionArribo": [22, 18, 25],
            "Fecha_Retiro": ["01/01/2024", "02/01/2024", "03/01/2024"],
            "Hora_Retiro": ["07:15:00", "08:00:00", "09:30:00"],
            "Fecha_Arribo": ["01/01/2024", "02/01/2024", "03/01/2024"],
            "Hora_Arribo": ["07:25:00", "08:25:00", "09:50:00"],
        }
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as performance when running in CI."""
    import os
    import pytest

    if os.getenv("CI") == "true":
        skip_perf = pytest.mark.skip(reason="Skip performance tests on CI")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_perf)


def pytest_configure(config):
    """Register custom markers to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line("markers", "integration: integration tests that touch external resources")
    config.addinivalue_line("markers", "performance: performance/benchmark tests")
