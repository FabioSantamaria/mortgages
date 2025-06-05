import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math
import numpy as np
from scipy import stats

# Core calculation functions from your notebook
def cuota_mensual(capital, tasa, plazo):
    """Calculate monthly payment"""
    if plazo <= 0:
        raise ValueError("El plazo debe ser mayor a 0 meses")
    if capital <= 0:
        return 0
    
    tasa_mensual = tasa / 1200
    return (capital * tasa_mensual) / (1 - (1 + tasa_mensual)**-plazo)

def intereses_mensuales(capital_pendiente, tasa):
    """Calculate monthly interest"""
    tasa_mensual = tasa / 1200
    return capital_pendiente * tasa_mensual

def calcular_plazo(capital, tasa, cuota):
    """Calculate remaining months to pay the loan"""
    if capital <= 0:
        return 0
    
    tasa_mensual = tasa / 1200
    if cuota <= capital * tasa_mensual:
        raise ValueError("La cuota no cubre los intereses mínimos")
    
    plazo = -math.log(1 - capital * tasa_mensual / cuota) / math.log(1 + tasa_mensual)
    return max(math.ceil(plazo), 1)

def maximo_precio_piso_segun_sueldo(sueldo_neto_mensual, relacion_cuota_sueldo, 
                                    porcentaje_entrada, tasa_interes, plazo):
    """Calculate maximum house price based on salary"""
    exponencial = (1. + tasa_interes / (12. * 100.))**(-plazo)
    factor = tasa_interes / (12. * 100.) * 1. / (1. - exponencial)
    cuota_mensual = sueldo_neto_mensual * relacion_cuota_sueldo
    capital_pendiente = cuota_mensual / factor
    precio_piso = capital_pendiente / (1. - porcentaje_entrada / 100.)
    return precio_piso

def simulacion_hipoteca_simple(capital_inicial, tasa, plazo_inicial, cuota_inicial):
    """Simple mortgage simulation"""
    if capital_inicial <= 0:
        raise ValueError("El capital inicial debe ser positivo")
    if plazo_inicial <= 0:
        raise ValueError("El plazo inicial debe ser positivo")
    if cuota_inicial <= 0:
        raise ValueError("La cuota inicial debe ser positiva")
    
    registros = []
    capital_pendiente = capital_inicial
    cuota_mensual_fija = cuota_inicial
    mes_actual = 0
    
    for mes in range(1, plazo_inicial + 1):
        mes_actual += 1
        
        if capital_pendiente <= 0:
            break
        
        interes = intereses_mensuales(capital_pendiente, tasa)
        amortizacion = min(cuota_mensual_fija - interes, capital_pendiente)
        
        registros.append({
            'Mes': mes_actual,
            'Capital_pendiente': capital_pendiente,
            'Cuota_mensual': cuota_mensual_fija,
            'Intereses_mensuales': interes,
            'Amortizacion_mensual': amortizacion
        })
        
        capital_pendiente -= amortizacion
    
    return pd.DataFrame(registros)

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

def plot_monte_carlo_results(stats_df):
    """Create plot with mean values and confidence bands"""
    fig = go.Figure()
    
    # Monthly payment
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Cuota_mensual_mean'],
        mode='lines',
        name='Cuota Mensual (Media)',
        line=dict(color='blue', width=2)
    ))
    
    # Upper bound for monthly payment
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Cuota_mensual_<lambda_1>'],
        mode='lines',
        line=dict(color='rgba(0,100,80,0.2)'),
        showlegend=False
    ))
    
    # Lower bound for monthly payment
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Cuota_mensual_<lambda_0>'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,0.2)'),
        name='Cuota Mensual (90% CI)'
    ))
    
    # Monthly interest
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Intereses_mensuales_mean'],
        mode='lines',
        name='Intereses Mensuales (Media)',
        line=dict(color='red', width=2)
    ))
    
    # Upper bound for interest
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Intereses_mensuales_<lambda_1>'],
        mode='lines',
        line=dict(color='rgba(255,0,0,0.2)'),
        showlegend=False
    ))
    
    # Lower bound for interest
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Intereses_mensuales_<lambda_0>'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='rgba(255,0,0,0.2)'),
        name='Intereses Mensuales (90% CI)'
    ))
    
    # Monthly amortization
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Amortizacion_mensual_mean'],
        mode='lines',
        name='Amortización Mensual (Media)',
        line=dict(color='green', width=2)
    ))
    
    # Upper bound for amortization
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Amortizacion_mensual_<lambda_1>'],
        mode='lines',
        line=dict(color='rgba(0,255,0,0.2)'),
        showlegend=False
    ))
    
    # Lower bound for amortization
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Amortizacion_mensual_<lambda_0>'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.2)',
        line=dict(color='rgba(0,255,0,0.2)'),
        name='Amortización Mensual (90% CI)'
    ))
    
    fig.update_layout(
        title='Simulación Monte Carlo - Hipoteca Variable con Euribor Estocástico',
        xaxis_title='Mes',
        yaxis_title='Importe (€)',
        hovermode='x unified',
        legend=dict(
            # yanchor="top",
            # y=0.99,
            # xanchor="left",
            # x=0.01
        )
    )
    
    return fig

