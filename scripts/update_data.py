import requests
import re
from pathlib import Path
from urllib.parse import urljoin

# Configuración de rutas relativas para portabilidad
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def descargar_con_reintento(url, ruta_archivo):
    """Descarga un archivo permitiendo reanudar si la conexión se interrumpe."""
    # 1. Verificar cuánto se ha descargado ya
    modo_apertura = 'wb'
    headers = {}
    size_inicial = 0

    if ruta_archivo.exists():
        size_inicial = ruta_archivo.stat().st_size
        # Si el archivo ya existe, pedimos solo lo que falta
        headers['Range'] = f'bytes={size_inicial}-'
        modo_apertura = 'ab'
        print(f"📦 Archivo parcial detectado ({size_inicial / 1024**2:.2f} MB). Intentando reanudar...")

    try:
        # stream=True es vital para archivos grandes
        with requests.get(url, headers=headers, stream=True, timeout=20) as r:
            # Si el servidor devuelve 416, es que el archivo ya está completo
            if r.status_code == 416:
                print("✅ El archivo ya estaba completo.")
                return True
            
            r.raise_for_status()
            
            # Si el servidor no soporta Range (devuelve 200 en vez de 206), reiniciamos
            if r.status_code == 200 and size_inicial > 0:
                print("⚠️ El servidor no soporta reanudación. Reiniciando descarga...")
                modo_apertura = 'wb'

            with open(ruta_archivo, modo_apertura) as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"❌ Error durante la descarga: {e}")
        return False

def buscar_y_descargar_nuevo_csv():
    url_base = "https://ecobici.cdmx.gob.mx/datos-abiertos/"
    dominio = "https://ecobici.cdmx.gob.mx"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url_base, timeout=15)
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        enlaces = soup.find_all('a', href=re.compile(r".*\.csv$"))
        if not enlaces: return None

        enlaces_validos = []
        for e in enlaces:
            href = e['href']
            if href.startswith('/'): href = urljoin(dominio, href)
            m = re.search(r"(\d{4}-\d{2})", href)
            if m: enlaces_validos.append((m.group(1), href))
        
        enlaces_validos.sort(reverse=True)
        mes_web, url_descarga = enlaces_validos[0]

        # Verificar si ya existe el .parquet (para no descargar de nuevo)
        if (DATA_DIR / f"ecobici_{mes_web}.parquet").exists():
            print(f"✅ El mes {mes_web} ya ha sido procesado a Parquet.")
            return None

        ruta_csv = DATA_DIR / f"{mes_web}.csv"
        
        exito = descargar_con_reintento(url_descarga, ruta_csv)
        
        if exito:
            print(f"💾 Descarga finalizada: {ruta_csv}")
            return str(ruta_csv)
        return None

    except Exception as e:
        print(f"❌ Error general: {e}")
        return None

if __name__ == "__main__":
    buscar_y_descargar_nuevo_csv()