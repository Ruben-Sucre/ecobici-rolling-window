# Futuros / Notas de rendimiento

- Detectar y normalizar nombres de columnas de tiempo: algunos archivos usan
  `fecha_origen`/`fecha_destino` mientras que otros usan `fecha_hora_retiro`/
  `fecha_hora_arribo`. El control de calidad ahora intenta resolver ambos casos
  automáticamente; sin embargo, cualquier nueva convención debe añadirse al
  resolvedor en `scripts/quality_check.py`.

- Evitar cargar columnas innecesarias: proyectar columnas al leer Parquet
  reduce el I/O y el uso de memoria.

- Profiling local: los artefactos `*.prof` y las carpetas `tmp_profile_data*`
  están en `.gitignore` y se usan para investigar cuellos de botella.

- Próximos pasos sugeridos:
  - Añadir pruebas que verifiquen distintas convenciones de nombres de columnas
    de fecha.
  - Registrar las convenciones observadas en los metadatos para normalizar
    upstream si es posible.
