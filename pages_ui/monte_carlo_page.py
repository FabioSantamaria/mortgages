import streamlit as st
import numpy as np
import pandas as pd
from modules.monte_carlo import run_monte_carlo_simulation, calculate_simulation_statistics
from modules.plotting import plot_monte_carlo_results, plot_euribor_evolution, create_individual_simulations_plot
from modules.ui_components import create_early_payment_inputs

def show_page():
    st.header("🎲 Monte Carlo - Euribor Estocástico")
    
    st.subheader("Parámetros de la hipoteca")
    col1, col2 = st.columns(2)
    with col1:
        capital_inicial = st.number_input("Capital inicial (€)", min_value=10000, value=200000, step=5000)
        spread = st.number_input("Spread sobre Euribor (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    with col2:
        plazo_anos = st.slider("Plazo del préstamo (años)", 5, 40, 20, 1)


    # Euribor configuration
    st.subheader("Parámetros de la simulación")
    col1, col2 = st.columns(2)
    with col1:
        initial_euribor = st.number_input("Euribor inicial (%)", min_value=-1.0, max_value=10.0, value=2.2, step=0.1)
    with col2:
        distribution_type = st.selectbox(
            "Tipo de distribución",
            ["Uniform Random Walk", "Constant", "Gaussian", "Mean Reverting"]
        )
    
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
    
    # Simulation parameters
    num_simulations = st.slider("Número de simulaciones", 10, 1000, 100, 10)
    
    show_individual_results = st.checkbox("Mostrar simulaciones individuales (muestra)")

    # Early payments
    inyecciones = create_early_payment_inputs(plazo_anos)
    
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
                    num_simulations=num_simulations,
                    inyecciones=inyecciones if inyecciones else None,
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
                
            except Exception as e:
                st.error(f"Error en la simulación: {str(e)}")
                st.write("Detalles del error:")
                st.code(str(e))

        # Show sample individual simulations
        if show_individual_results:
            st.subheader("🔍 Simulaciones individuales (muestra)")
            sample_sims = all_results[all_results['Simulation'].isin(range(min(10, num_simulations)))]
            
            # Create and display the plot
            individual_sims_plot = create_individual_simulations_plot(sample_sims)
            st.plotly_chart(individual_sims_plot, use_container_width=True)
