import numpy as np
import pandas as pd
from .calculations import cuota_mensual, intereses_mensuales, calcular_plazo

def generate_euribor_scenario(initial_euribor, plazo_anos, distribution_type, **params):
    """Generate a single Euribor scenario based on distribution type"""
    np.random.seed(None)  # Ensure different random seeds
    
    if distribution_type == "Gaussian":
        volatility = params.get('volatility', 0.5)
        drift = params.get('drift', 0.0)
        
        # Generate monthly changes
        monthly_changes = np.random.normal(drift/12, volatility/np.sqrt(12), plazo_anos * 12)
        
        # Apply changes cumulatively
        euribor_values = [initial_euribor]
        for change in monthly_changes:
            new_value = max(euribor_values[-1] + change, -1.0)  # Floor at -1%
            euribor_values.append(new_value)
        
        return euribor_values[1:]  # Remove initial value
    
    elif distribution_type == "Mean Reverting":
        mean_level = params.get('mean_level', initial_euribor)
        reversion_speed = params.get('reversion_speed', 0.1)
        volatility = params.get('volatility', 0.3)
        
        euribor_values = [initial_euribor]
        dt = 1/12  # Monthly time step
        
        for _ in range(plazo_anos * 12):
            current = euribor_values[-1]
            drift_term = reversion_speed * (mean_level - current) * dt
            random_term = volatility * np.sqrt(dt) * np.random.normal()
            new_value = max(current + drift_term + random_term, -1.0)
            euribor_values.append(new_value)
        
        return euribor_values[1:]
    
    elif distribution_type == "Uniform Random Walk":
        max_change = params.get('max_change', 0.25)
        
        euribor_values = [initial_euribor]
        for _ in range(plazo_anos * 12):
            change = np.random.uniform(-max_change/12, max_change/12)
            new_value = max(euribor_values[-1] + change, -1.0)
            euribor_values.append(new_value)
        
        return euribor_values[1:]
    
    else:  # Constant
        return [initial_euribor] * (plazo_anos * 12)

def simulacion_hipoteca_variable_montecarlo(capital_inicial, spread, plazo_inicial, 
                                           euribor_scenario, inyecciones=None):
    """Simulate variable mortgage with given Euribor scenario"""
    if inyecciones is None:
        inyecciones = []
    
    registros = []
    capital_pendiente = capital_inicial
    mes_actual = 0
    plazo_restante = plazo_inicial
    opcion_reduccion_actual = None
    
    # Calculate initial payment
    tasa_inicial = euribor_scenario[0] + spread
    cuota_mensual_fija = cuota_mensual(capital_inicial, tasa_inicial, plazo_inicial)
    
    for mes in range(1, min(plazo_inicial + 1, len(euribor_scenario) + 1)):
        mes_actual += 1
        
        if capital_pendiente <= 0 or plazo_restante <= 0:
            break
        
        # Get current Euribor and calculate rate
        euribor_actual = euribor_scenario[mes - 1]
        tasa_anual_actual = euribor_actual + spread
        
        # Recalculate payment annually
        if mes % 12 == 1 and mes > 1 and plazo_restante > 0:
            cuota_mensual_fija = cuota_mensual(capital_pendiente, tasa_anual_actual, plazo_restante)
        
        # Check for injections
        inyeccion_mes = 0
        tipo_inyeccion_mes = None
        for inyeccion in inyecciones:
            if inyeccion['mes_inyeccion'] == mes_actual:
                inyeccion_mes = inyeccion['capital_inyectado']
                tipo_inyeccion_mes = inyeccion['tipo_inyeccion']
        
        # Apply injection
        if inyeccion_mes > 0:
            if inyeccion_mes > capital_pendiente:
                inyeccion_mes = capital_pendiente
            capital_pendiente -= inyeccion_mes
        
        if capital_pendiente <= 0:
            registros.append({
                'Mes': mes_actual,
                'Euribor': euribor_actual,
                'Tasa_Anual': tasa_anual_actual,
                'Capital_pendiente': 0,
                'Cuota_mensual': 0,
                'Intereses_mensuales': 0,
                'Amortizacion_mensual': 0,
                'Inyeccion_capital': inyeccion_mes
            })
            break
        
        interes = intereses_mensuales(capital_pendiente, tasa_anual_actual)
        amortizacion = min(cuota_mensual_fija - interes, capital_pendiente)
        
        registros.append({
            'Mes': mes_actual,
            'Euribor': euribor_actual,
            'Tasa_Anual': tasa_anual_actual,
            'Capital_pendiente': capital_pendiente,
            'Cuota_mensual': cuota_mensual_fija,
            'Intereses_mensuales': interes,
            'Amortizacion_mensual': amortizacion,
            'Inyeccion_capital': inyeccion_mes
        })
        
        capital_pendiente -= amortizacion
        plazo_restante -= 1
        
        # Recalculate after injection
        if (inyeccion_mes > 0 or tipo_inyeccion_mes) and capital_pendiente > 0:
            if tipo_inyeccion_mes:
                opcion_reduccion_actual = tipo_inyeccion_mes
            
            if opcion_reduccion_actual == 'cuota':
                plazo_restante_recalculo = max(plazo_inicial - mes_actual, 1)
                if plazo_restante_recalculo > 0:
                    cuota_mensual_fija = cuota_mensual(capital_pendiente, tasa_anual_actual, plazo_restante_recalculo)
            elif opcion_reduccion_actual == 'plazo':
                nuevo_plazo = calcular_plazo(capital_pendiente, tasa_anual_actual, cuota_mensual_fija)
                if nuevo_plazo > 0:
                    plazo_restante = nuevo_plazo
    
    return pd.DataFrame(registros)

def run_monte_carlo_simulation(capital_inicial, spread, plazo_anos, initial_euribor, 
                              distribution_type, num_simulations, inyecciones=None, **dist_params):
    """Run Monte Carlo simulation for variable mortgage"""
    if inyecciones is None:
        inyecciones = []
    
    all_simulations = []
    
    for i in range(num_simulations):
        # Generate Euribor scenario
        euribor_scenario = generate_euribor_scenario(
            initial_euribor, plazo_anos, distribution_type, **dist_params
        )
        
        # Run mortgage simulation
        df_sim = simulacion_hipoteca_variable_montecarlo(
            capital_inicial, spread, plazo_anos * 12, euribor_scenario, inyecciones
        )
        
        df_sim['Simulation'] = i
        all_simulations.append(df_sim)
    
    return pd.concat(all_simulations, ignore_index=True)

def calculate_simulation_statistics(df_all_sims):
    """Calculate mean and confidence intervals from simulation results"""
    # Group by month and calculate statistics
    stats_df = df_all_sims.groupby('Mes').agg({
        'Cuota_mensual': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Intereses_mensuales': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Amortizacion_mensual': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Euribor': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)]
    }).round(2)
    
    # Flatten column names
    stats_df.columns = ['_'.join(col).strip() for col in stats_df.columns.values]
    stats_df = stats_df.reset_index()
    
    return stats_df