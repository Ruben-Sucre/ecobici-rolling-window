import streamlit as st
import plotly.express as px

try:
    from .analysis import EcobiciEngine
except ImportError:  # Ejecución directa con streamlit
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from scripts.analysis import EcobiciEngine

st.set_page_config(
    page_title="Dashboard Ecobici CDMX", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# FUNCIONES DE CACHÉ OPTIMIZADAS
# ============================================================================

@st.cache_resource
def init_engine():
    """Inicializa el motor (LazyFrame interno cacheado en memoria)."""
    return EcobiciEngine()

@st.cache_data(ttl=3600)
def cargar_metadata(_engine):
    """Carga metadata para filtros (se ejecuta una sola vez por hora)."""
    return _engine.get_metadata()

@st.cache_data(ttl=600)
def ejecutar_analisis(_engine, filtros_tuple):
    """
    Ejecuta el análisis con filtros.
    Usa tuple para filtros porque st.cache_data necesita tipos hashables.
    """
    # Convertir tuple de vuelta a dict
    filtros_dict = dict(filtros_tuple) if filtros_tuple else None
    return _engine.run_full_analysis(filtros_dict)


# ============================================================================
# SECCIÓN: MÉTRICAS PRINCIPALES
# ============================================================================

def render_metricas_principales(metrics):
    """Renderiza las 4 métricas principales en tarjetas."""
    st.subheader("📊 Métricas Clave")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Viajes",
            f"{metrics['total_viajes']:,}",
            help="Número total de viajes en el período seleccionado"
        )
    
    with col2:
        st.metric(
            "Duración Promedio",
            f"{metrics['promedio_minutos']:.1f} min",
            help="Duración promedio de los viajes"
        )
    
    with col3:
        mediana_edad = metrics.get('mediana_edad')
        val_edad = f"{int(mediana_edad)} años" if mediana_edad else "N/A"
        st.metric(
            "Edad Mediana",
            val_edad,
            help="Edad mediana de los usuarios"
        )
    
    with col4:
        viajes_fallidos = metrics.get('viajes_fallidos', 0)
        porcentaje_fallidos = (viajes_fallidos / metrics['total_viajes'] * 100) if metrics['total_viajes'] > 0 else 0
        st.metric(
            "Viajes Fallidos",
            f"{viajes_fallidos:,}",
            delta=f"{porcentaje_fallidos:.2f}%",
            delta_color="inverse",
            help="Viajes < 1 min (posibles bicis defectuosas)"
        )


# ============================================================================
# SECCIÓN: GRÁFICOS PRINCIPALES
# ============================================================================

def render_graficos_principales(results):
    """Renderiza los gráficos de tendencia temporal y horas pico."""
    
    # FILA 1: Tendencia temporal + Horas pico
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Tendencia de Uso")
        df_mes = results["viajes_por_mes"].to_dict(as_series=False)
        fig_tendencia = px.line(
            df_mes,
            x="mes_anio",
            y="viajes",
            markers=True,
            title="Viajes por Mes"
        )
        fig_tendencia.update_traces(line_color="#FF4B4B")
        fig_tendencia.update_layout(
            xaxis_title="Mes",
            yaxis_title="Número de Viajes",
            hovermode="x unified"
        )
        st.plotly_chart(fig_tendencia, use_container_width=True)
    
    with col2:
        st.subheader("⏰ Horas Pico")
        df_horas = results["horas_pico"].to_dict(as_series=False)
        fig_horas = px.bar(
            df_horas,
            x="hora_retiro",
            y="viajes",
            title="Distribución Horaria"
        )
        fig_horas.update_traces(marker_color="#FF4B4B")
        fig_horas.update_layout(
            xaxis_title="Hora del Día",
            yaxis_title="Viajes",
            showlegend=False
        )
        st.plotly_chart(fig_horas, use_container_width=True)


# ============================================================================
# SECCIÓN: TOP ESTACIONES Y GÉNERO
# ============================================================================

def render_analisis_secundario(results):
    """Renderiza Top estaciones y distribución por género."""
    
    st.markdown("---")
    st.subheader("🚉 Análisis de Estaciones y Usuarios")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Top 10 Estaciones Origen**")
        df_origen = results["top_estaciones_origen"].to_dict(as_series=False)
        fig_origen = px.bar(
            df_origen,
            x="viajes",
            y="estacion_origen_id",
            orientation="h",
            color="viajes",
            color_continuous_scale="Reds"
        )
        fig_origen.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_origen, use_container_width=True)
    
    with col2:
        st.markdown("**Top 10 Estaciones Destino**")
        df_destino = results["top_estaciones_destino"].to_dict(as_series=False)
        fig_destino = px.bar(
            df_destino,
            x="viajes",
            y="estacion_destino_id",
            orientation="h",
            color="viajes",
            color_continuous_scale="Blues"
        )
        fig_destino.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_destino, use_container_width=True)
    
    with col3:
        st.markdown("**Distribución por Género**")
        df_genero = results["distribucion_genero"].to_dict(as_series=False)
        fig_genero = px.pie(
            df_genero,
            values="viajes",
            names="genero",
            color="genero",
            color_discrete_map={"F": "#FF4B8B", "M": "#4B8BFF", "O": "#B0B0B0"}
        )
        st.plotly_chart(fig_genero, use_container_width=True)


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def render_dashboard():
    """Función principal que orquesta todo el dashboard."""
    
    # Header
    st.title("🚲 Dashboard Ecobici Ciudad de México")
    st.markdown("Monitor en tiempo real del sistema de bicicletas públicas")
    
    # Inicializar motor (cacheado en memoria)
    engine = init_engine()
    
    # Cargar metadata (una sola vez)
    with st.spinner("Cargando metadata..."):
        try:
            metadata = cargar_metadata(engine)
        except Exception as e:
            st.error(f"❌ Error cargando metadata: {e}")
            st.stop()
    
    # Sin filtros (sidebar deshabilitado temporalmente)
    filtros_tuple = None
    
    # Ejecutar análisis con filtros (cacheado por 10 minutos)
    with st.spinner("Procesando datos..."):
        try:
            results = ejecutar_analisis(engine, filtros_tuple)
        except Exception as e:
            st.error(f"❌ Error en análisis: {e}")
            st.stop()
    
    # Renderizar secciones
    render_metricas_principales(results["metrics"])
    st.markdown("---")
    render_graficos_principales(results)
    render_analisis_secundario(results)
    
    # Footer
    st.markdown("---")
    st.caption("📊 Datos actualizados automáticamente cada hora | Powered by Polars + Streamlit")


if __name__ == "__main__":
    render_dashboard()