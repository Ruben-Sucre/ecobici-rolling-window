from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from .utils.paths import get_data_dir


def obtener_csv_pendientes(data_dir: Path | str | None = None) -> list[Path]:
    target_dir = get_data_dir(data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    csvs = list(target_dir.glob("*.csv"))
    pendientes = []
    for archivo_csv in csvs:
        match = re.search(r"(\d{4}-\d{2})", archivo_csv.name)
        if match:
            mes = match.group(1)
            archivo_parquet = target_dir / f"ecobici_{mes}.parquet"
            if not archivo_parquet.exists():
                pendientes.append(archivo_csv)
    pendientes.sort()
    return pendientes

def procesar_csv_a_parquet(ruta_csv: Path | str, data_dir: Path | str | None = None) -> bool:
    target_dir = get_data_dir(data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    ruta_csv = Path(ruta_csv)
    match = re.search(r"(\d{4}-\d{2})", ruta_csv.name)
    if not match:
        raise ValueError(f"El nombre del archivo {ruta_csv.name} no contiene un patrón de fecha YYYY-MM")
    mes = match.group(1)
    ruta_salida = target_dir / f"ecobici_{mes}.parquet"
    
    print(f"⚙️ Procesando: {ruta_csv.name}...")

    try:
        df = pl.read_csv(
            ruta_csv, 
            null_values=["NULL", "null", ""], 
            infer_schema_length=10000,
            ignore_errors=False
        )

        # 💡 SOLUCIÓN: Detectar si viene con 'A' mayúscula o minúscula
        # Esto hace que el script sea más robusto
        col_arribo = "Ciclo_EstacionArribo" if "Ciclo_EstacionArribo" in df.columns else "Ciclo_Estacionarribo"

        df_limpio = df.with_columns([
            pl.col("Genero_Usuario").cast(pl.Categorical),
            pl.col("Edad_Usuario").fill_null(0).cast(pl.UInt8),
            pl.col("Ciclo_Estacion_Retiro").cast(pl.UInt16, strict=False),
            pl.col(col_arribo).cast(pl.UInt16, strict=False), # Usamos la variable detectada
            
            pl.format("{} {}", pl.col("Fecha_Retiro"), pl.col("Hora_Retiro"))
              .str.to_datetime(format="%d/%m/%Y %H:%M:%S", strict=False)
              .alias("fecha_hora_retiro"),
              
            pl.format("{} {}", pl.col("Fecha_Arribo"), pl.col("Hora_Arribo"))
              .str.to_datetime(format="%d/%m/%Y %H:%M:%S", strict=False)
              .alias("fecha_hora_arribo")
        ]).select([
            pl.col("Genero_Usuario").alias("genero"),
            pl.col("Edad_Usuario").alias("edad"),
            pl.col("Bici").alias("bici_id"),
            pl.col("Ciclo_Estacion_Retiro").alias("estacion_origen_id"),
            pl.col(col_arribo).alias("estacion_destino_id"), # Renombramos correctamente
            pl.col("fecha_hora_retiro"),
            pl.col("fecha_hora_arribo")
        ])

        df_limpio.write_parquet(ruta_salida, compression="zstd")
        print(f"✅ Convertido con éxito: {ruta_salida.name}")
        return True

    except Exception as e:
        print(f"❌ Error procesando {ruta_csv.name}: {e}")
        return False

def main():
    pendientes = obtener_csv_pendientes()
    if not pendientes:
        print("🙌 No hay archivos CSV pendientes.")
        return

    for archivo in pendientes:
        if procesar_csv_a_parquet(archivo):
            print("\n💡 El archivo Parquet es ~80% más ligero.")
            respuesta = input(f"¿Deseas borrar el original {archivo.name}? (s/n, default: s): ").lower()
            if respuesta in ['s', '', 'si', 'yes']:
                archivo.unlink()
                print(f"🗑️ Archivo {archivo.name} eliminado.")

if __name__ == "__main__":
    main()