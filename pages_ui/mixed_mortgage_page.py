import streamlit as st
import numpy as np
import pandas as pd
from modules.mixed_mortgage import (
    run_mixed_monte_carlo_simulation, 
    calculate_mixed_simulation_statistics,
    compare_mixed_vs_variable_mortgage
)
from modules.plotting import plot_monte_carlo_results, plot_euribor_evolution, create_individual_simulations_plot
from modules.ui_components import create_early_payment_inputs

def show_page():
    st.header("🏠 Hipoteca Mixta - Monte Carlo")
    st.info("💡 **Hipoteca Mixta**: Tipo fijo los primeros años (3-10), después tipo variable (Euribor + diferencial)")
    
    st.subheader("Parámetros de la hipoteca mixta")
    col1, col2 = st.columns(2)
    with col1:
        capital_inicial = st.number_input("Capital inicial (€)", min_value=10000, value=200000, step=5000)
        tasa_fija = st.number_input("Tipo fijo inicial (%)", min_value=0.1, max_value=10.0, value=3.5, step=0.1)
    with col2:
        plazo_anos = st.slider("Plazo del préstamo (años)", 5, 40, 20, 1)
    
    # Mixed mortgage specific parameters
    st.subheader("Configuración del período mixto")
    col1, col2 = st.columns(2)
    with col1:
        initial_euribor = st.number_input("Euribor inicial (%)", min_value=-1.0, max_value=10.0, value=2.2, step=0.1)
        spread = st.number_input("Diferencial sobre Euribor (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    with col2:
        anos_fijos = st.slider("Años con tipo fijo", 3, 10, 5, 1)
        st.info(f"📅 **Período fijo**: Meses 1-{anos_fijos * 12} (tipo {tasa_fija}%)")
        st.info(f"📈 **Período variable**: Mes {anos_fijos * 12 + 1} en adelante (Euribor + {spread:.2f}%)")

    # Euribor distribution configuration
    st.subheader("Parámetros de la simulación Euribor")
    col1, col2 = st.columns(2)
    with col1:
        distribution_type = st.selectbox(
            "Tipo de distribución",
            ["Uniform Random Walk", "Constant", "Gaussian", "Mean Reverting"]
        )
    with col2:
        num_simulations = st.slider("Número de simulaciones", 10, 1000, 100, 10)
    
    # Distribution parameters
    dist_params = {}
    if distribution_type == "Gaussian":
        col1, col2 = st.columns(2)
        with col1:
            dist_params['volatility'] = st.slider("Volatilidad anual", 0.1, 2.0, 0.2, 0.1)
        with col2:
            dist_params['drift'] = st.slider("Deriva anual (%)", -2.0, 2.0, 0.0, 0.1)
    
    elif distribution_type == "Mean Reverting":
        col1, col2, col3 = st.columns(3)
        with col1:
            dist_params['mean_level'] = st.number_input("Nivel medio (%)", value=initial_euribor)
        with col2:
            dist_params['reversion_speed'] = st.slider("Velocidad de reversión", 0.01, 1.0, 0.1, 0.01)
        with col3:
            dist_params['volatility'] = st.slider("Volatilidad", 0.1, 1.0, 0.3, 0.1)
    
    elif distribution_type == "Uniform Random Walk":
        dist_params['max_change'] = st.slider("Cambio máximo anual (%)", 0.1, 2.0, 0.25, 0.05)
    
    # Additional options
    col1, col2 = st.columns(2)
    with col1:
        show_individual_results = st.checkbox("Mostrar simulaciones individuales (muestra)")
    with col2:
        show_comparison = st.checkbox("Comparar con hipoteca 100% variable")

    # Early payments
    inyecciones = create_early_payment_inputs(plazo_anos)
    
    # Run simulation
    if st.button("🚀 Ejecutar simulación Monte Carlo Mixta", key="run_mixed_mc"):
        with st.spinner("Ejecutando simulaciones de hipoteca mixta..."):
            try:
                if show_comparison:
                    # Run comparison analysis
                    comparison_results = compare_mixed_vs_variable_mortgage(
                        capital_inicial=capital_inicial,
                        tasa_fija=tasa_fija,
                        spread=spread,
                        plazo_anos=plazo_anos,
                        anos_fijos=anos_fijos,
                        initial_euribor=initial_euribor,
                        distribution_type=distribution_type,
                        num_simulations=num_simulations,
                        inyecciones=inyecciones if inyecciones else None,
                        **dist_params
                    )
                    
                    all_results = comparison_results['mixed_results']
                    variable_results = comparison_results['variable_results']
                    comparison = comparison_results['comparison']
                    
                    # Show comparison metrics
                    st.subheader("🔄 Comparación: Hipoteca Mixta vs Variable")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Intereses Mixta", 
                            f"{comparison['mixed_avg_interest']:,.0f} €"
                        )
                    with col2:
                        st.metric(
                            "Intereses Variable", 
                            f"{comparison['variable_avg_interest']:,.0f} €"
                        )
                    with col3:
                        difference = comparison['interest_difference']
                        st.metric(
                            "Diferencia", 
                            f"{difference:,.0f} €",
                            delta=f"{difference:,.0f} €" if difference != 0 else None
                        )
                    with col4:
                        duration_diff = comparison['duration_difference']
                        st.metric(
                            "Diferencia duración", 
                            f"{duration_diff:.1f} años",
                            delta=f"{duration_diff:.1f} años" if duration_diff != 0 else None
                        )
                    
                    if difference > 0:
                        st.success(f"💰 La hipoteca mixta ahorra **{difference:,.0f} €** en intereses comparada con la variable")
                    elif difference < 0:
                        st.warning(f"⚠️ La hipoteca mixta cuesta **{abs(difference):,.0f} €** más en intereses que la variable")
                    else:
                        st.info("ℹ️ Ambas hipotecas tienen costes similares")
                
                else:
                    # Run only mixed mortgage simulation
                    all_results = run_mixed_monte_carlo_simulation(
                        capital_inicial=capital_inicial,
                        tasa_fija=tasa_fija,
                        spread=spread,
                        plazo_anos=plazo_anos,
                        anos_fijos=anos_fijos,
                        initial_euribor=initial_euribor,
                        distribution_type=distribution_type,
                        num_simulations=num_simulations,
                        inyecciones=inyecciones if inyecciones else None,
                        **dist_params
                    )
                
                # Split the DataFrame into list of DataFrames by simulation number
                simulation_dfs = [group for _, group in all_results.groupby('Simulation')]
                
                # Calculate statistics
                stats_df = calculate_mixed_simulation_statistics(all_results)
                
                # Summary metrics
                st.subheader("📊 Resumen de resultados - Hipoteca Mixta")
                
                duraciones = [len(df) for df in simulation_dfs]
                intereses_totales = [df['Intereses_mensuales'].sum() for df in simulation_dfs]
                pagos_iniciales = [df['Cuota_mensual'].iloc[0] for df in simulation_dfs]
                
                # Calculate average rates for fixed and variable periods
                fixed_period_data = all_results[all_results['Tipo_Periodo'] == 'Fijo']
                variable_period_data = all_results[all_results['Tipo_Periodo'] == 'Variable']
                
                avg_fixed_rate = fixed_period_data['Tasa_Anual'].mean() if len(fixed_period_data) > 0 else tasa_fija
                avg_variable_rate = variable_period_data['Tasa_Anual'].mean() if len(variable_period_data) > 0 else initial_euribor + spread
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Duración promedio", f"{np.mean(duraciones)/12:.1f} años")
                with col2:
                    st.metric("Intereses totales promedio", f"{np.mean(intereses_totales):,.0f} €")
                with col3:
                    st.metric("Pago inicial", f"{np.mean(pagos_iniciales):,.0f} €")
                with col4:
                    st.metric("Tipo medio período fijo", f"{avg_fixed_rate:.2f}%")
                
                # Additional metrics for mixed mortgage
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tipo medio período variable", f"{avg_variable_rate:.2f}%")
                with col2:
                    meses_fijos_total = anos_fijos * 12
                    st.metric("Meses con tipo fijo", f"{meses_fijos_total} meses")
                with col3:
                    pct_fijo = (meses_fijos_total / np.mean(duraciones)) * 100
                    st.metric("% tiempo con tipo fijo", f"{pct_fijo:.1f}%")
                
                # Charts
                st.subheader("📈 Evolución de pagos")
                fig_payments = plot_monte_carlo_results(stats_df)
                st.plotly_chart(fig_payments, use_container_width=True)
                
                st.subheader("📈 Evolución del Euribor")
                fig_euribor = plot_euribor_evolution(stats_df)
                st.plotly_chart(fig_euribor, use_container_width=True)
                
                # Interest rate evolution chart
                st.subheader("📈 Evolución del tipo de interés (Mixta)")
                import plotly.graph_objects as go
                
                fig_rates = go.Figure()
                fig_rates.add_trace(go.Scatter(
                    x=stats_df['Mes'],
                    y=stats_df['Tasa_Anual_mean'],
                    mode='lines',
                    name='Tipo medio',
                    line=dict(color='blue', width=2)
                ))
                
                fig_rates.add_trace(go.Scatter(
                    x=stats_df['Mes'],
                    y=stats_df['Tasa_Anual_<lambda_0>'],
                    mode='lines',
                    name='Percentil 5',
                    line=dict(color='lightblue', dash='dash'),
                    showlegend=False
                ))
                
                fig_rates.add_trace(go.Scatter(
                    x=stats_df['Mes'],
                    y=stats_df['Tasa_Anual_<lambda_1>'],
                    mode='lines',
                    name='Percentil 95',
                    line=dict(color='lightblue', dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(173, 216, 230, 0.2)'
                ))
                
                # Add vertical line to show transition from fixed to variable
                fig_rates.add_vline(
                    x=anos_fijos * 12, 
                    line_dash="dot", 
                    line_color="red",
                    annotation_text=f"Fin período fijo (mes {anos_fijos * 12})"
                )
                
                fig_rates.update_layout(
                    title='Evolución del Tipo de Interés - Hipoteca Mixta',
                    xaxis_title='Mes',
                    yaxis_title='Tipo de Interés (%)',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_rates, use_container_width=True)
                
                # Detailed statistics
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
                
                # Risk analysis
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
                
                # Show sample individual simulations
                if show_individual_results:
                    st.subheader("🔍 Simulaciones individuales (muestra)")
                    sample_sims = all_results[all_results['Simulation'].isin(range(min(10, num_simulations)))]
                    
                    # Create and display the plot
                    individual_sims_plot = create_individual_simulations_plot(sample_sims)
                    st.plotly_chart(individual_sims_plot, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error en la simulación: {str(e)}")
                st.write("Detalles del error:")
                st.code(str(e))