import requests
from bs4 import BeautifulSoup
import os
import re
from pathlib import Path
from urllib.parse import urljoin # Importación recomendada para unir URLs

# def obtener_ultimo_mes_local(data_path="data/"): #primera version 
def obtener_ultimo_mes_local(data_path="/home/ruben/ecobici-project/data/"): #Dirección corregida
    """Revisa los archivos parquet existentes y devuelve el último (YYYY-MM)."""
    # Se asume que el usuario guarda datos en 'data/'
    archivos = sorted(list(Path(data_path).glob("ecobici_*.parquet")))
    if not archivos:
        return None
    match = re.search(r"(\d{4}-\d{2})", archivos[-1].name)
    return match.group(1) if match else None

def buscar_y_descargar_nuevo_csv():
    url_base = "https://ecobici.cdmx.gob.mx/datos-abiertos/"
    dominio = "https://ecobici.cdmx.gob.mx" # Dominio necesario para completar rutas
    ultimo_local = obtener_ultimo_mes_local()
    print(f"Último mes en base de datos: {ultimo_local}")

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
            # CORRECCIÓN: Si la URL es relativa, le pegamos el dominio
            if href.startswith('/'):
                href = urljoin(dominio, href)
            
            m = re.search(r"(\d{4}-\d{2})", href)
            if m:
                enlaces_validos.append((m.group(1), href))
        
        enlaces_validos.sort(reverse=True)
        mes_web, url_descarga = enlaces_validos[0]

        print(f"Mes más reciente en la web: {mes_web}")

        if ultimo_local and mes_web <= ultimo_local:
            print(f"✅ El sistema ya está actualizado. No hay archivos nuevos por procesar.")
            return None

        print(f"🆕 ¡Nuevo archivo detectado! Descargando {mes_web}...")
        print(f"🔗 URL de descarga: {url_descarga}") # Para depuración
        
        r_file = requests.get(url_descarga, stream=True)
        r_file.raise_for_status() # Verifica que la descarga sea exitosa
        
        # nombre_csv = f"{mes_web}.csv" # Versión anterior
        nombre_csv = f"/home/ruben/ecobici-project/data/{mes_web}.csv" # Guardar en carpeta data versión corregida        
        with open(nombre_csv, 'wb') as f:
            for chunk in r_file.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"💾 Archivo guardado como: {nombre_csv}")
        return nombre_csv

    except Exception as e:
        print(f"❌ Error durante la búsqueda/descarga: {e}")
        return None

if __name__ == "__main__":
    buscar_y_descargar_nuevo_csv()