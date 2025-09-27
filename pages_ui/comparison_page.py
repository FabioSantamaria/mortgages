import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any
import io

from modules.comparison import MortgageComparison
from modules.ui_components import create_early_payment_inputs
import copy

# TODO REFACTOR 
def get_distribution_parameters(distribucion_tipo: str) -> Dict:
    """Get distribution parameters based on type"""
    
    if distribucion_tipo == "Gaussian":
        col1, col2 = st.columns(2)
        with col1:
            media = st.number_input("Media (%)", value=3.0, step=0.1, format="%.2f")
        with col2:
            desviacion = st.number_input("Desviación Estándar (%)", value=1.0, step=0.1, format="%.2f")
        return {'media': media, 'desviacion': desviacion}
    
    elif distribucion_tipo == "Mean Reverting":
        col1, col2, col3 = st.columns(3)
        with col1:
            media_largo_plazo = st.number_input("Media Largo Plazo (%)", value=3.0, step=0.1, format="%.2f")
        with col2:
            velocidad_reversion = st.number_input("Velocidad Reversión", value=0.1, step=0.01, format="%.3f")
        with col3:
            volatilidad = st.number_input("Volatilidad (%)", value=0.5, step=0.1, format="%.2f")
        return {
            'media_largo_plazo': media_largo_plazo,
            'velocidad_reversion': velocidad_reversion,
            'volatilidad': volatilidad
        }
    
    elif distribucion_tipo == "Uniform Random Walk":
        col1, col2 = st.columns(2)
        with col1:
            cambio_min = st.number_input("Cambio Mínimo (%)", value=-0.5, step=0.1, format="%.2f")
        with col2:
            cambio_max = st.number_input("Cambio Máximo (%)", value=0.5, step=0.1, format="%.2f")
        return {'cambio_min': cambio_min, 'cambio_max': cambio_max}
    
    else:  # Constante
        return {}

