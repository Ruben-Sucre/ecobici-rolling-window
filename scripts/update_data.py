import requests
import re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def descargar_con_reintento(url, ruta_archivo):
    # ... (tu código de descarga existente)
    pass

def buscar_y_descargar_nuevo_csv():
    """Busca el CSV más reciente en el portal y lo descarga si no existe."""
    url_base = "https://ecobici.cdmx.gob.mx/datos-abiertos/"
    dominio = "https://ecobici.cdmx.gob.mx"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url_base, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        enlaces = soup.find_all('a', href=re.compile(r".*\.csv$"))
        if not enlaces: 
            print("❌ No se encontraron enlaces CSV.")
            return None

        enlaces_validos = []
        for e in enlaces:
            href = e['href']
            if href.startswith('/'): href = urljoin(dominio, href)
            m = re.search(r"(\d{4}-\d{2})", href)
            if m: enlaces_validos.append((m.group(1), href))
        
        enlaces_validos.sort(reverse=True) # El más reciente primero
        mes_web, url_descarga = enlaces_validos[0]

        ruta_csv = DATA_DIR / f"{mes_web}.csv"
        archivo_parquet = DATA_DIR / f"ecobici_{mes_web}.parquet"

        if archivo_parquet.exists():
            print(f"✅ El mes {mes_web} ya está procesado.")
            return None

        print(f"📡 Descargando datos de {mes_web}...")
        # Aquí llamas a tu función de descarga
        # exito = descargar_con_reintento(url_descarga, ruta_csv)
        return ruta_csv if ruta_csv.exists() else None

    except Exception as e:
        print(f"❌ Error en Step 1: {e}")
        return None