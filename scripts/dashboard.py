import streamlit as st
from .analysis import EcobiciEngine

st.set_page_config(page_title="Dashboard Ecobici", layout="wide") # 1. Mejor uso de pantalla

# 2. LA MAGIA: Cacheamos la carga de datos
@st.cache_data(ttl=3600) # Se refresca cada hora automáticamente
def cargar_datos():
    engine = EcobiciEngine()
    # Aquí obtenemos el diccionario con los dataframes ya calculados (collect)
    return engine.run_full_analysis() 

def render_dashboard():
    st.title("🚲 Monitor de Rendimiento EcoBici")
    
    # Mensaje de carga elegante
    with st.spinner('Procesando millones de viajes...'):
        try:
            results = cargar_datos() # Usamos la función con caché
        except Exception as e:
            st.error(f"Error crítico cargando datos: {e}")
            st.stop()

    metrics = results["metrics"]
    
    # 3. Layout Responsivo: Usar columnas pero controlando el espacio
    # En móvil, Streamlit colapsa las columnas automáticamente, 
    # pero es bueno agruparlas en un contenedor.
    with st.container():
        st.subheader("Métricas Clave")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Viajes", f"{metrics['total_viajes']:,}")
        c2.metric("Duración Promedio", f"{metrics['promedio_minutos']:.1f} min")
        
        # Manejo de nulos (tu lógica estaba bien, solo la pulimos visualmente)
        med_edad = metrics.get('mediana_edad')
        val_edad = f"{int(med_edad)} años" if med_edad else "N/A"
        c3.metric("Edad Mediana", val_edad)

    st.markdown("---")

    # 4. Gráfica mejorada
    st.subheader("Tendencia de Uso")
    # Streamlit maneja pandas mejor para gráficos nativos, tu conversión es correcta
    df_chart = results["viajes_por_mes"].to_pandas()
    st.line_chart(df_chart, x="mes_anio", y="viajes", color="#FF4B4B") # Color Ecobici ;)

if __name__ == "__main__":
    render_dashboard()