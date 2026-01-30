from __future__ import annotations

from pathlib import Path

import pytest

from scripts import update_data


class DummyResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")


@pytest.fixture
def fake_html() -> str:
    return """
    <html>
        <body>
            <a href="/files/2024-10.csv">2024-10</a>
            <a href="https://example.com/files/2024-11.csv">2024-11</a>
        </body>
    </html>
    """


def test_buscar_descarga_crea_archivo(monkeypatch, temp_data_dir: Path, fake_html: str) -> None:
    created: dict[str, Path] = {}

    def fake_get(url: str, timeout: int) -> DummyResponse:  # noqa: D401
        return DummyResponse(fake_html)

    def fake_descarga(url: str, destino: Path) -> Path:
        destino.write_text("csv,data")
        created[url] = destino
        return destino

    monkeypatch.setattr(update_data.requests, "get", fake_get)
    monkeypatch.setattr(update_data, "descargar_con_reintento", fake_descarga)

    csv_path = update_data.buscar_y_descargar_nuevo_csv(temp_data_dir, force=True)

    assert csv_path is not None
    assert csv_path.exists()
    assert csv_path.name == "2024-11.csv"


def test_buscar_descarga_omite_mes_procesado(monkeypatch, temp_data_dir: Path, fake_html: str) -> None:
    (temp_data_dir / "ecobici_2024-11.parquet").touch()

    def fake_get(url: str, timeout: int) -> DummyResponse:
        return DummyResponse(fake_html)

    monkeypatch.setattr(update_data.requests, "get", fake_get)

    csv_path = update_data.buscar_y_descargar_nuevo_csv(temp_data_dir)

    assert csv_path is None
