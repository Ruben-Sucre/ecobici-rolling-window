# Ecobici Data Pipeline 🚲🇲🇽

Este proyecto es un pipeline de datos automatizado diseñado para extraer, procesar y analizar la información de **Ecobici Ciudad de México**. 
El objetivo es transformar los archivos CSV masivos del portal de Datos Abiertos en un formato optimizado (Parquet) para generar reportes estadísticos 
mensuales de forma eficiente.

---

## 🔥 Rama Actual: `feature/refactor-engine`

### Objetivos de esta rama:
1. **Mejorar el dashboard** - Refactorizar la arquitectura de análisis con la clase `EcobiciEngine` para soportar visualizaciones interactivas con Streamlit
2. **Desplegar en aplicación web** - Preparar el dashboard para ser desplegado como aplicación web accesible públicamente

### Cambios implementados:
- ✅ Refactorización de `analysis.py` con arquitectura orientada a objetos
- ✅ Creación de `dashboard.py` con interfaz interactiva Streamlit
- ✅ Mantener compatibilidad hacia atrás con función wrapper
- ✅ Integración de Plotly para gráficos interactivos
- 🚧 Mejoras adicionales del dashboard (en progreso)
- 🚧 Configuración de despliegue web (pendiente)

---

## 🚀 Características

- **Web Scraping:** Localiza y descarga automáticamente el dataset más reciente del portal oficial.
- **Procesamiento con Polars:** ETL de alta velocidad que convierte archivos CSV a Parquet, reduciendo el peso de los datos en aproximadamente un 80%.
- **Control de Calidad:** Módulo de auditoría que detecta nulos, viajes inconsistentes (duraciones irreales) y errores de esquema.
- **Análisis Automatizado:** Generación de KPIs como total de viajes, duración promedio y estaciones con mayor demanda.
- **Dashboard Interactivo:** 🆕 Visualización en tiempo real con Streamlit y gráficos interactivos con Plotly.

## 📂 Estructura del Proyecto

```text
ecobici-rolling-window/
├── data/                    # Almacén de archivos .parquet (ventana de 13 meses)
├── scripts/
│   ├── update_data.py      # Scraping y descarga de nuevos datasets
│   ├── process_data.py     # Transformación y limpieza con Polars
│   ├── quality_check.py    # Validación automática de integridad
│   ├── analysis.py         # Motor de análisis (clase EcobiciEngine)
│   ├── dashboard.py        # 🆕 Dashboard interactivo con Streamlit
│   └── utils/
│       └── paths.py        # Gestión de rutas del proyecto
├── tests/                   # Suite de pruebas con pytest
│   ├── conftest.py
│   ├── test_analysis.py
│   ├── test_process_data.py
│   ├── test_quality_check.py
│   └── test_update_data.py
├── main.py                  # Orquestador del pipeline completo
├── requirements.txt         # Dependencias del proyecto
├── requirements-dev.txt     # Dependencias de desarrollo
├── pyproject.toml          # Configuración de Ruff (linter/formatter)
└── README.md               # Documentación
```

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd ecobici-rolling-window

# Instalar dependencias
pip install -r requirements.txt

# Para desarrollo (incluye pytest y ruff)
pip install -r requirements-dev.txt
```

## 🚀 Uso

### Pipeline Completo
Ejecuta el flujo completo de datos (descarga, procesamiento, validación y análisis):

```bash
python main.py
```

### Dashboard Interactivo 🆕
Lanza el dashboard de visualización en el navegador:

```bash
streamlit run scripts/dashboard.py
```

El dashboard se abrirá automáticamente en `http://localhost:8501`

### Módulos Individuales

```bash
# Solo procesar archivos CSV a Parquet
python -m scripts.process_data

# Solo ejecutar control de calidad
python -m scripts.quality_check

# Solo generar reporte de análisis
python -m scripts.analysis
```

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=scripts

# Solo tests unitarios (excluir tests de integración)
pytest -m "not integration"
```

## 🛠️ Tecnologías

| Tecnología | Uso |
|------------|-----|
| **Python 3.10+** | Lenguaje base |
| **Polars** | Procesamiento ultra rápido de DataFrames |
| **BeautifulSoup4** | Web scraping del portal de datos abiertos |
| **Streamlit** | 🆕 Framework de dashboard interactivo |
| **Plotly** | 🆕 Gráficos interactivos |
| **pytest** | Framework de testing |
| **Ruff** | Linter y formatter de código |

## 📊 Métricas del Proyecto

- **Reducción de tamaño:** ~80% (CSV → Parquet con compresión zstd)
- **Velocidad de procesamiento:** Millones de registros en segundos con Polars
- **Cobertura de tests:** > 85%
- **Ventana de datos:** 13 meses rodantes

## 🚧 Roadmap

- [ ] Mejorar dashboard con filtros interactivos (rango de fechas, estaciones)
- [ ] Agregar mapas de calor de estaciones más concurridas
- [ ] Configurar despliegue en Streamlit Cloud / Heroku / Railway
- [ ] Implementar caché de datos para mejorar rendimiento del dashboard
- [ ] API REST para consultar datos desde aplicaciones externas

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.
