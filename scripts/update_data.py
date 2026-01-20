import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from urllib.parse import urljoin

# Configuración de rutas relativas (Portabilidad)
# __file__ es la ubicación de este script (scripts/update_data.py)
# .parent.parent sube dos niveles para llegar a la raíz del proyecto (ecobici-project/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def verificar_existencia_local(mes_web):
    """
    Verifica si el mes ya existe en la carpeta data, ya sea como
    CSV original o como Parquet ya procesado.
    """
    archivo_csv = DATA_DIR / f"{mes_web}.csv"
    archivo_parquet = DATA_DIR / f"ecobici_{mes_web}.parquet"
    
    return archivo_csv.exists() or archivo_parquet.exists()

def obtener_ultimo_mes_registrado():
    """Revisa los archivos parquet existentes y devuelve el nombre del último mes."""
    archivos = sorted(list(DATA_DIR.glob("ecobici_*.parquet")))
    if not archivos:
        return None
    match = re.search(r"(\d{4}-\d{2})", archivos[-1].name)
    return match.group(1) if match else None

def buscar_y_descargar_nuevo_csv():
    url_base = "https://ecobici.cdmx.gob.mx/datos-abiertos/"
    dominio = "https://ecobici.cdmx.gob.mx"
    
    # Asegurar que la carpeta data exista
    DATA_DIR.mkdir(parents=True, exist_ok=True)

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
        
        # Ordenar por fecha descendente
        enlaces_validos.sort(reverse=True)
        mes_web, url_descarga = enlaces_validos[0]

        print(f"Mes más reciente en la web: {mes_web}")

        # NUEVA LÓGICA DE VERIFICACIÓN
        if verificar_existencia_local(mes_web):
            print(f"✅ El mes {mes_web} ya existe localmente (en .csv o .parquet).")
            return None

        print(f"🆕 ¡Nuevo archivo detectado! Descargando {mes_web}...")
        
        r_file = requests.get(url_descarga, stream=True)
        r_file.raise_for_status()
        
        ruta_guardado = DATA_DIR / f"{mes_web}.csv"
        
        with open(ruta_guardado, 'wb') as f:
            for chunk in r_file.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"💾 Archivo guardado en: {ruta_guardado}")
        return str(ruta_guardado)

    except Exception as e:
        print(f"❌ Error durante la búsqueda/descarga: {e}")
        return None

if __name__ == "__main__":
    buscar_y_descargar_nuevo_csv()