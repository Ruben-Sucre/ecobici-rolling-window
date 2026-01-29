from __future__ import annotations

from pathlib import Path
from typing import Iterator

import polars as pl
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
def sample_raw_df() -> pl.DataFrame:
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
