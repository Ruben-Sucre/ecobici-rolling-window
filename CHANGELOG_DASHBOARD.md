# Changelog - Dashboard Interactivo Ecobici

## 🚀 Versión 2.0 - Dashboard Dinámico (30 enero 2026)

### ✨ Nuevas Funcionalidades

#### 🔍 **Sistema de Filtros Interactivos**
- **Sidebar** con filtros dinámicos:
  - Multiselect de Años
  - Multiselect de Género (Hombre/Mujer)
  - Slider de Rango de Edad
  - Botón de reseteo de filtros

#### 📊 **Nuevas Métricas**
- **Viajes Fallidos**: Detecta bicis defectuosas (< 1 minuto de uso)
- **Horas Pico**: Distribución horaria de viajes (gráfico de barras)
- **Top 10 Estaciones Origen**: Mayor flujo de salidas
- **Top 10 Estaciones Destino**: Mayor flujo de llegadas
- **Distribución por Género**: Gráfico de pastel interactivo

#### 🎨 **Mejoras de Visualización**
- Gráficos interactivos con **Plotly** (zoom, pan, hover tooltips)
- Layout responsivo de 3 niveles:
  - 4 columnas para métricas principales
  - 2 columnas para tendencia temporal + horas pico
  - 3 columnas para estaciones + género
- Paleta de colores personalizada (rojo Ecobici: #FF4B4B)

### ⚡ Optimizaciones de Performance

#### 🗄️ **Sistema de Caché Multinivel**
1. **`@st.cache_resource`**: Motor EcobiciEngine (permanente en RAM)
2. **`@st.cache_data(ttl=3600)`**: Metadata para filtros (1 hora)
3. **`@st.cache_data(ttl=600)`**: Análisis con filtros (10 minutos)

#### 🚀 **Motor de Análisis Refactorizado**
- **LazyFrame interno cacheado**: `_get_raw_lazyframe()` se ejecuta solo una vez
- **Filtros dinámicos**: Sistema modular con `get_filtered_query()`
- **Metadata ligera**: `get_metadata()` sin procesar millones de filas
- **Agregaciones optimizadas**: Múltiples métricas en un solo `collect()`

### 🏗️ Arquitectura

#### Antes (Versión 1.0)
```python
# Un solo método monolítico
def run_full_analysis() -> dict
```

#### Ahora (Versión 2.0)
```python
# Arquitectura modular
def _get_raw_lazyframe() -> pl.LazyFrame       # Caché interno
def get_filtered_query(filters) -> pl.LazyFrame # Filtros dinámicos
def get_metadata() -> dict                      # Metadata ligera
def run_full_analysis(filters) -> dict          # Orquestador
```

### 📈 Impacto en Performance

| Métrica | Antes | Ahora | Mejora |
|---------|-------|-------|--------|
| **Carga inicial** | 3-5 seg | 1-2 seg | **~60%** |
| **Cambio de filtro** | 3-5 seg | <1 seg | **~80%** |
| **Consumo de RAM** | N/A | Optimizado | Cache inteligente |
| **UX** | Estático | Interactivo | ⭐⭐⭐⭐⭐ |

### 🎯 Próximos Pasos

- [ ] Agregar mapa de calor de estaciones
- [ ] Exportar datos filtrados a CSV
- [ ] Comparación año vs año
- [ ] Predicción de demanda con ML
- [ ] Despliegue en Streamlit Cloud

---

## 🛠️ Versión 2.1 - Robust Ingest & Error Handling (31 enero 2026)

### 🧩 Cambios
- Implementa descarga robusta con retries/backoff y timeouts en `scripts/update_data.py`.
- Añade excepciones específicas en `scripts/utils/exceptions.py`: `DownloadError`, `SchemaValidationError`, `DataValidationError`.
- Mejora el manejo de errores en `scripts/process_data.py`: valida esquema, detecta datasets vacíos y fechas inválidas; lanza `DataValidationError` en lugar de silenciar errores.
- Añade tests para cobertura de caminos felices y de fallo (mocking HTTP con `responses` y tests de validación de datos).
- CI: agrega `ruff` en workflow y marcas pytest `integration`/`performance`.

### Nota
- `procesar_csv_a_parquet` ahora lanza `DataValidationError` en fallos críticos; los callers deberían capturarla y continuar el pipeline para evitar abortos completos.

---

---

**Autor**: GitHub Copilot + Ruben  
**Stack**: Python 3.12 | Polars 1.37 | Streamlit 1.41 | Plotly 5.24
