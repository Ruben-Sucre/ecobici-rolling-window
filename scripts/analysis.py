import polars as pl
import glob
import os

def generar_reporte_mensual(data_path="data/"):
    # 1. Listar todos los archivos .parquet en la carpeta
    archivos = glob.glob(os.path.join(data_path, "*.parquet"))
    
    if not archivos:
        return "Error: No se encontraron archivos para analizar."

    # 2. Leer todos los archivos a la vez (Lazy para mayor eficiencia)
    # Polars permite escanear múltiples archivos y tratarlos como uno solo
    df = pl.scan_parquet(archivos)

    # 3. Lógica de limpieza rápida (basada en tus hallazgos previos)
    df_clean = df.filter(
        (pl.col("genero").is_in(["M", "F", "O"])) &  # Limpiar géneros inválidos
        (pl.col("edad") > 0) &                       # Quitar edades en cero
        (pl.col("estacion_origen_id").is_not_null()) # Quitar nulos críticos
    )

    # 4. Cálculos para el reporte
    # Vamos a calcular: Total de viajes, viajes por género y las 5 estaciones más usadas
    stats = df_clean.select([
        pl.len().alias("total_viajes"),
        pl.col("genero").value_counts(sort=True).head(3).alias("distribucion_genero"),
    ]).collect()

    top_estaciones = df_clean.group_by("estacion_origen_nombre") \
        .agg(pl.len().alias("conteo")) \
        .sort("conteo", descending=True) \
        .head(5) \
        .collect()

    # 5. Formatear el resultado como un string para el mail
    resumen = f"""
    --- REPORTE OPERATIVO ECOBICI ---
    Total de viajes en los últimos 13 meses: {stats['total_viajes'][0]:,}
    
    Distribución por Género:
    {stats['distribucion_genero'][0]}
    
    Top 5 Estaciones de Inicio:
    {top_estaciones}
    """
    return resumen

if __name__ == "__main__":
    print(generar_reporte_mensual())