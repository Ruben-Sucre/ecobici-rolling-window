# Ecobici Data Pipeline 🚲🇲🇽

Este proyecto es un pipeline de datos automatizado diseñado para extraer, procesar y analizar la información de **Ecobici Ciudad de México**. 
El objetivo es transformar los archivos CSV masivos del portal de Datos Abiertos en un formato optimizado (Parquet) para generar reportes estadísticos 
mensuales de forma eficiente.

## 🚀 Características

- **Web Scraping:** Localiza y descarga automáticamente el dataset más reciente del portal oficial.
- **Procesamiento con Polars:** ETL de alta velocidad que convierte archivos CSV a Parquet, reduciendo el peso de los datos en aproximadamente un 80%.
- **Control de Calidad:** Módulo de auditoría que detecta nulos, viajes inconsistentes (duraciones irreales) y errores de esquema.
- **Análisis Automatizado:** Generación de KPIs como total de viajes, duración promedio y estaciones con mayor demanda.

## 📂 Estructura del Proyecto

```text
ecobici-project/
├── data/               # Almacén de archivos .parquet (ventana de 13 meses)
├── scripts/
│   ├── update_data.py    # Scraping y descarga de nuevos datasets
│   ├── process_data.py   # Transformación y limpieza con Polars
│   ├── quality_check.py  # Validación automática de integridad
│   └── analysis.py       # Generación de estadísticas y KPIs
├── main.py             # Orquestador del pipeline completo
├── requirements.txt    # Dependencias del proyecto
└── README.md           # Documentación
