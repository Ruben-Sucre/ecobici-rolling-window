# dashboard.py
import streamlit as st
from scripts.analysis import EcobiciEngine # Importamos tu motor

def render_dashboard():
    st.title("Dashboard Ecobici")
    
    # Inicializamos el motor
    engine = EcobiciEngine()
    
    try:
        # 1. Obtenemos datos base para los filtros (opcional)
        # 2. Llamamos al análisis (puedes pasar los estados de los sliders aquí)
        results = engine.run_full_analysis()
        
        # 3. Usamos los resultados directamente
        metrics = results["metrics"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Total viajes", f"{metrics['total_viajes']:,}")
        c2.metric("Promedio minutos", f"{metrics['promedio_minutos']:.2f}")
        
        # 4. Manejar nulos en la mediana de edad para evitar errores de tipo
        mediana_edad = metrics.get('mediana_edad')
        if mediana_edad is not None:
            c3.metric("Mediana edad", f"{int(mediana_edad)}")
        else:
            c3.metric("Mediana edad", "N/A")
        
        # 5. Graficamos
        st.line_chart(results["viajes_por_mes"].to_pandas(), x="mes_anio", y="viajes")

    except Exception as e:
        st.error(f"Error en el motor de análisis: {e}")

if __name__ == "__main__":
    render_dashboard()