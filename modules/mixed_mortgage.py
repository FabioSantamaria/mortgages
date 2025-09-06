import numpy as np
import pandas as pd
from .calculations import cuota_mensual, intereses_mensuales, calcular_plazo
from .monte_carlo import generate_euribor_scenario

def simulacion_hipoteca_mixta(capital_inicial, tasa_fija, spread, plazo_inicial, 
                               anos_fijos, euribor_scenario, inyecciones=None):
    """
    Simulate mixed mortgage with fixed rate for initial years and variable rate for remaining years
    
    Parameters:
    - capital_inicial: Initial loan amount
    - tasa_fija: Fixed interest rate for initial years (%)
    - spread: Spread over Euribor for variable period (%)
    - plazo_inicial: Total loan term in months
    - anos_fijos: Number of years with fixed rate (3-10)
    - euribor_scenario: List of Euribor values for each month
    - inyecciones: List of capital injections (optional)
    """
    if inyecciones is None:
        inyecciones = []
    
    registros = []
    capital_pendiente = capital_inicial
    mes_actual = 0
    plazo_restante = plazo_inicial
    opcion_reduccion_actual = None
    
    # Calculate initial payment with fixed rate
    cuota_mensual_fija = cuota_mensual(capital_inicial, tasa_fija, plazo_inicial)
    
    # Fixed rate period (first anos_fijos years)
    meses_fijos = anos_fijos * 12
    
    for mes in range(1, min(plazo_inicial + 1, len(euribor_scenario) + 1)):
        mes_actual += 1
        
        if capital_pendiente <= 0 or plazo_restante <= 0:
            break
        
        # Determine current interest rate
        if mes_actual <= meses_fijos:
            # Fixed rate period
            tasa_anual_actual = tasa_fija
            tipo_periodo = "Fijo"
        else:
            # Variable rate period
            euribor_actual = euribor_scenario[mes - 1]
            tasa_anual_actual = euribor_actual + spread
            tipo_periodo = "Variable"
            
            # Recalculate payment when transitioning to variable rate or annually during variable period
            if mes_actual == meses_fijos + 1:  # First month of variable period
                cuota_mensual_fija = cuota_mensual(capital_pendiente, tasa_anual_actual, plazo_restante)
            elif (mes_actual - meses_fijos) % 12 == 1 and mes_actual > meses_fijos + 1:  # Annual recalculation
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
                'Tipo_Periodo': tipo_periodo,
                'Euribor': euribor_scenario[mes - 1] if mes <= len(euribor_scenario) else 0,
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
            'Tipo_Periodo': tipo_periodo,
            'Euribor': euribor_scenario[mes - 1] if mes <= len(euribor_scenario) else 0,
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

def run_mixed_monte_carlo_simulation(capital_inicial, tasa_fija, spread, plazo_anos, 
                                    anos_fijos, initial_euribor, distribution_type, 
                                    num_simulations, inyecciones=None, **dist_params):
    """
    Run Monte Carlo simulation for mixed mortgage (fixed + variable rates)
    
    Parameters:
    - capital_inicial: Initial loan amount
    - tasa_fija: Fixed interest rate for initial years (%)
    - spread: Spread over Euribor for variable period (%)
    - plazo_anos: Total loan term in years
    - anos_fijos: Number of years with fixed rate (3-10)
    - initial_euribor: Initial Euribor rate (%)
    - distribution_type: Type of Euribor distribution
    - num_simulations: Number of Monte Carlo simulations
    - inyecciones: List of capital injections (optional)
    - **dist_params: Distribution parameters
    """
    if inyecciones is None:
        inyecciones = []
    
    all_simulations = []
    
    for i in range(num_simulations):
        # Generate Euribor scenario
        euribor_scenario = generate_euribor_scenario(
            initial_euribor, plazo_anos, distribution_type, **dist_params
        )
        
        # Run mixed mortgage simulation
        df_sim = simulacion_hipoteca_mixta(
            capital_inicial, tasa_fija, spread, plazo_anos * 12, 
            anos_fijos, euribor_scenario, inyecciones
        )
        
        df_sim['Simulation'] = i
        all_simulations.append(df_sim)
    
    return pd.concat(all_simulations, ignore_index=True)

def calculate_mixed_simulation_statistics(df_all_sims):
    """
    Calculate mean and confidence intervals from mixed mortgage simulation results
    """
    # Group by month and calculate statistics
    stats_df = df_all_sims.groupby('Mes').agg({
        'Cuota_mensual': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Intereses_mensuales': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Amortizacion_mensual': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Euribor': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Tasa_Anual': ['mean', 'std', lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95)],
        'Tipo_Periodo': lambda x: x.iloc[0]  # Get the period type (should be same for all sims at same month)
    }).round(2)
    
    # Flatten column names
    stats_df.columns = ['_'.join(col).strip() for col in stats_df.columns.values]
    stats_df = stats_df.reset_index()
    
    return stats_df

def compare_mixed_vs_variable_mortgage(capital_inicial, tasa_fija, spread, plazo_anos, 
                                      anos_fijos, initial_euribor, distribution_type, 
                                      num_simulations, inyecciones=None, **dist_params):
    """
    Compare mixed mortgage vs pure variable mortgage
    
    Returns comparison statistics and DataFrames for both mortgage types
    """
    # Run mixed mortgage simulation
    mixed_results = run_mixed_monte_carlo_simulation(
        capital_inicial, tasa_fija, spread, plazo_anos, anos_fijos,
        initial_euribor, distribution_type, num_simulations, inyecciones, **dist_params
    )
    
    # Run pure variable mortgage simulation (using monte_carlo module)
    from .monte_carlo import run_monte_carlo_simulation
    variable_results = run_monte_carlo_simulation(
        capital_inicial, spread, plazo_anos, initial_euribor,
        distribution_type, num_simulations, inyecciones, **dist_params
    )
    
    # Calculate statistics for both
    mixed_stats = calculate_mixed_simulation_statistics(mixed_results)
    
    # Calculate comparison metrics
    mixed_sims = [group for _, group in mixed_results.groupby('Simulation')]
    variable_sims = [group for _, group in variable_results.groupby('Simulation')]
    
    mixed_total_interests = [df['Intereses_mensuales'].sum() for df in mixed_sims]
    variable_total_interests = [df['Intereses_mensuales'].sum() for df in variable_sims]
    
    mixed_durations = [len(df) for df in mixed_sims]
    variable_durations = [len(df) for df in variable_sims]
    
    comparison = {
        'mixed_avg_interest': np.mean(mixed_total_interests),
        'variable_avg_interest': np.mean(variable_total_interests),
        'interest_difference': np.mean(variable_total_interests) - np.mean(mixed_total_interests),
        'mixed_avg_duration': np.mean(mixed_durations) / 12,
        'variable_avg_duration': np.mean(variable_durations) / 12,
        'duration_difference': (np.mean(variable_durations) - np.mean(mixed_durations)) / 12
    }
    
    return {
        'comparison': comparison,
        'mixed_results': mixed_results,
        'variable_results': variable_results,
        'mixed_stats': mixed_stats
    }