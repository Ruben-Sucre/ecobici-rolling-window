# analysis.py
import polars as pl
from .utils.paths import get_data_dir

class EcobiciEngine:
    def __init__(self, data_dir=None):
        self.base_dir = get_data_dir(data_dir)
        self.pattern = str(self.base_dir / "ecobici_*.parquet")

    def get_base_query(self) -> pl.LazyFrame:
        """Crea la consulta base con las transformaciones iniciales."""
        if not self.base_dir.exists():
            raise FileNotFoundError(f"No se encontró: {self.base_dir}")
            
        return pl.scan_parquet(self.pattern).with_columns([
            ((pl.col("fecha_hora_arribo") - pl.col("fecha_hora_retiro")).dt.total_minutes()).alias("duracion_minutos"),
            pl.col("fecha_hora_retiro").dt.strftime("%Y-%m").alias("mes_anio")
        ]).filter(
            (pl.col("duracion_minutos") > 1) & (pl.col("duracion_minutos") < 180)
        )

    def run_full_analysis(self, filters: dict | None = None):
        """Procesa todo y devuelve un diccionario con resultados listos para usar."""
        lf = self.get_base_query()
        
        # Aplicar filtros si existen (puedes expandir esto)
        if filters:
            if "edades" in filters:
                lf = lf.filter(pl.col("edad").is_between(filters["edades"][0], filters["edades"][1]))
        
        # Ejecutar cálculos (Collect)
        resumen = lf.select([
            pl.len().alias("total_viajes"),
            pl.col("duracion_minutos").mean().alias("promedio_minutos"),
            pl.col("edad").median().alias("mediana_edad")
        ]).collect().to_dicts()[0]

        viajes_mes = lf.group_by("mes_anio").agg(pl.len().alias("viajes")).sort("mes_anio").collect()
        
        return {
            "metrics": resumen,
            "viajes_por_mes": viajes_mes,
            "base_data": lf # Devolvemos el LazyFrame por si la UI necesita más filtros
        }


# Función wrapper para mantener compatibilidad con código anterior
def generar_reporte_mensual(data_dir=None) -> str:
    """
    Wrapper de compatibilidad que genera un reporte en formato texto.
    Por dentro usa la clase EcobiciEngine.
    """
    engine = EcobiciEngine(data_dir)
    results = engine.run_full_analysis()
    
    metrics = results["metrics"]
    viajes_mes = results["viajes_por_mes"]
    
    # Formatear el reporte de texto
    reporte = []
    reporte.append("=" * 60)
    reporte.append("REPORTE AUTOMÁTICO ECOBICI")
    reporte.append("=" * 60)
    reporte.append("")
    reporte.append("📊 RESUMEN GENERAL")
    reporte.append("-" * 60)
    reporte.append(f"Total de viajes: {metrics['total_viajes']:,}")
    reporte.append(f"Promedio de duración: {metrics['promedio_minutos']:.2f} minutos")
    reporte.append(f"Mediana de edad: {metrics['mediana_edad']:.0f} años")
    reporte.append("")
    reporte.append("📅 VIAJES POR MES")
    reporte.append("-" * 60)
    
    for row in viajes_mes.iter_rows(named=True):
        reporte.append(f"{row['mes_anio']}: {row['viajes']:,} viajes")
    
    reporte.append("")
    reporte.append("=" * 60)
    
    return "\n".join(reporte)