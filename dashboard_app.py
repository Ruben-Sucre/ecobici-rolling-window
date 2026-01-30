"""Punto de entrada para el dashboard de Streamlit."""
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar y ejecutar el dashboard
from scripts.dashboard import render_dashboard

if __name__ == "__main__":
    render_dashboard()
