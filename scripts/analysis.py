from __future__ import annotations

from pathlib import Path

import polars as pl

from .utils.paths import get_data_dir


def generar_reporte_mensual(data_dir: Path | str | None = None) -> str:
    base_dir = get_data_dir(data_dir)
    pattern = base_dir / "ecobici_*.parquet"
    
    try:
        # Verificamos si la carpeta existe
        if not base_dir.exists():
            return f"Error: La carpeta de datos no existe en: {base_dir.resolve()}"

        # 2. Cargar archivos (LazyFrame)
        # scan_parquet acepta el objeto Path convertido a string para el glob
        query = pl.scan_parquet(str(pattern))
        
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
        --- REPORTE AUTOMÁTICO ECOBICI (Pathlib version) ---
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