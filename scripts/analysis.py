# analysis.py
import polars as pl
from .utils.paths import get_data_dir


class EcobiciEngine:
    """Motor de análisis optimizado para consultas dinámicas con Polars LazyFrames."""
    
    def __init__(self, data_dir=None):
        self.base_dir = get_data_dir(data_dir)
        self.pattern = str(self.base_dir / "ecobici_*.parquet")
        self._raw_lf = None  # Cache interno del LazyFrame base

    def _get_raw_lazyframe(self) -> pl.LazyFrame:
        """Carga el LazyFrame base con transformaciones mínimas (solo una vez)."""
        if self._raw_lf is None:
            if not self.base_dir.exists():
                raise FileNotFoundError(f"No se encontró: {self.base_dir}")
            
            # Usar cast_options para manejar inconsistencias Categorical/String
            cast_opts = pl.ScanCastOptions(categorical_to_string='allow')
            
            # IMPORTANTE: allow_missing_columns para archivos con esquemas inconsistentes
            lf = pl.scan_parquet(
                self.pattern, 
                cast_options=cast_opts,
                missing_columns="insert"
            )

            schema = lf.collect_schema()
            fecha_origen_expr = (
                pl.col("fecha_origen")
                if "fecha_origen" in schema
                else pl.col("fecha_hora_retiro")
                if "fecha_hora_retiro" in schema
                else pl.lit(None)
            )
            fecha_destino_expr = (
                pl.col("fecha_destino")
                if "fecha_destino" in schema
                else pl.col("fecha_hora_arribo")
                if "fecha_hora_arribo" in schema
                else pl.lit(None)
            )
            genero_expr = pl.col("genero") if "genero" in schema else pl.lit(None)

            lf = lf.with_columns([
                # Compatibilidad con esquemas antiguos
                fecha_origen_expr.alias("fecha_origen"),
                fecha_destino_expr.alias("fecha_destino"),
                pl.when(genero_expr.is_in(["H", "M", "-"]))
                .then(
                    pl.when(genero_expr == "H").then(pl.lit("M"))
                    .when(genero_expr == "M").then(pl.lit("F"))
                    .otherwise(pl.lit("O"))
                )
                .otherwise(genero_expr)
                .alias("genero"),
            ])

            self._raw_lf = lf.with_columns([
                # Duración del viaje
                ((pl.col("fecha_destino") - pl.col("fecha_origen"))
                 .dt.total_minutes()).alias("duracion_minutos"),
                
                # Extraer componentes temporales
                pl.col("fecha_origen").dt.strftime("%Y-%m").alias("mes_anio"),
                pl.col("fecha_origen").dt.year().alias("anio"),
                pl.col("fecha_origen").dt.hour().alias("hora_retiro"),
                
                # Identificar viajes fallidos (< 1 min indica problemas con la bici)
                (pl.col("fecha_destino") - pl.col("fecha_origen"))
                .dt.total_minutes().lt(1).alias("es_viaje_fallido")
            ])
        
        return self._raw_lf

    def get_filtered_query(self, filters: dict | None = None) -> pl.LazyFrame:
        """
        Aplica filtros dinámicos al LazyFrame base.
        
        Filtros soportados:
        - anios: list[int] - Años a incluir
        - generos: list[str] - Géneros ('F', 'M', 'O')
        - estaciones_origen: list[int] - IDs de estaciones de origen
        - rango_edad: tuple[int, int] - (edad_min, edad_max)
        - duracion_min: float - Duración mínima en minutos
        - duracion_max: float - Duración máxima en minutos
        """
        lf = self._get_raw_lazyframe()
        
        if not filters:
            # Filtro por defecto: viajes válidos (> 1 min y < 3 horas)
            return lf.filter(
                (pl.col("duracion_minutos") > 1) & 
                (pl.col("duracion_minutos") < 180)
            )
        
        # Aplicar filtros dinámicamente
        conditions = []
        
        # Filtro de años
        if "anios" in filters and filters["anios"]:
            conditions.append(pl.col("anio").is_in(filters["anios"]))
        
        # Filtro de género
        if "generos" in filters and filters["generos"]:
            conditions.append(pl.col("genero").is_in(filters["generos"]))
        
        # Filtro de estaciones de origen
        if "estaciones_origen" in filters and filters["estaciones_origen"]:
            conditions.append(pl.col("estacion_origen_id").is_in(filters["estaciones_origen"]))
        
        # Rango de edad
        if "rango_edad" in filters:
            edad_min, edad_max = filters["rango_edad"]
            conditions.append(pl.col("edad").is_between(edad_min, edad_max))
        
        # Duración (con valores por defecto para viajes válidos)
        duracion_min = filters.get("duracion_min", 1)
        duracion_max = filters.get("duracion_max", 180)
        conditions.append(
            (pl.col("duracion_minutos") > duracion_min) & 
            (pl.col("duracion_minutos") < duracion_max)
        )
        
        # Combinar todas las condiciones con AND
        if conditions:
            combined_filter = conditions[0]
            for condition in conditions[1:]:
                combined_filter = combined_filter & condition
            lf = lf.filter(combined_filter)
        
        return lf

    def get_metadata(self) -> dict:
        """Obtiene metadata para poblar los filtros de la UI (sin collect pesado)."""
        lf = self._get_raw_lazyframe()
        
        # Queries ligeras para obtener valores únicos
        metadata = {}
        
        # Años disponibles
        anios_df = lf.select(pl.col("anio").unique()).collect()
        metadata["anios_disponibles"] = sorted(anios_df["anio"].to_list())
        
        # Géneros disponibles
        generos_df = lf.select(pl.col("genero").unique()).collect()
        metadata["generos_disponibles"] = sorted(
            [g for g in generos_df["genero"].to_list() if g is not None]
        )
        
        # Rango de edades (min/max para el slider)
        edad_stats = lf.select([
            pl.col("edad").min().alias("edad_min"),
            pl.col("edad").max().alias("edad_max")
        ]).collect()
        metadata["edad_min"] = int(edad_stats["edad_min"][0])
        metadata["edad_max"] = int(edad_stats["edad_max"][0])
        
        return metadata

    def run_full_analysis(self, filters: dict | None = None) -> dict:
        """
        Análisis completo con métricas principales y secundarias.
        OPTIMIZADO: Usa UN SOLO .collect() para todas las agregaciones.
        """
        lf = self.get_filtered_query(filters)

        metrics_lf = lf.select([
            pl.len().alias("total_viajes"),
            pl.col("duracion_minutos").mean().alias("promedio_minutos"),
            pl.col("edad").median().alias("mediana_edad"),
            pl.col("es_viaje_fallido").sum().alias("viajes_fallidos"),
        ]).with_columns(pl.lit(1).alias("_join_key"))

        viajes_mes_lf = (
            lf.group_by("mes_anio")
            .agg(pl.len().alias("viajes"))
            .sort("mes_anio")
            .with_columns(
                pl.col("viajes").rolling_mean(window_size=3).alias("viajes_rolling_3m")
            )
        )
        viajes_mes_list_lf = (
            viajes_mes_lf.with_columns(pl.lit(1).alias("_join_key"))
            .group_by("_join_key")
            .agg(pl.struct(["mes_anio", "viajes", "viajes_rolling_3m"]).alias("viajes_por_mes"))
        )

        horas_pico_list_lf = (
            lf.group_by("hora_retiro")
            .agg(pl.len().alias("viajes"))
            .sort("hora_retiro")
            .with_columns(pl.lit(1).alias("_join_key"))
            .group_by("_join_key")
            .agg(pl.struct(["hora_retiro", "viajes"]).alias("horas_pico"))
        )

        top_estaciones_origen_list_lf = (
            lf.group_by("estacion_origen_id")
            .agg(pl.len().alias("viajes"))
            .sort("viajes", descending=True)
            .head(10)
            .with_columns(pl.lit(1).alias("_join_key"))
            .group_by("_join_key")
            .agg(pl.struct(["estacion_origen_id", "viajes"]).alias("top_estaciones_origen"))
        )

        top_estaciones_destino_list_lf = (
            lf.group_by("estacion_destino_id")
            .agg(pl.len().alias("viajes"))
            .sort("viajes", descending=True)
            .head(10)
            .with_columns(pl.lit(1).alias("_join_key"))
            .group_by("_join_key")
            .agg(pl.struct(["estacion_destino_id", "viajes"]).alias("top_estaciones_destino"))
        )

        distribucion_genero_list_lf = (
            lf.filter(pl.col("genero").is_in(["F", "M", "O"]))
            .group_by("genero")
            .agg(pl.len().alias("viajes"))
            .with_columns(pl.lit(1).alias("_join_key"))
            .group_by("_join_key")
            .agg(pl.struct(["genero", "viajes"]).alias("distribucion_genero"))
        )

        result_lf = (
            metrics_lf
            .join(viajes_mes_list_lf, on="_join_key", how="left")
            .join(horas_pico_list_lf, on="_join_key", how="left")
            .join(top_estaciones_origen_list_lf, on="_join_key", how="left")
            .join(top_estaciones_destino_list_lf, on="_join_key", how="left")
            .join(distribucion_genero_list_lf, on="_join_key", how="left")
            .drop("_join_key")
        )

        result_df = result_lf.collect()

        def _list_struct_to_df(value: list[dict] | None) -> pl.DataFrame:
            if not value:
                return pl.DataFrame()
            return pl.DataFrame(value)

        row = result_df.row(0, named=True)
        metrics = {
            "total_viajes": int(row["total_viajes"] or 0),
            "promedio_minutos": row["promedio_minutos"] or 0.0,
            "mediana_edad": row["mediana_edad"] or 0.0,
            "viajes_fallidos": int(row["viajes_fallidos"] or 0),
        }
        total_viajes = metrics["total_viajes"]
        metrics["porcentaje_viajes_fallidos"] = (
            (metrics["viajes_fallidos"] / total_viajes) * 100
            if total_viajes > 0
            else 0.0
        )

        return {
            "metrics": metrics,
            "viajes_por_mes": _list_struct_to_df(row.get("viajes_por_mes")),
            "horas_pico": _list_struct_to_df(row.get("horas_pico")),
            "viajes_por_hora": _list_struct_to_df(row.get("horas_pico")),
            "top_estaciones_origen": _list_struct_to_df(row.get("top_estaciones_origen")),
            "top_estaciones_destino": _list_struct_to_df(row.get("top_estaciones_destino")),
            "distribucion_genero": _list_struct_to_df(row.get("distribucion_genero")),
        }

    def get_filtered_data(
        self,
        filters: dict | None = None,
        columns: list[str] | None = None,
        limit: int | None = 10000,
    ) -> pl.DataFrame:
        """
        Devuelve datos filtrados listos para exportación.

        - columns: lista opcional de columnas a incluir
        - limit: máximo de filas a retornar (None para sin límite)
        """
        lf = self.get_filtered_query(filters)

        if columns:
            schema_cols = set(lf.collect_schema().names())
            selected = [c for c in columns if c in schema_cols]
            if not selected:
                raise ValueError("Ninguna columna solicitada existe en el dataset")
            lf = lf.select(selected)

        if limit is not None:
            lf = lf.limit(limit)

        return lf.collect()


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
    reporte.append("Viajes por mes")

    if len(viajes_mes) > 0:
        periodo_inicio = viajes_mes["mes_anio"].min()
        periodo_fin = viajes_mes["mes_anio"].max()
        reporte.append(f"Periodo analizado: {periodo_inicio} a {periodo_fin}")
    
    for row in viajes_mes.iter_rows(named=True):
        reporte.append(f"{row['mes_anio']}: {row['viajes']:,} viajes")
    
    reporte.append("")
    reporte.append("=" * 60)
    
    return "\n".join(reporte)