def plot_euribor_evolution(stats_df):
    """Plot Euribor evolution with confidence bands"""
    fig = go.Figure()
    
    # Mean Euribor
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Euribor_mean'],
        mode='lines',
        name='Euribor Medio',
        line=dict(color='purple', width=2)
    ))

    # Upper bound for Euribor
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Euribor_<lambda_1>'],
        mode='lines',
        line=dict(color='rgba(128,0,128,0.2)'),
        showlegend=False
    ))

    # Lower bound for Euribor
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Euribor_<lambda_0>'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(128,0,128,0.2)',
        line=dict(color='rgba(128,0,128,0.2)'),
        name='Euribor (90% CI)'
    ))
    
    fig.update_layout(
        title='Evolución del Euribor - Simulación Monte Carlo',
        xaxis_title='Mes',
        yaxis_title='Euribor (%)',
        hovermode='x unified'
    )
    
    return fig

def simulacion_hipoteca_multiple_inyeccion(capital_inicial, tasa, plazo_inicial,
                                            cuota_inicial, inyecciones):
    """
    Simulación robusta de hipoteca con múltiples inyecciones de capital y tipos de reducción
    definidos para cada inyección a lo largo del tiempo.
    """
    # Validaciones iniciales generales
    if capital_inicial <= 0:
        raise ValueError("El capital inicial debe ser positivo")
    if plazo_inicial <= 0:
        raise ValueError("El plazo inicial debe ser positivo")
    if cuota_inicial <= 0:
        raise ValueError("La cuota inicial debe ser positiva")

    # Validaciones de las inyecciones
    if not isinstance(inyecciones, list):
        raise TypeError("Las inyecciones deben ser una lista de diccionarios")
    
    opcion_reduccion_actual = None
    for inyeccion in inyecciones:
        if not isinstance(inyeccion, dict):
            raise TypeError("Cada inyección debe ser un diccionario")
        if 'mes_inyeccion' not in inyeccion:
            raise ValueError("Cada inyección debe tener 'mes_inyeccion'")
        if 'capital_inyectado' not in inyeccion:
            inyeccion['capital_inyectado'] = 0 # Asumir 0 si no se especifica
        if 'tipo_inyeccion' in inyeccion and inyeccion['tipo_inyeccion'] not in ['cuota', 'plazo']:
            raise ValueError("Tipo de inyección debe ser 'cuota' o 'plazo' o None")

    registros = []
    capital_pendiente = capital_inicial
    cuota_actual = cuota_inicial
    plazo_restante = plazo_inicial
    mes_actual = 0

    for mes in range(1, plazo_inicial + 1):
        mes_actual += 1

        # Verificar si hay inyección/acción este mes
        inyeccion_mes = 0
        tipo_inyeccion_mes = None
        for inyeccion in inyecciones:
            if inyeccion['mes_inyeccion'] == mes_actual:
                inyeccion_mes = inyeccion['capital_inyectado']
                tipo_inyeccion_mes = inyeccion['tipo_inyeccion']

        # Aplicar inyección si existe y validar que no supere el capital restante
        if inyeccion_mes > 0:
            if inyeccion_mes > capital_pendiente:
                raise ValueError(f"Inyección en el mes {mes_actual} supera el capital pendiente.")
            capital_pendiente -= inyeccion_mes

        if capital_pendiente <= 0:
            registros.append({
                'Mes': mes_actual,
                'Capital_pendiente': 0,
                'Cuota_mensual': 0,
                'Intereses_mensuales': 0,
                'Amortizacion_mensual': 0,
                'Inyeccion_capital': inyeccion_mes,
                'Tipo_Reduccion': tipo_inyeccion_mes if tipo_inyeccion_mes else opcion_reduccion_actual
            })
            break

        interes = intereses_mensuales(capital_pendiente, tasa)
        amortizacion = min(cuota_actual - interes, capital_pendiente)

        registros.append({
            'Mes': mes_actual,
            'Capital_pendiente': capital_pendiente,
            'Cuota_mensual': cuota_actual,
            'Intereses_mensuales': interes,
            'Amortizacion_mensual': amortizacion,
            'Inyeccion_capital': inyeccion_mes,
            'Tipo_Reduccion': tipo_inyeccion_mes if tipo_inyeccion_mes else opcion_reduccion_actual
        })

        capital_pendiente -= amortizacion

        # Recalcular cuota o plazo si hubo inyección o cambio de tipo y aún queda préstamo
        if (inyeccion_mes > 0 or tipo_inyeccion_mes) and capital_pendiente > 0:
            if tipo_inyeccion_mes:
                opcion_reduccion_actual = tipo_inyeccion_mes

            nuevo_capital = capital_pendiente

            if opcion_reduccion_actual == 'cuota':
                plazo_restante_recalculo = max(plazo_inicial - mes_actual, 1)
                cuota_actual = cuota_mensual(nuevo_capital, tasa, plazo_restante_recalculo)
            elif opcion_reduccion_actual == 'plazo':
                cuota_actual_recalculo = cuota_actual # Mantenemos la cuota actual RECALCULADA previamente por el euribor
                plazo_restante = calcular_plazo(nuevo_capital, tasa, cuota_actual_recalculo) # Usar la tasa anual ACTUAL
                plazo_inicial = mes_actual + plazo_restante # Ajustamos plazo inicial para futuras inyecciones

    return pd.DataFrame(registros)

