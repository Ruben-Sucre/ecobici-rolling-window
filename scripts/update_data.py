import requests
from bs4 import BeautifulSoup
import os
import re
from pathlib import Path
from urllib.parse import urljoin

# --- CONFIGURACIÓN DE RUTAS DINÁMICAS ---
# __file__ es la ruta de este script (scripts/update_data.py)
# .parent es la carpeta 'scripts/', .parent.parent es la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def obtener_ultimo_mes_local(data_path=DATA_DIR):
    """Revisa los archivos parquet existentes en la ruta relativa y devuelve el último."""
    # Aseguramos que la carpeta exista para evitar errores
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
        
    archivos = sorted(list(data_path.glob("ecobici_*.parquet")))
    if not archivos:
        return None
    match = re.search(r"(\d{4}-\d{2})", archivos[-1].name)
    return match.group(1) if match else None

def buscar_y_descargar_nuevo_csv():
    url_base = "https://ecobici.cdmx.gob.mx/datos-abiertos/"
    dominio = "https://ecobici.cdmx.gob.mx"
    ultimo_local = obtener_ultimo_mes_local()
    print(f"Último mes en base de datos local: {ultimo_local}")

    try:
        response = requests.get(url_base, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        enlaces = soup.find_all('a', href=re.compile(r".*\.csv$"))
        
        if not enlaces:
            print("No se encontraron enlaces a archivos CSV.")
            return None

        enlaces_validos = []
        for e in enlaces:
            href = e['href']
            if href.startswith('/'):
                href = urljoin(dominio, href)
            
            m = re.search(r"(\d{4}-\d{2})", href)
            if m:
                enlaces_validos.append((m.group(1), href))
        
        enlaces_validos.sort(reverse=True)
        mes_web, url_descarga = enlaces_validos[0]

        print(f"Mes más reciente en la web: {mes_web}")

        if ultimo_local and mes_web <= ultimo_local:
            print(f"✅ El sistema ya está actualizado.")
            return None

        print(f"🆕 ¡Nuevo archivo detectado! Descargando {mes_web}...")
        
        r_file = requests.get(url_descarga, stream=True)
        r_file.raise_for_status()
        
        # Guardar usando la ruta dinámica
        nombre_csv = DATA_DIR / f"{mes_web}.csv"
        
        with open(nombre_csv, 'wb') as f:
            for chunk in r_file.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"💾 Archivo guardado como: {nombre_csv}")
        return str(nombre_csv)

    except Exception as e:
        print(f"❌ Error durante la búsqueda/descarga: {e}")
        return None

if __name__ == "__main__":
    buscar_y_descargar_nuevo_csv()