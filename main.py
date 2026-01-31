from __future__ import annotations

import argparse
import logging
from pathlib import Path

# 1. IMPORTANTE: Solo una línea para los módulos de scripts
from scripts import analysis, process_data, quality_check
# 2. El helper de rutas
from scripts.utils.paths import get_data_dir

logger = logging.getLogger(__name__)

def run_pipeline(data_dir: Path | str | None = None, delete_original: bool = False) -> None:
    base_dir = get_data_dir(data_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    logger.info("🚀 Iniciando el pipeline de automatización Ecobici...")

    # 1. ACTUALIZACIÓN: Buscar y descargar nuevos datos
    logger.info("Step 1: Buscando actualizaciones en el portal de Datos Abiertos...")
    
    # 2. PROCESAMIENTO: Convertir CSVs pendientes a Parquet
    logger.info("Step 2: Procesando archivos CSV pendientes...")
    pendientes = process_data.obtener_csv_pendientes(base_dir)
    
    if not pendientes:
        logger.info("☕ No hay archivos nuevos para procesar.")
    else:
        for csv_path in pendientes:
            # Procesar el archivo
            exito = process_data.procesar_csv_a_parquet(csv_path, base_dir)
            
            if exito:
                # 3. CALIDAD: Si el proceso fue exitoso, ejecutar auditoría
                mes_str = csv_path.stem  # Extrae el nombre (ej. "2025-12")
                archivo_parquet = f"ecobici_{mes_str}.parquet"
                
                logger.info("Step 3: Ejecutando control de calidad para %s...", archivo_parquet)
                calidad_ok = quality_check.ejecutar_control_calidad(archivo_parquet, base_dir)
                
                if calidad_ok:
                    if delete_original:
                        csv_path.unlink()
                        logger.info("🗑️ Archivo %s eliminado.", csv_path.name)
                    else:
                        logger.info("📁 Archivo %s conservado.", csv_path.name)
                else:
                    logger.warning(
                        "⚠️ Atención: El archivo %s no pasó las pruebas de calidad.",
                        archivo_parquet,
                    )

    # 4. ANÁLISIS: Generar reporte con la ventana de 13 meses
    logger.info("Step 4: Generando reporte estadístico mensual...")
    try:
        reporte = analysis.generar_reporte_mensual(base_dir)
        logger.info("%s", reporte)
    except Exception as e:
        logger.error("❌ Error al generar el reporte: %s", e)

    logger.info("✅ Pipeline finalizado con éxito.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline de automatización Ecobici")
    parser.add_argument(
        "--delete-original",
        action="store_true",
        help="Borra el CSV original si el control de calidad es exitoso.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directorio base de datos (opcional).",
    )
    return parser

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _build_parser().parse_args()
    run_pipeline(data_dir=args.data_dir, delete_original=args.delete_original)