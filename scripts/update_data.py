from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .utils.paths import get_data_dir


def descargar_con_reintento(url: str, ruta_archivo: Path) -> None:
    """Placeholder para la lógica de descarga con reintentos."""
    # ... (tu código de descarga existente)
    pass


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
            print("❌ No se encontraron enlaces CSV.")
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
            print("❌ No se encontraron enlaces con formato YYYY-MM.")
            return None

        enlaces_validos.sort(reverse=True)
        mes_web, url_descarga = enlaces_validos[0]

        ruta_csv = target_dir / f"{mes_web}.csv"
        archivo_parquet = target_dir / f"ecobici_{mes_web}.parquet"

        if archivo_parquet.exists() and not force:
            print(f"✅ El mes {mes_web} ya está procesado.")
            return None

        print(f"📡 Descargando datos de {mes_web}...")
        descargar_con_reintento(url_descarga, ruta_csv)
        return ruta_csv if ruta_csv.exists() else None

    except Exception as exc:  # pragma: no cover - logging path
        print(f"❌ Error en Step 1: {exc}")
        return None