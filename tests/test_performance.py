import polars as pl
import time
from scripts import analysis

def test_engine_performance_large(tmp_path):
    # Crear un DataFrame grande (1 millón de filas)
    n = 1_000_000
    generos = (["M", "F", "O"] * ((n // 3) + 1))[:n]
    from datetime import datetime, timedelta
    base = datetime(2024, 1, 1, 7, 0, 0)
    df = pl.DataFrame({
        "genero": generos,
        "edad": [25] * n,
        "bici_id": list(range(n)),
        "estacion_origen_id": [1] * n,
        "estacion_destino_id": [2] * n,
        "fecha_origen": [base] * n,
        "fecha_destino": [base + timedelta(minutes=12)] * n,
    })
    parquet_path = tmp_path / "ecobici_big.parquet"
    df.write_parquet(parquet_path)
    engine = analysis.EcobiciEngine(data_dir=tmp_path)
    start = time.time()
    results = engine.get_filtered_query().collect()
    elapsed = time.time() - start
    # El procesamiento debe ser razonablemente rápido (<10s)
    assert elapsed < 10, f"Procesamiento muy lento: {elapsed:.2f}s"
    assert len(results) == n
