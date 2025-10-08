import pandas as pd
from modules.mixed_mortgage import run_mixed_monte_carlo_simulation, calculate_mixed_simulation_statistics

def test_run_mixed_monte_carlo_simulation_basic():
    df = run_mixed_monte_carlo_simulation(
        capital_inicial=100000,
        tasa_fija=2.0,
        spread=1.5,
        plazo_anos=20,
        anos_fijos=5,
        initial_euribor=2.0,
        distribution_type='Constant',
        num_simulations=5,
        inyecciones=[]
    )
    assert isinstance(df, pd.DataFrame)
    assert 'Simulation' in df.columns
    assert 'Tipo_Periodo' in df.columns

def test_calculate_mixed_simulation_statistics_shape():
    df = run_mixed_monte_carlo_simulation(
        capital_inicial=100000,
        tasa_fija=2.0,
        spread=1.5,
        plazo_anos=5,
        anos_fijos=2,
        initial_euribor=2.0,
        distribution_type='Constant',
        num_simulations=3,
        inyecciones=[]
    )
    stats = calculate_mixed_simulation_statistics(df)
    assert isinstance(stats, pd.DataFrame)
    assert 'Mes' in stats.columns
    assert any(col.startswith('Cuota_mensual_') for col in stats.columns)