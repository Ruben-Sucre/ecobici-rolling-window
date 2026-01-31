from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

import logging
import requests
from bs4 import BeautifulSoup

from .utils.paths import get_data_dir
from .utils.exceptions import DownloadError

logger = logging.getLogger(__name__)


def descargar_con_reintento(url: str, ruta_archivo: Path, timeout: tuple = (5, 15)) -> None:
    """Descarga un recurso con reintentos, streaming y timeouts.

    Lanza DownloadError en caso de fallo.
    """
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])  # type: ignore[arg-type]
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        with session.get(url, timeout=timeout, stream=True) as r:
            r.raise_for_status()
            ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
            with ruta_archivo.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error descargando %s: %s", url, e)
        raise DownloadError("HTTP error") from e
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.warning("Error de conexión/timeout descargando %s: %s", url, e)
        raise DownloadError("Connection/Timeout") from e
    except requests.exceptions.RequestException as e:
        logger.exception("Error en request al descargar %s", url)
        raise DownloadError("Request failed") from e


def buscar_y_descargar_nuevo_csv(
    data_dir: Path | str | None = None,
    *,
    force: bool = False,
) -> Path | None:
    """Busca el CSV más reciente en el portal y lo descarga si no existe."""
    url_base = "https://ecobici.cdmx.gob.mx/datos-abiertos/"
    dominio = "https://ecobici.cdmx.gob.mx"
    target_dir = get_data_dir(data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url_base, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        enlaces = soup.find_all("a", href=re.compile(r".*\.csv$"))
        if not enlaces:
            logger.warning("No se encontraron enlaces CSV en la página: %s", url_base)
            return None

        enlaces_validos: list[tuple[str, str]] = []
        for enlace in enlaces:
            href = enlace["href"]
            if href.startswith("/"):
                href = urljoin(dominio, href)
            match = re.search(r"(\d{4}-\d{2})", href)
            if match:
                enlaces_validos.append((match.group(1), href))

        if not enlaces_validos:
            logger.warning("No se encontraron enlaces CSV con formato YYYY-MM en: %s", url_base)
            return None

        enlaces_validos.sort(reverse=True)
        mes_web, url_descarga = enlaces_validos[0]

        ruta_csv = target_dir / f"{mes_web}.csv"
        archivo_parquet = target_dir / f"ecobici_{mes_web}.parquet"

        if archivo_parquet.exists() and not force:
            logger.info("Mes %s ya procesado (%s).", mes_web, archivo_parquet.name)
            return None

        logger.info("Descargando datos de %s desde %s...", mes_web, url_descarga)
        try:
            descargar_con_reintento(url_descarga, ruta_csv)
        except DownloadError as exc:  # pragma: no cover - network error path
            logger.error("Fallo descargando %s: %s", url_descarga, exc)
            return None
        return ruta_csv if ruta_csv.exists() else None

    except Exception as exc:  # pragma: no cover - logging path
        logger.exception("Error en Step 1: %s", exc)
        return None