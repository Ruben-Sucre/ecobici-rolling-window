from __future__ import annotations

import argparse
import csv
import logging
import re
import unicodedata
from pathlib import Path

import polars as pl

from .utils.paths import get_data_dir
from .utils.exceptions import DataValidationError, SchemaValidationError

logger = logging.getLogger(__name__)


def obtener_csv_pendientes(data_dir: Path | str | None = None) -> list[Path]:
    target_dir = get_data_dir(data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    csvs = list(target_dir.glob("*.csv"))
    pendientes = []
    for archivo_csv in csvs:
        match = re.search(r"(\d{4}-\d{2})", archivo_csv.name)
        if match:
            mes = match.group(1)
            archivo_parquet = target_dir / f"ecobici_{mes}.parquet"
            if not archivo_parquet.exists():
                pendientes.append(archivo_csv)
    pendientes.sort()
    return pendientes


def _leer_encabezado_csv(ruta_csv: Path) -> list[str]:
    with ruta_csv.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.reader(archivo)
        return next(lector, [])


def _normalizar_columna(nombre: str) -> str:
    texto = unicodedata.normalize("NFKD", nombre)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.strip().lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return texto


_COLUMN_MAPPING = {
    "genero_usuario": "genero",
    "genero": "genero",
    "sexo_usuario": "genero",
    "sexo": "genero",
    "edad_usuario": "edad",
    "edad": "edad",
    "bici": "bici_id",
    "bicicleta": "bici_id",
    "id_bici": "bici_id",
    "bici_id": "bici_id",
    "ciclo_estacion_retiro": "estacion_origen_id",
    "ciclo_estacion_origen": "estacion_origen_id",
    "estacion_retiro": "estacion_origen_id",
    "estacion_origen": "estacion_origen_id",
    "id_estacion_origen": "estacion_origen_id",
    "estacion_origen_id": "estacion_origen_id",
    "ciclo_estacionarribo": "estacion_destino_id",
    "ciclo_estacion_arribo": "estacion_destino_id",
    "estacion_arribo": "estacion_destino_id",
    "estacion_destino": "estacion_destino_id",
    "id_estacion_destino": "estacion_destino_id",
    "estacion_destino_id": "estacion_destino_id",
    "fecha_retiro": "fecha_origen",
    "fecha_origen": "fecha_origen",
    "fecha_inicio": "fecha_origen",
    "fecha_salida": "fecha_origen",
    "hora_retiro": "hora_origen",
    "hora_origen": "hora_origen",
    "hora_inicio": "hora_origen",
    "hora_salida": "hora_origen",
    "fecha_arribo": "fecha_destino",
    "fecha_destino": "fecha_destino",
    "fecha_fin": "fecha_destino",
    "fecha_llegada": "fecha_destino",
    "hora_arribo": "hora_destino",
    "hora_destino": "hora_destino",
    "hora_fin": "hora_destino",
    "hora_llegada": "hora_destino",
}

_REQUIRED_COLUMNS = {
    "genero",
    "edad",
    "bici_id",
    "estacion_origen_id",
    "estacion_destino_id",
    "fecha_origen",
    "hora_origen",
    "fecha_destino",
    "hora_destino",
}


def _mapear_columnas(encabezado: list[str]) -> dict[str, str]:
    renombres: dict[str, str] = {}
    for columna in encabezado:
        normalizada = _normalizar_columna(columna)
        estandar = _COLUMN_MAPPING.get(normalizada)
        if estandar and estandar not in renombres.values():
            renombres[columna] = estandar

    faltantes = _REQUIRED_COLUMNS - set(renombres.values())
    if faltantes:
        faltantes_texto = ", ".join(sorted(faltantes))
        from .utils.exceptions import SchemaValidationError
        raise SchemaValidationError(f"Faltan columnas requeridas: {faltantes_texto}")

    return renombres

def procesar_csv_a_parquet(ruta_csv: Path | str, data_dir: Path | str | None = None) -> bool:
    target_dir = get_data_dir(data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    ruta_csv = Path(ruta_csv)
    match = re.search(r"(\d{4}-\d{2})", ruta_csv.name)
    if not match:
        raise ValueError(f"El nombre del archivo {ruta_csv.name} no contiene un patrón de fecha YYYY-MM")
    mes = match.group(1)
    ruta_salida = target_dir / f"ecobici_{mes}.parquet"
    
    logger.info("⚙️ Procesando: %s...", ruta_csv.name)

    try:
        encabezado = _leer_encabezado_csv(ruta_csv)
        renombres = _mapear_columnas(encabezado)
        schema_por_columna = {
            "genero": pl.Utf8,
            "edad": pl.Int64,
            "bici_id": pl.Int64,
            "estacion_origen_id": pl.Int64,
            "estacion_destino_id": pl.Int64,
            "fecha_origen": pl.Utf8,
            "hora_origen": pl.Utf8,
            "fecha_destino": pl.Utf8,
            "hora_destino": pl.Utf8,
        }
        schema_dict = {
            columna_original: schema_por_columna[columna_estandar]
            for columna_original, columna_estandar in renombres.items()
            if columna_estandar in schema_por_columna
        }

        df = pl.read_csv(
            ruta_csv,
            schema_overrides=schema_dict,
            null_values=["NULL", "null", ""],
            ignore_errors=False,
        )

        df = df.rename(renombres)

        # Validación: DataFrame no vacío
        if df.height == 0:
            logger.error("Dataset vacío: %s", ruta_csv)
            raise DataValidationError("Dataset vacío")

        genero_normalizado = (
            pl.col("genero")
            .cast(pl.Utf8, strict=False)
            .str.strip_chars()
            .str.to_uppercase()
        )
        edad_col = pl.col("edad").cast(pl.Int64, strict=False)

        df_limpio = df.with_columns([
            pl.when(genero_normalizado.is_null() | (genero_normalizado == ""))
            .then(pl.lit("O"))
            .when(genero_normalizado.is_in(["F", "FEMENINO", "MUJER", "MUJERES"]))
            .then(pl.lit("F"))
            .when(genero_normalizado.is_in(["M", "MASCULINO", "H", "HOMBRE", "HOMBRES"]))
            .then(pl.lit("M"))
            .otherwise(pl.lit("O"))
            .alias("genero"),
            pl.when(edad_col.is_null() | (edad_col == 0) | (edad_col > 100))
            .then(None)
            .otherwise(edad_col)
            .alias("edad"),
            pl.col("bici_id").cast(pl.Int64, strict=False).alias("bici_id"),
            pl.col("estacion_origen_id").cast(pl.Int64, strict=False).alias("estacion_origen_id"),
            pl.col("estacion_destino_id").cast(pl.Int64, strict=False).alias("estacion_destino_id"),
            pl.format("{} {}", pl.col("fecha_origen"), pl.col("hora_origen"))
            .str.to_datetime(format="%d/%m/%Y %H:%M:%S", strict=False)
            .alias("fecha_origen"),
            pl.format("{} {}", pl.col("fecha_destino"), pl.col("hora_destino"))
            .str.to_datetime(format="%d/%m/%Y %H:%M:%S", strict=False)
            .alias("fecha_destino"),
        ]).select([
            pl.col("genero"),
            pl.col("edad"),
            pl.col("bici_id"),
            pl.col("estacion_origen_id"),
            pl.col("estacion_destino_id"),
            pl.col("fecha_origen"),
            pl.col("fecha_destino"),
        ])

        # Validación: fechas de origen/destino no todas inválidas
        if df_limpio.filter(pl.col("fecha_origen").is_not_null()).height == 0:
            logger.error("Todas las fechas de origen son inválidas en: %s", ruta_csv)
            raise DataValidationError("Todas las fechas de origen son inválidas")
        if df_limpio.filter(pl.col("fecha_destino").is_not_null()).height == 0:
            logger.error("Todas las fechas de destino son inválidas en: %s", ruta_csv)
            raise DataValidationError("Todas las fechas de destino son inválidas")

        df_limpio.write_parquet(ruta_salida, compression="snappy")
        logger.info("✅ Convertido con éxito: %s", ruta_salida.name)
        return True

    except (ValueError, SchemaValidationError) as e:
        # Si el error viene de mapa de columnas, promover a DataValidationError
        if isinstance(e, SchemaValidationError):
            logger.error("Error de esquema procesando %s: %s", ruta_csv.name, e)
            raise DataValidationError("Esquema inválido") from e
        logger.error("Error de validación procesando %s: %s", ruta_csv.name, e)
        raise DataValidationError("Validación de datos falló") from e
    except OSError as e:
        logger.error("Error de IO procesando %s: %s", ruta_csv.name, e)
        raise

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Procesamiento de CSV a Parquet")
    parser.add_argument(
        "--delete-original",
        action="store_true",
        help="Borra el CSV original si el procesamiento es exitoso.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directorio base de datos (opcional).",
    )
    return parser


def main() -> None:
    pendientes = obtener_csv_pendientes()
    if not pendientes:
        logger.info("🙌 No hay archivos CSV pendientes.")
        return

    for archivo in pendientes:
        if procesar_csv_a_parquet(archivo):
            logger.info("💡 El archivo Parquet es ~80%% más ligero.")
            logger.info("📁 Archivo %s conservado.", archivo.name)


def main_cli() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    pendientes = obtener_csv_pendientes(args.data_dir)
    if not pendientes:
        logger.info("🙌 No hay archivos CSV pendientes.")
        return

    for archivo in pendientes:
        if procesar_csv_a_parquet(archivo, args.data_dir):
            logger.info("💡 El archivo Parquet es ~80%% más ligero.")
            if args.delete_original:
                archivo.unlink()
                logger.info("🗑️ Archivo %s eliminado.", archivo.name)
            else:
                logger.info("📁 Archivo %s conservado.", archivo.name)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main_cli()