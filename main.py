import os
from scripts import update_data, process_data, quality_check, analysis

def run_pipeline():
    print("🚀 Iniciando el pipeline de automatización Ecobici...\n")

    # 1. ACTUALIZACIÓN: Buscar y descargar nuevos datos
    print("Step 1: Buscando actualizaciones en el portal de Datos Abiertos...")
    nuevo_csv = update_data.buscar_y_descargar_nuevo_csv()
    
    # 2. PROCESAMIENTO: Convertir CSVs pendientes a Parquet
    print("\nStep 2: Procesando archivos CSV pendientes...")
    pendientes = process_data.obtener_csv_pendientes()
    
    if not pendientes:
        print("☕ No hay archivos nuevos para procesar.")
    else:
        for csv_path in pendientes:
            # Procesar el archivo
            exito = process_data.procesar_csv_a_parquet(csv_path)
            
            if exito:
                # 3. CALIDAD: Si el proceso fue exitoso, ejecutar auditoría
                mes_str = csv_path.stem  # Extrae el nombre (ej. "2025-12")
                archivo_parquet = f"ecobici_{mes_str}.parquet"
                
                print(f"\nStep 3: Ejecutando control de calidad para {archivo_parquet}...")
                calidad_ok = quality_check.ejecutar_control_calidad(archivo_parquet)
                
                if calidad_ok:
                    # Preguntar si se borra el original (siguiendo la lógica de tu script)
                    borrar = input(f"¿Deseas borrar el CSV original {csv_path.name}? (s/n): ").lower()
                    if borrar in ['s', '', 'si']:
                        csv_path.unlink()
                        print(f"🗑️ Archivo {csv_path.name} eliminado.")
                else:
                    print(f"⚠️ Atención: El archivo {archivo_parquet} no pasó las pruebas de calidad.")

    # 4. ANÁLISIS: Generar reporte con la ventana de 13 meses
    print("\nStep 4: Generando reporte estadístico mensual...")
    try:
        reporte = analysis.generar_reporte_mensual()
        print(reporte)
    except Exception as e:
        print(f"❌ Error al generar el reporte: {e}")

    print("\n✅ Pipeline finalizado con éxito.")

if __name__ == "__main__":
    run_pipeline()