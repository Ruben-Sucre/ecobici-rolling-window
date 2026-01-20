import polars as pl
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def ejecutar_control_calidad(nombre_archivo_parquet):
    """
    Realiza una auditoría de integridad sobre un archivo Parquet específico.
    """
    ruta_archivo = DATA_DIR / nombre_archivo_parquet
    
    if not ruta_archivo.exists():
        print(f"⚠️ El archivo {nombre_archivo_parquet} no existe para validación.")
        return False

    print(f"🔍 Auditando calidad de: {nombre_archivo_parquet}...")
    
    # Usamos scan_parquet para no cargar todo en RAM innecesariamente
    df = pl.scan_parquet(ruta_archivo)

    # Definición de métricas de calidad
    check = df.select([
        # 1. Viajes fuera de rango de tiempo (según tus criterios de análisis)
        ((pl.col("fecha_hora_arribo") - pl.col("fecha_hora_retiro")).dt.total_minutes() <= 1)
        .sum().alias("viajes_muy_cortos"),
        
        ((pl.col("fecha_hora_arribo") - pl.col("fecha_hora_retiro")).dt.total_minutes() >= 180)
        .sum().alias("viajes_muy_largos"),
        
        # 2. Integridad de usuarios
        pl.col("genero").is_null().sum().alias("nulos_genero"),
        pl.col("edad").filter(pl.col("edad") == 0).count().alias("edades_en_cero"),
        
        # 3. Integridad de infraestructura
        pl.col("estacion_origen_id").is_null().sum().alias("origen_nulo"),
        pl.col("estacion_destino_id").is_null().sum().alias("destino_nulo"),
        
        # 4. Total de registros
        pl.len().alias("total_registros")
    ]).collect()

    # Extraer resultados para validación lógica
    res = check.to_dicts()[0]
    
    print(f"📊 Resumen de Calidad:")
    print(f"   - Total registros: {res['total_registros']:,}")
    print(f"   - Viajes sospechosos (<1m o >3h): {res['viajes_muy_cortos'] + res['viajes_muy_largos']}")
    print(f"   - Datos de usuario faltantes (edad/género): {res['edades_en_cero'] + res['nulos_genero']}")

    # Umbral de tolerancia: Si más del 10% de los datos son nulos o inconsistentes, lanzar advertencia
    umbral_error = res['total_registros'] * 0.10
    total_inconsistencias = sum([res['origen_nulo'], res['destino_nulo'], res['nulos_genero']])

    if total_inconsistencias > umbral_error:
        print(f"❌ ALERTA: El archivo tiene un nivel de inconsistencia alto ({total_inconsistencias} fallos).")
        return False
    
    print("✅ Calidad validada: El archivo cumple con los estándares mínimos.")
    return True

if __name__ == "__main__":
    # Prueba rápida con el último archivo procesado
    ejecutar_control_calidad("ecobici_2025-12.parquet")