def add_simulation_form():
    """Form to add a new simulation"""
    
    # The main form is now a standard container, not a Streamlit form block.
    # This allows for the dynamic button to function correctly.
    sim_type = st.selectbox(
        "Tipo de Hipoteca",
        ["Fija", "Variable", "Mixta"],
        help="Selecciona el tipo de hipoteca a simular",
        key="mortgage_type_selector"
    )
    
    st.subheader("Parámetros de Simulación")
    
    # Simulation name
    sim_name = st.text_input(
        "Nombre de la Simulación",
        placeholder="Ej: Fija 3.5%, Variable Euribor+1.2%",
        value=sim_type,
        help="Nombre descriptivo para identificar esta simulación"
    )
    
    # Common parameters
    st.subheader("Parámetros Básicos")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        capital = st.number_input(
            "Capital (€)",
            min_value=10000.0,
            max_value=2000000.0,
            value=300000.0,
            step=5000.0,
            format="%.0f"
        )
    
    with col2:
        plazo_anos = st.number_input(
            "Plazo (años)",
            min_value=5,
            max_value=40,
            value=30,
            step=1
        )
    
    # Type-specific parameters
    if sim_type == "Fija":
        with col3:
            tasa_interes = st.number_input(
                "Tasa de Interés (%)",
                min_value=0.1,
                max_value=15.0,
                value=3.5,
                step=0.1,
                format="%.2f"
            )
    
    elif sim_type == "Variable":
        st.subheader("Parámetros Variable")
        col1, col2 = st.columns(2)
        
        with col1:
            spread = st.number_input(
                "Spread sobre Euribor (%)",
                min_value=0.0,
                max_value=5.0,
                value=1.2,
                step=0.1,
                format="%.2f"
            )
        
        with col2:
            euribor_inicial = st.number_input(
                "Euribor Inicial (%)",
                min_value=-1.0,
                max_value=10.0,
                value=3.5,
                step=0.1,
                format="%.2f"
            )
        
        # Euribor distribution parameters
        distribucion_tipo = st.selectbox(
            "Tipo de Distribución del Euribor",
            ["Uniform Random Walk", "Mean Reverting", "Gaussian", "Constant"]
        )
        
        parametros_distribucion = get_distribution_parameters(distribucion_tipo)
        
        num_simulaciones = st.number_input(
            "Número de Simulaciones Monte Carlo",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100
        )
    
    elif sim_type == "Mixta":
        st.subheader("Parámetros Mixta")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tasa_fija = st.number_input(
                "Tasa Fija (%)",
                min_value=0.1,
                max_value=15.0,
                value=2.8,
                step=0.1,
                format="%.2f"
            )
        
        with col2:
            anos_fijos = st.number_input(
                "Años con Tasa Fija",
                min_value=1,
                max_value=15,
                value=5,
                step=1
            )
        
        with col3:
            spread = st.number_input(
                "Spread Variable (%)",
                min_value=0.0,
                max_value=5.0,
                value=1.2,
                step=0.1,
                format="%.2f"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            euribor_inicial = st.number_input(
                "Euribor Inicial (%)",
                min_value=-1.0,
                max_value=10.0,
                value=3.5,
                step=0.1,
                format="%.2f"
            )
        
        # Euribor distribution parameters
        distribucion_tipo = st.selectbox(
            "Tipo de Distribución del Euribor",
            ["Uniform Random Walk", "Mean Reverting", "Gaussian", "Constant"]
        )
        
        parametros_distribucion = get_distribution_parameters(distribucion_tipo)
        
        with col2:
            num_simulaciones = st.number_input(
                "Número de Simulaciones Monte Carlo",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100
            )
    
    inyecciones = create_early_payment_inputs(plazo_anos, "comparison_form")
    
    # Submit button is now a regular button, as we are no longer in a form.
    submitted = st.button("🚀 Añadir simulación a la cesta")

    if submitted:
        if not sim_name.strip():
            st.error("❌ El nombre de la simulación es obligatorio")
        else:
            # Check for duplicate names
            existing_names = [sim['name'] for sim in st.session_state.comparison_simulations]
            if sim_name in existing_names:
                st.error("❌ Ya existe una simulación con ese nombre")
            else:
                # Create simulation config
                sim_config = {
                    'name': sim_name,
                    'type': sim_type.lower(),
                    'capital': capital,
                    'plazo_anos': plazo_anos,
                    'inyecciones': copy.deepcopy(inyecciones) if inyecciones else []
                }
                
                if sim_type == "Fija":
                    sim_config['tasa_interes'] = tasa_interes
                
                elif sim_type == "Variable":
                    sim_config.update({
                        'spread': spread,
                        'euribor_inicial': euribor_inicial,
                        'distribucion_tipo': distribucion_tipo,
                        'parametros_distribucion': parametros_distribucion,
                        'num_simulaciones': num_simulaciones
                    })
                
                elif sim_type == "Mixta":
                    sim_config.update({
                        'tasa_fija': tasa_fija,
                        'anos_fijos': anos_fijos,
                        'spread': spread,
                        'euribor_inicial': euribor_inicial,
                        'distribucion_tipo': distribucion_tipo,
                        'parametros_distribucion': parametros_distribucion,
                        'num_simulaciones': num_simulaciones
                    })
                
                st.session_state.comparison_simulations.append(sim_config)
                st.session_state.comparison_results = None  # Reset results
                st.success(f"✅ Simulación '{sim_name}' añadida correctamente")
                st.rerun()

def display_configured_simulations():
    """Display the list of configured simulations"""
    
    for i, sim in enumerate(st.session_state.comparison_simulations):
        with st.expander(f"📊 {sim['name']} ({sim['type'].title()})", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Tipo:** {sim['type'].title()}")
                st.write(f"**Capital:** {sim['capital']:,.0f} €")
                st.write(f"**Plazo:** {sim['plazo_anos']} años")
                
                if sim['type'] == 'fija':
                    st.write(f"**Tasa de Interés:** {sim['tasa_interes']:.2f}%")
                elif sim['type'] == 'variable':
                    st.write(f"**Spread:** {sim['spread']:.2f}%")
                    st.write(f"**Euribor Inicial:** {sim['euribor_inicial']:.2f}%")
                    st.write(f"**Simulaciones:** {sim['num_simulaciones']}")
                    st.write(f"**Distribución Euribor:** {sim['distribucion_tipo']}")
                elif sim['type'] == 'mixta':
                    st.write(f"**Tasa Fija:** {sim['tasa_fija']:.2f}% ({sim['anos_fijos']} años)")
                    st.write(f"**Spread Variable:** {sim['spread']:.2f}%")
                    st.write(f"**Euribor Inicial:** {sim['euribor_inicial']:.2f}%")
                    st.write(f"**Simulaciones:** {sim['num_simulaciones']}")
                    st.write(f"**Distribución Euribor:** {sim['distribucion_tipo']}")
                if sim['inyecciones']:
                    st.write(f"**Inyecciones:** {len(sim['inyecciones'])} configuradas")
                    st.write("**Detalles de Inyecciones:**")
                    for inyeccion in sim['inyecciones']:
                        st.write(f"- Mes {inyeccion['mes_inyeccion']}: {inyeccion['capital_inyectado']:,.0f} € ({inyeccion['tipo_inyeccion']})")
            
            with col2:
                if st.button(f"🗑️ Eliminar", key=f"delete_{i}"):
                    st.session_state.comparison_simulations.pop(i)
                    st.session_state.comparison_results = None
                    st.rerun()

def run_all_simulations(bank_name: str):
    """Execute all configured simulations"""
    if not st.session_state.comparison_simulations:
        st.error("❌ No hay simulaciones configuradas")
        return
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize comparison object
        comparison = MortgageComparison(bank_name)
        
        # Add all simulations to comparison
        for sim_config in st.session_state.comparison_simulations:
            comparison.add_simulation(sim_config)
        
        status_text.text("🔄 Ejecutando simulaciones...")
        
        # Run all simulations
        results = comparison.run_all_simulations()
        
        # Update progress
        progress_bar.progress(100)
        status_text.text("✅ Simulaciones completadas")
        
        # Store results in session state
        st.session_state.comparison_results = {
            'comparison_object': comparison,
            'results': results,
            'bank_name': bank_name
        }
        
        # Show success message
        successful_sims = len([r for r in results.values() if 'error' not in r])
        failed_sims = len([r for r in results.values() if 'error' in r])
        
        if failed_sims == 0:
            st.success(f"✅ Todas las {successful_sims} simulaciones se ejecutaron correctamente")
        else:
            st.warning(f"⚠️ {successful_sims} simulaciones exitosas, {failed_sims} fallaron")
            
            # Show errors
            for sim_name, result in results.items():
                if 'error' in result:
                    st.error(f"❌ Error en '{sim_name}': {result['error']}")
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Error ejecutando simulaciones: {str(e)}")

def display_comparison_results(bank_name: str):
    """Display comparison results with charts and tables"""
    if not st.session_state.comparison_results:
        return
    
    comparison = st.session_state.comparison_results['comparison_object']
    results = st.session_state.comparison_results['results']
    
    st.subheader(f"📊 Resultados de Comparación - {bank_name}")
    
    # Summary table
    st.subheader("📋 Resumen Comparativo")
    summary_df = comparison.get_comparison_summary()
    
    if not summary_df.empty:
        st.dataframe(summary_df, width='stretch', hide_index=True)
        
        # Export buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📊 Exportar a Excel", use_container_width=True):
                try:
                    excel_buffer = comparison.export_to_excel()
                    st.download_button(
                        label="⬇️ Descargar Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"comparacion_hipotecas_{bank_name.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generando Excel: {str(e)}")
        
        with col2:
            if st.button("📄 Exportar a CSV", use_container_width=True):
                try:
                    csv_buffer = comparison.export_to_csv()
                    st.download_button(
                        label="⬇️ Descargar CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"comparacion_hipotecas_{bank_name.replace(' ', '_')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generando CSV: {str(e)}")
    
    # Detailed comparison charts
    st.subheader("📈 Gráficos Comparativos")
    
    # Filter successful results
    successful_results = {name: result for name, result in results.items() if 'error' not in result}
    
    if len(successful_results) >= 2:
        # Total interest comparison
        fig_interest = create_interest_comparison_chart(successful_results)
        if fig_interest:
            st.plotly_chart(fig_interest, width='stretch')
        
        # Total payment comparison
        fig_payment = create_payment_comparison_chart(successful_results)
        if fig_payment:
            st.plotly_chart(fig_payment, width='stretch')
        
        # Monthly payment evolution (for variable/mixed mortgages)
        fig_evolution = create_payment_evolution_chart(successful_results)
        if fig_evolution:
            st.plotly_chart(fig_evolution, width='stretch')
    
    # Individual simulation details
    st.subheader("🔍 Detalles por Simulación")
    
    for sim_name, result in successful_results.items():
        with st.expander(f"📊 {sim_name} ({result['type'].title()})", expanded=False):
            display_individual_simulation_details(result)

def create_interest_comparison_chart(results: Dict[str, Any]):
    """Create a bar chart comparing total interest payments"""
    try:
        names = []
        interests = []
        colors = []
        
        color_map = {'fija': '#1f77b4', 'variable': '#ff7f0e', 'mixta': '#2ca02c'}
        
        for name, result in results.items():
            names.append(name)
            summary = result['summary']
            
            if result['type'] == 'fija':
                interests.append(summary['total_intereses'])
            else:
                interests.append(summary['total_intereses_promedio'])
            
            colors.append(color_map.get(result['type'], '#d62728'))
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=interests,
                marker_color=colors,
                text=[f"{int(i):,} €" for i in interests],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Comparación de Intereses Totales",
            xaxis_title="Simulación",
            yaxis_title="Intereses Totales (€)",
            showlegend=False
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de intereses: {str(e)}")
        return None

def create_payment_comparison_chart(results: Dict[str, Any]):
    """Create a bar chart comparing total payments"""
    try:
        names = []
        payments = []
        colors = []
        
        color_map = {'fija': '#1f77b4', 'variable': '#ff7f0e', 'mixta': '#2ca02c'}
        
        for name, result in results.items():
            names.append(name)
            summary = result['summary']
            
            if result['type'] == 'fija':
                payments.append(summary['total_pagado'])
            else:
                payments.append(summary['total_pagado_promedio'])
            
            colors.append(color_map.get(result['type'], '#d62728'))
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=payments,
                marker_color=colors,
                text=[f"{int(p):,} €" for p in payments],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Comparación de Pagos Totales",
            xaxis_title="Simulación",
            yaxis_title="Pago Total (€)",
            showlegend=False
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de pagos: {str(e)}")
        return None

def create_payment_evolution_chart(results: Dict[str, Any]):
    """Create a line chart showing payment evolution over time"""
    try:
        fig = go.Figure()
        
        for name, result in results.items():
            if result['type'] == 'fija':
                # Fixed mortgage - constant payment
                df = result['simulation_data']
                fig.add_trace(go.Scatter(
                    x=df['Mes'],
                    y=df['Cuota_mensual'],
                    mode='lines',
                    name=f"{name} (Fija)",
                    line=dict(width=2)
                ))
            else:
                # Variable/Mixed mortgage - show average evolution
                if 'statistics' in result:
                    # Use sample data for visualization
                    df_sample = result['simulation_data'].head(360)  # First 30 years
                    if not df_sample.empty:
                        # Group by month and calculate mean
                        monthly_avg = df_sample.groupby('Mes')['Cuota_mensual'].mean().reset_index()
                        fig.add_trace(go.Scatter(
                            x=monthly_avg['Mes'],
                            y=monthly_avg['Cuota_mensual'],
                            mode='lines',
                            name=f"{name} ({result['type'].title()} - Promedio)",
                            line=dict(width=2, dash='dash' if result['type'] == 'variable' else 'dot')
                        ))
        
        fig.update_layout(
            title="Evolución de Cuotas Mensuales",
            xaxis_title="Mes",
            yaxis_title="Cuota Mensual (€)",
            hovermode='x unified'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de evolución: {str(e)}")
        return None

def display_individual_simulation_details(result: Dict[str, Any]):
    """Display detailed information for an individual simulation"""
    summary = result['summary']
    sim_type = result['type']
    
    # Basic information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Capital Inicial", f"{summary['capital_inicial']:,.0f} €")
        st.metric("Plazo", f"{summary['plazo_anos']} años")
    
    with col2:
        if sim_type == 'fija':
            st.metric("Tasa de Interés", f"{summary['tasa_interes']:.2f}%")
            st.metric("Cuota Mensual", f"{summary['cuota_mensual']:,.2f} €")
        else:
            if sim_type == 'mixta':
                st.metric("Tasa Fija", f"{summary['tasa_fija']:.2f}% ({summary['anos_fijos']}a)")
            st.metric("Spread", f"{summary['spread']:.2f}%")
    
    with col3:
        if sim_type == 'fija':
            st.metric("Total Intereses", f"{summary['total_intereses']:,.0f} €")
            st.metric("Total Pagado", f"{summary['total_pagado']:,.0f} €")
        else:
            st.metric("Total Intereses (Promedio)", f"{summary['total_intereses_promedio']:,.0f} €")
            st.metric("Total Pagado (Promedio)", f"{summary['total_pagado_promedio']:,.0f} €")
    
    # Early payments information
    if summary.get('inyecciones_totales', 0) > 0:
        st.info(f"💰 Inyecciones de capital: {summary['inyecciones_totales']:,.0f} €")
        if summary.get('ahorro_intereses', 0) > 0:
            st.success(f"💡 Ahorro en intereses: {summary['ahorro_intereses']:,.0f} €")
    
    # Monte Carlo statistics for variable/mixed mortgages
    if sim_type in ['variable', 'mixta'] and 'statistics' in result:
        st.subheader("📊 Estadísticas Monte Carlo")
        stats_df = result['statistics']
        st.dataframe(stats_df, width='stretch', hide_index=True)

def show_page():
    """Display the mortgage comparison page"""
    
    st.title("🏦 Comparación de Hipotecas")
    st.markdown("Compara diferentes tipos de hipotecas (fija, variable, mixta) para un banco específico")
    
    # Bank name input
    st.subheader("📋 Información del Banco")
    bank_name = st.text_input(
        "Nombre del Banco",
        value="",
        placeholder="Ej: Banco Santander, BBVA, CaixaBank...",
        help="Introduce el nombre del banco para identificar las simulaciones"
    )
    
    if not bank_name.strip():
        st.warning("⚠️ Por favor, introduce el nombre del banco para continuar")
        return
    
    # Initialize session state for simulations
    if 'comparison_simulations' not in st.session_state:
        st.session_state.comparison_simulations = []
    
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = None
    
    # Simulation configuration section
    st.subheader("⚙️ Configuración de Simulaciones")
    
    # Add new simulation
    with st.expander("➕ Añadir Nueva Simulación", expanded=len(st.session_state.comparison_simulations) == 0):
        add_simulation_form()
    
    # Display current simulations
    if st.session_state.comparison_simulations:
        st.subheader("📊 Simulaciones Configuradas")
        display_configured_simulations()
        
        # Run simulations button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Ejecutar Todas las Simulaciones", type="primary", use_container_width=True):
                run_all_simulations(bank_name)
        
        # Display results if available
        if st.session_state.comparison_results:
            display_comparison_results(bank_name)
    
    else:
        st.info("ℹ️ No hay simulaciones configuradas. Añade al menos una simulación para comenzar.")