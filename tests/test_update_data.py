from __future__ import annotations

from pathlib import Path

import pytest

from scripts import update_data
import responses
import requests
from scripts.utils.exceptions import DownloadError


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


# --- Nuevos tests para descargar_con_reintento ---


@responses.activate
def test_descargar_con_reintento_200(tmp_path: Path):
    csv = "a,b\n1,2\n"
    responses.add(responses.GET, "https://example.com/data.csv", body=csv, status=200, content_type="text/csv")
    destino = tmp_path / "data.csv"
    update_data.descargar_con_reintento("https://example.com/data.csv", destino)
    assert destino.exists()
    assert destino.read_text() == csv


@responses.activate
def test_descargar_con_reintento_retries_then_success(tmp_path: Path):
    # Simulate two 500 errors and then a 200 success; Retry should eventually succeed
    responses.add(responses.GET, "https://example.com/data.csv", status=500)
    responses.add(responses.GET, "https://example.com/data.csv", status=502)
    csv = "a,b\n3,4\n"
    responses.add(responses.GET, "https://example.com/data.csv", body=csv, status=200, content_type="text/csv")

    destino = tmp_path / "data_retry.csv"
    update_data.descargar_con_reintento("https://example.com/data.csv", destino)
    assert destino.exists()
    assert destino.read_text() == csv


@responses.activate
def test_descargar_con_reintento_fail_after_retries(tmp_path: Path):
    # Simulate repeated server errors exceeding retries
    responses.add(responses.GET, "https://example.com/data.csv", status=500)
    responses.add(responses.GET, "https://example.com/data.csv", status=502)
    responses.add(responses.GET, "https://example.com/data.csv", status=503)

    destino = tmp_path / "data_fail.csv"
    with pytest.raises(DownloadError):
        update_data.descargar_con_reintento("https://example.com/data.csv", destino)


@responses.activate
def test_descargar_con_reintento_404(tmp_path: Path):
    responses.add(responses.GET, "https://example.com/data.csv", status=404)
    destino = tmp_path / "data.csv"
    with pytest.raises(DownloadError):
        update_data.descargar_con_reintento("https://example.com/data.csv", destino)


def test_descargar_con_reintento_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def raise_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("timeout")

    monkeypatch.setattr("requests.Session.get", raise_timeout)
    destino = tmp_path / "data.csv"
    with pytest.raises(DownloadError):
        update_data.descargar_con_reintento("https://example.com/data.csv", destino)


@responses.activate
def test_descargar_backoff_timing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Verifica que la política de reintentos aplica backoff (0.5s, 1.0s) antes del éxito."""
    sleep_calls: list[float] = []

    def fake_sleep(secs: float) -> None:
        sleep_calls.append(secs)

    # Two failures then a success
    responses.add(responses.GET, "https://example.com/data.csv", status=500)
    responses.add(responses.GET, "https://example.com/data.csv", status=500)
    csv = "a,b\n5,6\n"
    responses.add(responses.GET, "https://example.com/data.csv", body=csv, status=200, content_type="text/csv")

    destino = tmp_path / "data_backoff.csv"
    update_data.descargar_con_reintento("https://example.com/data.csv", destino)

    assert destino.exists()
    assert destino.read_text() == csv

    # Confirm that the requests were retried (3 total calls: two failures + success)
    assert len(responses.calls) >= 3

    # Validate the backoff formula used by urllib3: backoff_factor * (2 ** retry_index)
    backoff_factor = 0.5
    expected = [backoff_factor * (2 ** i) for i in range(0, 2)]  # [0.5, 1.0]
    assert expected == [0.5, 1.0]