def calcular_ahorro_intereses_multiple_inyeccion(capital_inicial, tasa, plazo_inicial,
                                                 cuota_inicial, inyecciones):
    """Calculate total interest savings from multiple injections"""
    # Simulación con inyecciones
    df_con_inyecciones = simulacion_hipoteca_multiple_inyeccion(
        capital_inicial, tasa, plazo_inicial, cuota_inicial, inyecciones)
    intereses_con_inyecciones = df_con_inyecciones['Intereses_mensuales'].sum()

    # Simulación base SIN inyecciones
    df_sin_inyecciones = simulacion_hipoteca_multiple_inyeccion(
        capital_inicial, tasa, plazo_inicial, cuota_inicial, inyecciones=[])
    intereses_sin_inyecciones = df_sin_inyecciones['Intereses_mensuales'].sum()

    ahorro_intereses = intereses_sin_inyecciones - intereses_con_inyecciones
    return ahorro_intereses, intereses_sin_inyecciones, intereses_con_inyecciones

def plot_hipoteca_simple(df_hipoteca_simple):
    """Create interactive plot for mortgage simulation"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_hipoteca_simple['Mes'],
        y=df_hipoteca_simple['Cuota_mensual'],
        mode='lines',
        line=dict(color='blue'),
        name='Cuota Mensual'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_hipoteca_simple['Mes'],
        y=df_hipoteca_simple['Amortizacion_mensual'],
        mode='lines',
        line=dict(color='red'),
        name='Amortización Mensual'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_hipoteca_simple['Mes'],
        y=df_hipoteca_simple['Intereses_mensuales'],
        mode='lines',
        line=dict(color='yellow'),
        name='Intereses Mensuales'
    ))
    
    fig.update_layout(
        title='Simulación de Hipoteca',
        xaxis_title="Mes",
        yaxis_title="Importe (euros)",
        font_family="Arial",
        font_color="black",
        legend=dict(
            #yanchor="top",
            #y=0.99,
            #xanchor="right",
            #x=0.01,
            #bgcolor="black",
            #bordercolor="black",
            #borderwidth=1
        )
    )
    
    return fig

def plot_comparacion(df_hipoteca_original, df_hipoteca_con_inyecciones):
    """Create comparison plot between original and early payment scenarios"""
    fig = go.Figure()

    # Original (sin inyecciones)
    fig.add_trace(go.Scatter(
        x=df_hipoteca_original['Mes'],
        y=df_hipoteca_original['Amortizacion_mensual'],
        mode='lines',
        line=dict(color='blue', dash='dash'),
        name='Amortización Mensual (Original)'
    ))

    fig.add_trace(go.Scatter(
        x=df_hipoteca_original['Mes'],
        y=df_hipoteca_original['Cuota_mensual'],
        mode='lines',
        line=dict(color='red', dash='dash'),
        name='Cuota Mensual (Original)'
    ))

    fig.add_trace(go.Scatter(
        x=df_hipoteca_original['Mes'],
        y=df_hipoteca_original['Intereses_mensuales'],
        mode='lines',
        line=dict(color='yellow', dash='dash'),
        name='Intereses Mensuales (Original)'
    ))

    # Con inyecciones
    fig.add_trace(go.Scatter(
        x=df_hipoteca_con_inyecciones['Mes'],
        y=df_hipoteca_con_inyecciones['Amortizacion_mensual'],
        mode='lines',
        line=dict(color='blue'),
        name='Amortización Mensual (Con Inyecciones)'
    ))

    fig.add_trace(go.Scatter(
        x=df_hipoteca_con_inyecciones['Mes'],
        y=df_hipoteca_con_inyecciones['Cuota_mensual'],
        mode='lines',
        line=dict(color='red'),
        name='Cuota Mensual (Con Inyecciones)'
    ))

    fig.add_trace(go.Scatter(
        x=df_hipoteca_con_inyecciones['Mes'],
        y=df_hipoteca_con_inyecciones['Intereses_mensuales'],
        mode='lines',
        line=dict(color='yellow'),
        name='Intereses Mensuales (Con Inyecciones)'
    ))

    # Marcar inyecciones
    inyecciones_meses = df_hipoteca_con_inyecciones[df_hipoteca_con_inyecciones['Inyeccion_capital'] > 0]
    if not inyecciones_meses.empty:
        for mes in inyecciones_meses['Mes']:
            fig.add_vline(
                x=mes,
                line_dash="solid",
                line_color="green",
                line_width=2,
                name="Inyecciones de Capital"
            )

    fig.update_layout(
        title='Comparativa: Hipoteca Original vs. Hipoteca con Amortizaciones Anticipadas',
        xaxis_title="Mes",
        yaxis_title="Importe (euros)",
        font_family="Arial",
        font_color="black",
        legend=dict(
            # yanchor="top",
            # y=0.99,
            # xanchor="right",
            # x=0.01,
            # bgcolor="black",
            # bordercolor="black",
            # borderwidth=1
        )
    )
    
    return fig

def calcular_costes_iniciales_estimados(capital_inicial, es_vivienda_nueva=False, 
                                       contratar_gestoria=False, impuesto_ccaa_itp_porcentaje=8.0):
    """Calculate initial costs estimation"""
    costes = {}
    
    # Notaría (0.2% - 0.5% del precio)
    costes['Notaria'] = capital_inicial * 0.003
    
    # Registro (0.1% - 0.3% del precio)
    costes['Registro'] = capital_inicial * 0.002
    
    # Gestoría (opcional)
    if contratar_gestoria:
        costes['Gestoria'] = min(600, capital_inicial * 0.001)
    else:
        costes['Gestoria'] = 0
    
    # Impuestos
    if es_vivienda_nueva:
        # IVA (10%) + AJD (1.2%)
        costes['IVA'] = capital_inicial * 0.10
        costes['AJD'] = capital_inicial * 0.012
        costes['ITP'] = 0
    else:
        # ITP (varía por CCAA, típicamente 6-10%)
        costes['ITP'] = capital_inicial * (impuesto_ccaa_itp_porcentaje / 100)
        costes['IVA'] = 0
        costes['AJD'] = 0
    
    # Tasación (300-600€)
    costes['Tasacion'] = 400
    
    # Comisión apertura banco (0.5% - 1%)
    costes['Comision_apertura'] = capital_inicial * 0.005
    
    return costes

# Streamlit App
st.set_page_config(page_title="Calculadora de Hipotecas", page_icon="🏠", layout="wide")

st.title("🏠 Calculadora de Hipotecas Avanzada")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una opción:",
    ["Máximo precio según sueldo", "Simulación de hipoteca", "Amortizaciones anticipadas", 
     "Monte Carlo - Euribor Estocástico", "Costes iniciales"]
)

if opcion == "Máximo precio según sueldo":
    st.header("💰 Máximo precio de vivienda según sueldo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sueldo_neto = st.number_input("Sueldo neto mensual (€)", min_value=1000, value=4000, step=100)
        relacion_cuota = st.slider("Porcentaje máximo del sueldo para la cuota", 0.2, 0.5, 0.33, 0.01)
        porcentaje_entrada = st.slider("Porcentaje de entrada (%)", 10, 30, 20, 1)
    
    with col2:
        tasa_interes = st.number_input("Tasa de interés anual (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.1)
        plazo_anos = st.slider("Plazo del préstamo (años)", 10, 40, 30, 1)
    
    if st.button("Calcular precio máximo"):
        precio_maximo = maximo_precio_piso_segun_sueldo(
            sueldo_neto, relacion_cuota, porcentaje_entrada, tasa_interes, plazo_anos * 12
        )
        
        st.success(f"**Precio máximo de vivienda: {precio_maximo:,.0f} €**")
        
        # Desglose
        entrada_necesaria = precio_maximo * (porcentaje_entrada / 100)
        capital_prestamo = precio_maximo - entrada_necesaria
        cuota_mensual_calc = cuota_mensual(capital_prestamo, tasa_interes, plazo_anos * 12)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Entrada necesaria", f"{entrada_necesaria:,.0f} €")
        with col2:
            st.metric("Capital del préstamo", f"{capital_prestamo:,.0f} €")
        with col3:
            st.metric("Cuota mensual", f"{cuota_mensual_calc:,.0f} €")

elif opcion == "Simulación de hipoteca":
    st.header("📊 Simulación de hipoteca")
    
    col1, col2 = st.columns(2)
    
    with col1:
        capital_inicial = st.number_input("Capital inicial (€)", min_value=10000, value=200000, step=5000)
        tasa_anual = st.number_input("Tasa de interés anual (%)", min_value=0.5, max_value=10.0, value=3.22, step=0.01)
    
    with col2:
        plazo_anos = st.slider("Plazo del préstamo (años)", 5, 40, 20, 1)
        mostrar_tabla = st.checkbox("Mostrar tabla detallada")
    
    if st.button("Simular hipoteca"):
        plazo_meses = plazo_anos * 12
        cuota_inicial = cuota_mensual(capital_inicial, tasa_anual, plazo_meses)
        
        # Simulación
        df_simulacion = simulacion_hipoteca_simple(capital_inicial, tasa_anual, plazo_meses, cuota_inicial)
        intereses_totales = df_simulacion['Intereses_mensuales'].sum()
        total_pagado = intereses_totales + capital_inicial
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cuota mensual", f"{cuota_inicial:,.2f} €")
        with col2:
            st.metric("Intereses totales", f"{intereses_totales:,.2f} €")
        with col3:
            st.metric("Total a pagar", f"{total_pagado:,.2f} €")
        with col4:
            st.metric("% Intereses", f"{(intereses_totales/capital_inicial)*100:.1f}%")
        
        # Gráfico
        fig = plot_hipoteca_simple(df_simulacion)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla detallada (opcional)
        if mostrar_tabla:
            st.subheader("Tabla de amortización")
            # Mostrar solo los primeros 12 meses y últimos 12 meses
            df_display = pd.concat([
                df_simulacion.head(12),
                pd.DataFrame([{"Mes": "...", "Capital_pendiente": "...", "Cuota_mensual": "...", 
                             "Intereses_mensuales": "...", "Amortizacion_mensual": "..."}]),
                df_simulacion.tail(12)
            ]).reset_index(drop=True)
            
            st.dataframe(df_display, use_container_width=True)

elif opcion == "Amortizaciones anticipadas":
    st.header("💸 Simulación con Amortizaciones Anticipadas (Inyecciones)")
    
    # Parámetros básicos de la hipoteca
    st.subheader("Parámetros de la hipoteca")
    col1, col2 = st.columns(2)
    
    with col1:
        capital_inicial = st.number_input("Capital inicial (€)", min_value=10000, value=200000, step=5000, key="capital_inyec")
        tasa_anual = st.number_input("Tasa de interés anual (%)", min_value=0.5, max_value=10.0, value=3.22, step=0.01, key="tasa_inyec")
    
    with col2:
        plazo_anos = st.slider("Plazo del préstamo (años)", 5, 40, 20, 1, key="plazo_inyec")
    
    # Configuración de inyecciones
    st.subheader("Configuración de amortizaciones anticipadas")
    
    # Inicializar session state para inyecciones
    if 'inyecciones' not in st.session_state:
        st.session_state.inyecciones = []
    
    # Formulario para agregar inyecciones
    with st.expander("➕ Agregar nueva amortización anticipada"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            mes_inyeccion = st.number_input("Mes de la inyección", min_value=1, max_value=plazo_anos*12, value=48, step=1)
        with col2:
            capital_inyectado = st.number_input("Capital a inyectar (€)", min_value=100, value=20000, step=100)
        with col3:
            tipo_inyeccion = st.selectbox("Tipo de reducción", ["cuota", "plazo"])
        with col4:
            st.write("")
            st.write("")
            if st.button("Agregar inyección"):
                # Check if there's already an injection for this month
                mes_exists = any(inj['mes_inyeccion'] == mes_inyeccion for inj in st.session_state.inyecciones)
                
                if mes_exists:
                    st.error(f"Ya existe una inyección para el mes {mes_inyeccion}")
                else:
                    nueva_inyeccion = {
                        'mes_inyeccion': mes_inyeccion,
                        'capital_inyectado': capital_inyectado,
                        'tipo_inyeccion': tipo_inyeccion
                    }
                    st.session_state.inyecciones.append(nueva_inyeccion)
                    st.success("Inyección agregada!")
    
    # Mostrar inyecciones actuales
    if st.session_state.inyecciones:
        st.subheader("Amortizaciones anticipadas configuradas:")
        
        # Crear DataFrame para mostrar las inyecciones
        df_inyecciones = pd.DataFrame(st.session_state.inyecciones)
        df_inyecciones['Capital (€)'] = df_inyecciones['capital_inyectado'].apply(lambda x: f"{x:,.0f}")
        df_inyecciones['Mes'] = df_inyecciones['mes_inyeccion']
        df_inyecciones['Tipo'] = df_inyecciones['tipo_inyeccion']
        
        # Mostrar tabla
        st.dataframe(df_inyecciones[['Mes', 'Capital (€)', 'Tipo']], use_container_width=True, hide_index=True)
        
        # Botón para limpiar inyecciones
        if st.button("🗑️ Limpiar todas las inyecciones"):
            st.session_state.inyecciones = []
            st.rerun()
    
    # Botón para simular
    if st.button("🚀 Simular con amortizaciones anticipadas"):
        if not st.session_state.inyecciones:
            st.warning("Agrega al menos una amortización anticipada para comparar.")
        else:
            plazo_meses = plazo_anos * 12
            cuota_inicial = cuota_mensual(capital_inicial, tasa_anual, plazo_meses)
            
            try:
                # Simulación original (sin inyecciones)
                df_original = simulacion_hipoteca_multiple_inyeccion(
                    capital_inicial, tasa_anual, plazo_meses, cuota_inicial, [])
                
                # Simulación con inyecciones
                df_con_inyecciones = simulacion_hipoteca_multiple_inyeccion(
                    capital_inicial, tasa_anual, plazo_meses, cuota_inicial, st.session_state.inyecciones)
                
                # Calcular ahorros
                ahorro_total, intereses_sin, intereses_con = calcular_ahorro_intereses_multiple_inyeccion(
                    capital_inicial, tasa_anual, plazo_meses, cuota_inicial, st.session_state.inyecciones)
                
                # Métricas de comparación
                st.subheader("📈 Resultados de la simulación")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Ahorro en intereses", f"{ahorro_total:,.2f} €")
                with col2:
                    st.metric("Intereses originales", f"{intereses_sin:,.2f} €")
                with col3:
                    st.metric("Intereses con inyecciones", f"{intereses_con:,.2f} €")
                with col4:
                    porcentaje_ahorro = (ahorro_total / intereses_sin) * 100 if intereses_sin > 0 else 0
                    st.metric("% Ahorro", f"{porcentaje_ahorro:.1f}%")
                
                # Gráfico de comparación
                fig_comparacion = plot_comparacion(df_original, df_con_inyecciones)
                st.plotly_chart(fig_comparacion, use_container_width=True)
                
                # Información adicional
                st.subheader("ℹ️ Información adicional")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Hipoteca original:**")
                    st.write(f"- Duración: {len(df_original)} meses ({len(df_original)/12:.1f} años)")
                    st.write(f"- Total pagado: {intereses_sin + capital_inicial:,.2f} €")
                
                with col2:
                    st.write("**Hipoteca con inyecciones:**")
                    st.write(f"- Duración: {len(df_con_inyecciones)} meses ({len(df_con_inyecciones)/12:.1f} años)")
                    st.write(f"- Total pagado: {intereses_con + capital_inicial + sum([inj['capital_inyectado'] for inj in st.session_state.inyecciones]):,.2f} €")
                    meses_ahorrados = len(df_original) - len(df_con_inyecciones)
                    st.write(f"- Tiempo ahorrado: {meses_ahorrados} meses ({meses_ahorrados/12:.1f} años)")
                
            except Exception as e:
                st.error(f"Error en la simulación: {str(e)}")

elif opcion == "Monte Carlo - Euribor Estocástico":
    st.header("🎲 Simulación Monte Carlo - Euribor Estocástico")
    
    # Parámetros básicos de la hipoteca
    st.subheader("Parámetros de la hipoteca")
    col1, col2 = st.columns(2)
    
    with col1:
        capital_inicial = st.number_input("Capital inicial (€)", min_value=10000, value=200000, step=5000, key="capital_mc")
        spread = st.number_input("Spread sobre Euribor (%)", min_value=0.1, max_value=5.0, value=1.5, step=0.1, key="spread_mc")
    
    with col2:
        plazo_anos = st.slider("Plazo del préstamo (años)", 5, 40, 20, 1, key="plazo_mc")
        num_simulaciones = st.slider("Número de simulaciones", 10, 1000, 100, 10, key="num_sim")
    
    # Configuración del Euribor
    st.subheader("Configuración del Euribor")
    col1, col2 = st.columns(2)
    
    with col1:
        initial_euribor = st.number_input("Euribor inicial (%)", min_value=-1.0, max_value=10.0, value=3.5, step=0.1, key="euribor_inicial")
        distribution_type = st.selectbox(
            "Tipo de distribución",
            ["Gaussian", "Mean Reverting", "Uniform Random Walk", "Constant"],
            key="dist_type"
        )
    
    with col2:
        if distribution_type == "Gaussian":
            volatility = st.slider("Volatilidad anual (%)", 0.1, 2.0, 0.5, 0.1, key="volatility")
            drift = st.slider("Deriva anual (%)", -1.0, 1.0, 0.0, 0.1, key="drift")
            dist_params = {"volatility": volatility, "drift": drift}
        elif distribution_type == "Mean Reverting":
            mean_level = st.slider("Nivel medio (%)", 0.0, 8.0, 3.0, 0.1, key="mean_level")
            reversion_speed = st.slider("Velocidad de reversión", 0.1, 1.0, 0.3, 0.1, key="reversion_speed")
            volatility = st.slider("Volatilidad (%)", 0.1, 2.0, 0.5, 0.1, key="volatility_mr")
            dist_params = {"mean_level": mean_level, "reversion_speed": reversion_speed, "volatility": volatility}
        elif distribution_type == "Uniform Random Walk":
            max_change = st.slider("Cambio máximo por mes (%)", 0.1, 1.0, 0.3, 0.1, key="max_change")
            dist_params = {"max_change": max_change}
        else:  # Constant
            dist_params = {}
    
    # Configuración de inyecciones (opcional)
    st.subheader("Amortizaciones anticipadas (opcional)")
    
    # Inicializar session state para inyecciones MC
    if 'inyecciones_mc' not in st.session_state:
        st.session_state.inyecciones_mc = []
    
    with st.expander("➕ Agregar amortización anticipada"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            mes_inyeccion_mc = st.number_input("Mes", min_value=1, max_value=plazo_anos*12, value=48, step=1, key="mes_mc")
        with col2:
            capital_inyectado_mc = st.number_input("Capital (€)", min_value=100, value=20000, step=100, key="capital_inj_mc")
        with col3:
            tipo_inyeccion_mc = st.selectbox("Tipo", ["cuota", "plazo"], key="tipo_mc")
        with col4:
            st.write("")
            st.write("")
            if st.button("Agregar", key="add_mc"):
                # Check if there's already an injection for this month
                mes_exists = any(inj['mes_inyeccion'] == mes_inyeccion_mc for inj in st.session_state.inyecciones_mc)
                
                if mes_exists:
                    st.error(f"Ya existe una inyección para el mes {mes_inyeccion_mc}")
                else:
                    nueva_inyeccion = {
                        'mes_inyeccion': mes_inyeccion_mc,
                        'capital_inyectado': capital_inyectado_mc,
                        'tipo_inyeccion': tipo_inyeccion_mc
                    }
                    st.session_state.inyecciones_mc.append(nueva_inyeccion)
                    st.success("Inyección agregada!")
    
    # Mostrar inyecciones configuradas
    if st.session_state.inyecciones_mc:
        st.write("**Amortizaciones configuradas:**")
        df_inj_mc = pd.DataFrame(st.session_state.inyecciones_mc)
        st.dataframe(df_inj_mc[['mes_inyeccion', 'capital_inyectado', 'tipo_inyeccion']], 
                    use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Limpiar inyecciones", key="clear_mc"):
            st.session_state.inyecciones_mc = []
            st.rerun()
    
    # Ejecutar simulación
    if st.button("🚀 Ejecutar simulación Monte Carlo", key="run_mc"):
        with st.spinner("Ejecutando simulaciones..."):
            try:
                # Ejecutar simulaciones
                all_results = run_monte_carlo_simulation(
                    capital_inicial=capital_inicial,
                    spread=spread, 
                    plazo_anos=plazo_anos,
                    initial_euribor=initial_euribor,
                    distribution_type=distribution_type,
                    num_simulations=num_simulaciones,
                    inyecciones=st.session_state.inyecciones_mc if st.session_state.inyecciones_mc else None,
                    **dist_params
                )
                
                # Split the DataFrame into list of DataFrames by simulation number
                simulation_dfs = [group for _, group in all_results.groupby('Simulation')]
                
                # Calcular estadísticas
                stats_df = calculate_simulation_statistics(all_results)
                
                # Métricas resumen
                st.subheader("📊 Resumen de resultados")
                
                duraciones = [len(df) for df in simulation_dfs]
                intereses_totales = [df['Intereses_mensuales'].sum() for df in simulation_dfs]
                pagos_iniciales = [df['Cuota_mensual'].iloc[0] for df in simulation_dfs]
                euribor_final = [df['Euribor'].iloc[-1] for df in simulation_dfs]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Duración promedio", f"{np.mean(duraciones)/12:.1f} años")
                with col2:
                    st.metric("Intereses totales promedio", f"{np.mean(intereses_totales):,.0f} €")
                with col3:
                    st.metric("Pago inicial promedio", f"{np.mean(pagos_iniciales):,.0f} €")
                with col4:
                    st.metric("Euribor final promedio", f"{np.mean(euribor_final):.2f}%")
                
                # Gráficos
                st.subheader("📈 Evolución de pagos")
                fig_payments = plot_monte_carlo_results(stats_df)
                st.plotly_chart(fig_payments, use_container_width=True)
                
                st.subheader("📈 Evolución del Euribor")
                fig_euribor = plot_euribor_evolution(stats_df)
                st.plotly_chart(fig_euribor, use_container_width=True)
                
                # Estadísticas detalladas
                st.subheader("📋 Estadísticas detalladas")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Intereses totales:**")
                    st.write(f"- Media: {np.mean(intereses_totales):,.0f} €")
                    st.write(f"- Mediana: {np.median(intereses_totales):,.0f} €")
                    st.write(f"- Desv. estándar: {np.std(intereses_totales):,.0f} €")
                    st.write(f"- Percentil 5: {np.percentile(intereses_totales, 5):,.0f} €")
                    st.write(f"- Percentil 95: {np.percentile(intereses_totales, 95):,.0f} €")
                
                with col2:
                    st.write("**Duración del préstamo:**")
                    st.write(f"- Media: {np.mean(duraciones)/12:.1f} años")
                    st.write(f"- Mediana: {np.median(duraciones)/12:.1f} años")
                    st.write(f"- Desv. estándar: {np.std(duraciones)/12:.1f} años")
                    st.write(f"- Percentil 5: {np.percentile(duraciones, 5)/12:.1f} años")
                    st.write(f"- Percentil 95: {np.percentile(duraciones, 95)/12:.1f} años")
                
                # Análisis de riesgo
                st.subheader("⚠️ Análisis de riesgo")
                
                percentiles = [10, 25, 50, 75, 90]
                risk_data = []
                for p in percentiles:
                    risk_data.append({
                        "Percentil": f"P{p}",
                        "Intereses totales (€)": f"{np.percentile(intereses_totales, p):,.0f}",
                        "Duración (años)": f"{np.percentile(duraciones, p)/12:.1f}"
                    })
                
                df_risk = pd.DataFrame(risk_data)
                st.dataframe(df_risk, use_container_width=True, hide_index=True)
                
                # Mostrar algunas simulaciones individuales
                if st.checkbox("Mostrar simulaciones individuales (muestra)"):
                    st.subheader("🔍 Simulaciones individuales (muestra)")
                    
                    num_mostrar = min(5, len(simulation_dfs))
                    indices_muestra = np.random.choice(len(simulation_dfs), num_mostrar, replace=False)
                    
                    fig_individual = go.Figure()
                    
                    for i, idx in enumerate(indices_muestra):
                        df_sim = simulation_dfs[idx]
                        fig_individual.add_trace(go.Scatter(
                            x=df_sim.index + 1,
                            y=df_sim['Cuota_mensual'],
                            mode='lines',
                            name=f'Simulación {idx+1}',
                            opacity=0.7
                        ))
                    
                    fig_individual.update_layout(
                        title='Muestra de simulaciones individuales - Cuota mensual',
                        xaxis_title='Mes',
                        yaxis_title='Cuota mensual (€)',
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_individual, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error en la simulación: {str(e)}")
                st.write("Detalles del error:")
                st.code(str(e))

elif opcion == "Costes iniciales":
    st.header("💸 Estimación de costes iniciales")
    
    col1, col2 = st.columns(2)
    
    with col1:
        precio_vivienda = st.number_input("Precio de la vivienda (€)", min_value=50000, value=300000, step=10000)
        es_nueva = st.checkbox("¿Es vivienda nueva?")
        contratar_gestoria = st.checkbox("¿Contratar gestoría?")
    
    with col2:
        if not es_nueva:
            itp_porcentaje = st.slider("ITP de tu comunidad autónoma (%)", 6.0, 10.0, 8.0, 0.5)
        else:
            itp_porcentaje = 8.0
    
    if st.button("Calcular costes"):
        costes = calcular_costes_iniciales_estimados(
            precio_vivienda, es_nueva, contratar_gestoria, itp_porcentaje
        )
        
        total_costes = sum(costes.values())
        
        st.success(f"**Total costes iniciales estimados: {total_costes:,.2f} €**")
        
        # Desglose de costes
        st.subheader("Desglose de costes:")
        
        costes_df = pd.DataFrame([
            {"Concepto": "Notaría", "Importe": f"{costes['Notaria']:,.2f} €"},
            {"Concepto": "Registro", "Importe": f"{costes['Registro']:,.2f} €"},
            {"Concepto": "Gestoría", "Importe": f"{costes['Gestoria']:,.2f} €"},
            {"Concepto": "Tasación", "Importe": f"{costes['Tasacion']:,.2f} €"},
            {"Concepto": "Comisión apertura", "Importe": f"{costes['Comision_apertura']:,.2f} €"},
            {"Concepto": "IVA" if es_nueva else "ITP", "Importe": f"{costes['IVA'] if es_nueva else costes['ITP']:,.2f} €"},
            {"Concepto": "AJD", "Importe": f"{costes['AJD']:,.2f} €"} if es_nueva else {"Concepto": "", "Importe": ""}
        ])
        
        # Filtrar filas vacías
        costes_df = costes_df[costes_df['Concepto'] != '']
        
        st.dataframe(costes_df, use_container_width=True, hide_index=True)
        
        # Gráfico de costes
        fig_costes = go.Figure(data=[
            go.Bar(
                x=list(costes.keys()),
                y=list(costes.values()),
                marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
            )
        ])
        
        fig_costes.update_layout(
            title="Distribución de costes iniciales",
            xaxis_title="Concepto",
            yaxis_title="Importe (€)",
            showlegend=False
        )
        
        st.plotly_chart(fig_costes, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "💡 **Nota**: Esta calculadora proporciona estimaciones basadas en los parámetros introducidos. "
    "Consulta siempre con un profesional financiero para decisiones importantes."
)