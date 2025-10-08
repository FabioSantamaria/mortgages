import math
import pandas as pd
from modules.calculations import cuota_mensual, simulacion_hipoteca_multiple_inyeccion

def test_cuota_mensual_basic():
    cuota = cuota_mensual(100000, 3.0, 240)  # 20 years
    assert cuota > 0
    assert math.isfinite(cuota)

def test_simulacion_multiple_inyeccion_basic():
    df = simulacion_hipoteca_multiple_inyeccion(
        capital_inicial=100000,
        tasa=3.0,
        plazo_inicial=240,
        cuota_inicial=cuota_mensual(100000, 3.0, 240),
        inyecciones=[{'mes_inyeccion': 12, 'capital_inyectado': 5000, 'tipo_inyeccion': 'plazo'}]
    )
    assert isinstance(df, pd.DataFrame)
    assert set(['Mes','Capital_pendiente','Cuota_mensual','Intereses_mensuales','Amortizacion_mensual']).issubset(df.columns)