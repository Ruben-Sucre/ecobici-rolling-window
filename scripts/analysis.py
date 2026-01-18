import polars as pl
import os

def generar_reporte_mensual():
    # 1. Obtener la ruta absoluta de la carpeta del proyecto
    # __file__ es la ruta al script actual (scripts/analysis.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Subimos un nivel para llegar a la raíz del proyecto y luego entramos a 'data'
    data_path = os.path.join(script_dir, "..", "data")
    
    # Definimos el patrón de búsqueda de archivos
    pattern = os.path.join(data_path, "ecobici_*.parquet")
    
    try:
        # Verificamos si la carpeta existe para dar un error más claro
        if not os.path.exists(data_path):
            return f"Error: La carpeta de datos no existe en: {os.path.abspath(data_path)}"

        # 2. Cargar archivos (LazyFrame)
        query = pl.scan_parquet(pattern)
        
        # Transformaciones
        df = query.with_columns([
            ((pl.col("fecha_hora_arribo") - pl.col("fecha_hora_retiro")).dt.total_minutes()).alias("duracion_minutos"),
            pl.col("fecha_hora_retiro").dt.strftime("%Y-%m").alias("mes_anio")
        ]).filter(
            (pl.col("duracion_minutos") > 1) & (pl.col("duracion_minutos") < 180)
        )

        # 3. Ejecutar Cálculos
        resumen_general = df.select([
            pl.len().alias("total_viajes"),
            pl.col("duracion_minutos").mean().alias("promedio_minutos"),
            pl.col("edad").median().alias("mediana_edad")
        ]).collect()

        viajes_por_mes = df.group_by("mes_anio").agg(
            pl.len().alias("viajes")
        ).sort("mes_anio").collect()

        top_estaciones = df.group_by("estacion_origen_id").agg(
            pl.len().alias("conteo")
        ).sort("conteo", descending=True).head(5).collect()

        # 4. Formatear el Reporte
        reporte = f"""
        --- REPORTE AUTOMÁTICO ECOBICI ---
        Periodo analizado: {viajes_por_mes['mes_anio'][0]} a {viajes_por_mes['mes_anio'][-1]}
        Total de viajes: {resumen_general['total_viajes'][0]:,}
        Duración promedio: {resumen_general['promedio_minutos'][0]:.2f} min
        Mediana de edad: {resumen_general['mediana_edad'][0]} años

        Viajes por mes:
        {viajes_por_mes}

        Top 5 Estaciones (ID):
        {top_estaciones}
        """
        return reporte

    except Exception as e:
        return f"Error procesando los datos: {e}\nPatrón buscado: {pattern}"

if __name__ == "__main__":
    print(generar_reporte_mensual())