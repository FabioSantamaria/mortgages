import plotly.graph_objects as go
import numpy as np

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

def plot_mortgage_simulation(df):
    """Create plot for mortgage simulation results"""
    fig = go.Figure()
    
    # Monthly payment
    fig.add_trace(go.Scatter(
        x=df['Mes'],
        y=df['Cuota_mensual'],
        mode='lines',
        name='Cuota mensual',
        line=dict(color='blue', width=2)
    ))
    
    # Monthly interest
    fig.add_trace(go.Scatter(
        x=df['Mes'],
        y=df['Intereses_mensuales'],
        mode='lines',
        name='Intereses mensuales',
        line=dict(color='red', width=2)
    ))
    
    # Monthly amortization
    fig.add_trace(go.Scatter(
        x=df['Mes'],
        y=df['Amortizacion_mensual'],
        mode='lines',
        name='Amortización mensual',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title='Evolución de pagos',
        xaxis_title='Mes',
        yaxis_title='Importe (€)',
        hovermode='x unified'
    )
    
    return fig

def plot_monte_carlo_results(stats_df, distribution_type="Gaussian", has_early_payments=False):
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
        #showlegend=False,
        name='Cuota Mensual (90% CI UP)'
    ))
    
    # Lower bound for monthly payment
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Cuota_mensual_<lambda_0>'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,0.2)'),
        name='Cuota Mensual (90% CI LOW)'
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
        #showlegend=False,
        name='Intereses Mensuales (90% CI UP)'
    ))
    
    # Lower bound for interest
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Intereses_mensuales_<lambda_0>'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='rgba(255,0,0,0.2)'),
        name='Intereses Mensuales (90% CI LOW)'
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
        #showlegend=False,
        name='Amortización Mensual (90% CI UP)'
    ))
    
    # Lower bound for amortization
    fig.add_trace(go.Scatter(
        x=stats_df['Mes'],
        y=stats_df['Amortizacion_mensual_<lambda_0>'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.2)',
        line=dict(color='rgba(0,255,0,0.2)'),
        name='Amortización Mensual (90% CI LOW)'
    ))
    
    fig.update_layout(
        title='Simulación Monte Carlo - Hipoteca Variable con Euribor Estocástico',
        xaxis_title='Mes',
        yaxis_title='Importe (€)',
        hovermode='x unified'
    )
    
    return fig

def plot_cost_breakdown(costes):
    """Create bar chart for initial costs breakdown"""
    fig = go.Figure(data=[
        go.Bar(
            x=list(costes.keys()),
            y=list(costes.values()),
            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        )
    ])
    
    fig.update_layout(
        title="Distribución de costes iniciales",
        xaxis_title="Concepto",
        yaxis_title="Importe (€)",
        showlegend=False
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

def create_individual_simulations_plot(sample_sims):
    """Creates a plotly figure showing individual simulation traces"""
    fig = go.Figure()

    # Add a trace for each simulation
    for sim_id in sample_sims['Simulation'].unique():
        sim_data = sample_sims[sample_sims['Simulation'] == sim_id]
        fig.add_trace(go.Scatter(
            x=sim_data['Mes'],
            y=sim_data['Cuota_mensual'],
            mode='lines',
            name=f'Simulación {sim_id+1}',
            opacity=0.7
        ))

    # Configure layout
    fig.update_layout(
        title='Muestra de simulaciones individuales - Cuota mensual',
        xaxis_title='Mes',
        yaxis_title='Cuota mensual (€)',
        hovermode='x unified'
    )

    return fig