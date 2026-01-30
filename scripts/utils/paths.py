from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"


@lru_cache(maxsize=None)
def get_data_dir(base: Path | str | None = None) -> Path:
    """Return the data directory honoring an explicit base, env var, or default."""
    if base is not None:
        return Path(base)

    env_override = os.getenv("ECOBICI_DATA_DIR")
    if env_override:
        return Path(env_override)

    return _DEFAULT_DATA_DIR
