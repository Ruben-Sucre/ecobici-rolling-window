# Criterios de éxito para la suite de pruebas

- Todas las pruebas unitarias y de integración deben pasar sin errores.
- El motor de análisis debe manejar datos inválidos (géneros desconocidos, edades nulas, fechas inconsistentes) sin lanzar excepciones inesperadas.
- El dashboard debe importar y cargar sin errores críticos.
- El procesamiento de grandes volúmenes de datos debe completarse en menos de 10 segundos para 1 millón de registros sintéticos.
- Los errores de archivos corruptos deben ser detectados y reportados adecuadamente.
- Las pruebas deben ser reproducibles en cualquier entorno con dependencias instaladas.
