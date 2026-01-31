from __future__ import annotations

# Package-level exports for the scripts module. Avoid importing submodules at package import time
# to prevent heavy dependencies (like polars) from being imported during test collection.

__all__ = [
    "analysis",
    "process_data",
    "quality_check",
    "update_data",
]
