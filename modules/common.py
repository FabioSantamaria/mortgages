import copy
import numpy as np
import pandas as pd

def map_distribution_name_es_to_en(name: str) -> str:
    mapping = {
        'Gaussiana': 'Gaussian',
        'Reversión a la Media': 'Mean Reverting',
        'Caminata Aleatoria Uniforme': 'Uniform Random Walk',
        'Constante': 'Constant'
    }
    return mapping.get(name, 'Constant')

def map_distribution_params(distribution_type: str, params_es: dict, euribor_inicial: float) -> dict:
    """Map Spanish UI params to engine params for the chosen distribution."""
    if distribution_type == 'Gaussian':
        return {
            'volatility': params_es.get('desviacion', 1.0),
            'drift': params_es.get('media', 3.0) - euribor_inicial
        }
    elif distribution_type == 'Mean Reverting':
        return {
            'mean_level': params_es.get('media_largo_plazo', 3.0),
            'reversion_speed': params_es.get('velocidad_reversion', 0.1),
            'volatility': params_es.get('volatilidad', 0.3)
        }
    elif distribution_type == 'Uniform Random Walk':
        return {
            'max_change': params_es.get('cambio_maximo', 0.25)
        }
    else:
        return {}

def copy_inyecciones(inyecciones: list) -> list:
    return copy.deepcopy(inyecciones) if inyecciones else []

def format_currency(value: float) -> str:
    return f"{value:,.0f}"

def format_percent(value: float) -> str:
    return f"{value:.2f}"

def aggregate_per_simulation(df_all_sims: pd.DataFrame) -> dict:
    """Compute averages across simulations for interests, total paid, and months."""
    by_sim = df_all_sims.groupby('Simulation')
    total_intereses_promedio = by_sim['Intereses_mensuales'].sum().mean()
    total_pagado_promedio = by_sim['Cuota_mensual'].sum().mean()
    meses_totales_promedio = by_sim.size().mean()
    return {
        'total_intereses_promedio': total_intereses_promedio,
        'total_pagado_promedio': total_pagado_promedio,
        'meses_totales_promedio': meses_totales_promedio
    }