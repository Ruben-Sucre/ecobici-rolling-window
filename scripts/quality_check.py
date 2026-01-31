from __future__ import annotations

from pathlib import Path
from typing import Iterable

import polars as pl

from .utils.paths import get_data_dir


def _detectar_columnas_denormalizadas(schema: dict[str, object]) -> list[str]:
	"""
	Detecta columnas que parecen almacenar atributos dimensionales (p. ej. *_nombre, *_descripcion)
	y que además tienen un correspondiente *_id en el mismo schema.
	"""
	denorm = []
	cols = set(schema.keys())
	for col in cols:
		if any(tok in col for tok in ("nombre", "descripcion")):
			# extraer prefijo antes del último _
			if "_" in col:
				pref = col.rsplit("_", 1)[0]
				id_cand = f"{pref}_id"
				if id_cand in cols:
					denorm.append(col)
	return denorm

def _chequear_integridad_referencial(ruta_fact: Path, schema: dict[str, object], base_dir: Path) -> list[str]:
	"""
	Para cada columna que termina en _id en la fact table, intenta localizar la dimensión
	(asumiendo nombres comunes como 'estaciones.parquet' o 'usuarios.parquet') y verifica
	que todos los ids presentes en la fact existen en la dimensión.
	Devuelve una lista de mensajes de fallo (vacía si todo ok).
	"""
	issues: list[str] = []
	# mapeo heurístico: si la columna contiene 'estacion' -> estaciones.parquet, 'usuario' -> usuarios.parquet
	for col in [c for c in schema.keys() if c.endswith("_id")]:
		target_file = None
		if "estacion" in col or "station" in col:
			cand = base_dir / "estaciones.parquet"
			if cand.exists():
				target_file = cand
		if "usuario" in col or "user" in col:
			cand = base_dir / "usuarios.parquet"
			if cand.exists():
				target_file = cand
		# si no encontramos fichero dim, saltar (solo aviso)
		if target_file is None:
			issues.append(f"Advertencia: No se encontró dimensión esperada para columna '{col}'.")
			continue

		# cargar ids de dimensión (intentar usar la columna con mismo nombre o 'id' como fallback)
		dim_df = pl.read_parquet(target_file)
		if col in dim_df.columns:
			dim_id_col = col
		elif "id" in dim_df.columns:
			dim_id_col = "id"
		else:
			# buscar alguna columna *_id en la dimensión
			cands = [c for c in dim_df.columns if c.endswith("_id")]
			if cands:
				dim_id_col = cands[0]
			else:
				issues.append(f"Advertencia: la dimensión {target_file.name} no tiene columna id utilizable para '{col}'.")
				continue

		# recoger ids únicos de fact y dimensión (colecciones en memoria)
		try:
			fact_ids = pl.scan_parquet(ruta_fact).select(pl.col(col)).unique().collect()[col].to_list()
		except Exception as e:
			issues.append(f"Error al leer columna '{col}' de la fact: {e}")
			continue

		dim_ids = dim_df.select(dim_id_col).unique().to_series().to_list()
		missing = set(fact_ids) - set(dim_ids)
		if missing:
			sample = list(missing)[:5]
			issues.append(f"Fallo referencial para '{col}': {len(missing)} ids no encontrados en {target_file.name} (ej.: {sample}).")

	return issues


def ejecutar_control_calidad(
    nombre_archivo_parquet: str | Path,
    data_dir: Path | str | None = None,
) -> bool:
    """
    Realiza una auditoría de integridad sobre un archivo Parquet específico.
    """
    base_dir = get_data_dir(data_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = Path(nombre_archivo_parquet)
    ruta_archivo = (
        parquet_path
        if parquet_path.is_absolute()
        else base_dir / parquet_path
    )
    
    if not ruta_archivo.exists():
        print(f"⚠️ El archivo {nombre_archivo_parquet} no existe para validación.")
        return False

    print(f"🔍 Auditando calidad de: {nombre_archivo_parquet}...")
    
    # Usamos scan_parquet para no cargar todo en RAM innecesariamente
    df = pl.scan_parquet(ruta_archivo)

    # nueva: obtener schema para chequeos de normalización (usar collect_schema para
    # evitar resolver todo el LazyFrame y eliminar el PerformanceWarning)
    schema = df.collect_schema()

    # Chequeo de normalización: detecta columnas denormalizadas
    denorm_cols = _detectar_columnas_denormalizadas(schema)
    if denorm_cols:
        print("⚠️ Se detectaron columnas probablemente denormalizadas en la tabla fact:")
        for c in denorm_cols:
            print(f"   - {c}")
    else:
        print("✅ No se detectaron columnas claramente denormalizadas.")

    # Chequeo referencial contra dimensiones esperadas
    referential_issues = _chequear_integridad_referencial(ruta_archivo, schema, base_dir)
    if referential_issues:
        print("❌ Problemas de integridad referencial / dimensiones:")
        for msg in referential_issues:
            print(f"   - {msg}")
    else:
        print("✅ Integridad referencial mínima verificada (si existen dimensiones).")

    # Definición de métricas de calidad
    check = df.select([
        # 1. Viajes fuera de rango de tiempo (según tus criterios de análisis)
        ((pl.col("fecha_destino") - pl.col("fecha_origen")).dt.total_minutes() <= 1)
        .sum().alias("viajes_muy_cortos"),
        
        ((pl.col("fecha_destino") - pl.col("fecha_origen")).dt.total_minutes() >= 180)
        .sum().alias("viajes_muy_largos"),
        
        # 2. Integridad de usuarios
        pl.col("genero").is_null().sum().alias("nulos_genero"),
        pl.col("edad").is_null().sum().alias("edades_nulas"),
        
        # 3. Integridad de infraestructura
        pl.col("estacion_origen_id").is_null().sum().alias("origen_nulo"),
        pl.col("estacion_destino_id").is_null().sum().alias("destino_nulo"),
        
        # 4. Total de registros
        pl.len().alias("total_registros")
    ]).collect()

    # Extraer resultados para validación lógica
    res = check.to_dicts()[0]
    
    print("📊 Resumen de Calidad:")
    print(f"   - Total registros: {res['total_registros']:,}")
    print(f"   - Viajes sospechosos (<1m o >3h): {res['viajes_muy_cortos'] + res['viajes_muy_largos']}")
    print(f"   - Datos de usuario faltantes (edad/género): {res['edades_nulas'] + res['nulos_genero']}")

    # Umbral de tolerancia: Si más del 10% de los datos son nulos o inconsistentes, lanzar advertencia
    umbral_error = res['total_registros'] * 0.10
    total_inconsistencias = sum([res['origen_nulo'], res['destino_nulo'], res['nulos_genero']])

    # considerar fallos de normalización/referencial como errores críticos
    if denorm_cols:
        print(f"❌ ALERTA: La tabla parece denormalizada (columnas: {denorm_cols}).")
        return False

    if any("Fallo referencial" in s for s in referential_issues):
        print("❌ ALERTA: Fallos referenciales detectados.")
        return False

    if total_inconsistencias > umbral_error:
        print(f"❌ ALERTA: El archivo tiene un nivel de inconsistencia alto ({total_inconsistencias} fallos).")
        return False
    
    print("✅ Calidad validada: El archivo cumple con los estándares mínimos.")
    return True

if __name__ == "__main__":
    # Prueba rápida con el último archivo procesado
    ejecutar_control_calidad("ecobici_2025-12.parquet")