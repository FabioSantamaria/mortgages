import pandas as pd
from modules.monte_carlo import run_monte_carlo_simulation, calculate_simulation_statistics

def test_run_monte_carlo_simulation_basic():
    df = run_monte_carlo_simulation(
        capital_inicial=100000,
        spread=1.5,
        plazo_anos=20,
        initial_euribor=2.0,
        distribution_type='Constant',
        num_simulations=5,
        inyecciones=[]
    )
    assert isinstance(df, pd.DataFrame)
    assert 'Simulation' in df.columns
    assert len(df) > 0

def test_calculate_simulation_statistics_shape():
    df = run_monte_carlo_simulation(
        capital_inicial=100000,
        spread=1.5,
        plazo_anos=5,
        initial_euribor=2.0,
        distribution_type='Constant',
        num_simulations=3,
        inyecciones=[]
    )
    stats = calculate_simulation_statistics(df)
    assert isinstance(stats, pd.DataFrame)
    assert 'Mes' in stats.columns
    assert any(col.startswith('Cuota_mensual_') for col in stats.columns)