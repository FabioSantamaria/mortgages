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

def mostrar_pagina_comparacion():
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

def add_simulation_form():
    """Form to add a new simulation"""
    
    # Pre-select mortgage type to determine form key
    sim_type = st.selectbox(
        "Tipo de Hipoteca",
        ["Fija", "Variable", "Mixta"],
        help="Selecciona el tipo de hipoteca a simular",
        key="mortgage_type_selector"
    )
    
    # Use dynamic form key based on mortgage type to force refresh
    with st.form(f"add_simulation_form_{sim_type.lower()}"):
        # Simulation name
        sim_name = st.text_input(
            "Nombre de la Simulación",
            placeholder="Ej: Fija 3.5%, Variable Euribor+1.2%",
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
                ["Gaussiana", "Reversión a la Media", "Caminata Aleatoria Uniforme", "Constante"]
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
                ["Gaussiana", "Reversión a la Media", "Caminata Aleatoria Uniforme", "Constante"]
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
        
        # Early payments section
        st.subheader("💰 Inyecciones de Capital (Opcional)")
        include_injections = st.checkbox("Incluir inyecciones de capital")
        
        inyecciones = []
        if include_injections:
            inyecciones = create_early_payment_inputs(plazo_anos, "comparison_form")
        
        # Submit button
        submitted = st.form_submit_button("➕ Añadir Simulación", type="primary")
        
        if submitted:
            if not sim_name.strip():
                st.error("❌ El nombre de la simulación es obligatorio")
                return
            
            # Check for duplicate names
            existing_names = [sim['name'] for sim in st.session_state.comparison_simulations]
            if sim_name in existing_names:
                st.error("❌ Ya existe una simulación con ese nombre")
                return
            
            # Create simulation config
            sim_config = {
                'name': sim_name,
                'type': sim_type.lower(),
                'capital': capital,
                'plazo_anos': plazo_anos,
                'inyecciones': inyecciones
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

def get_distribution_parameters(distribucion_tipo: str) -> Dict:
    """Get distribution parameters based on type"""
    
    if distribucion_tipo == "Gaussiana":
        col1, col2 = st.columns(2)
        with col1:
            media = st.number_input("Media (%)", value=3.0, step=0.1, format="%.2f")
        with col2:
            desviacion = st.number_input("Desviación Estándar (%)", value=1.0, step=0.1, format="%.2f")
        return {'media': media, 'desviacion': desviacion}
    
    elif distribucion_tipo == "Reversión a la Media":
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
    
    elif distribucion_tipo == "Caminata Aleatoria Uniforme":
        col1, col2 = st.columns(2)
        with col1:
            cambio_min = st.number_input("Cambio Mínimo (%)", value=-0.5, step=0.1, format="%.2f")
        with col2:
            cambio_max = st.number_input("Cambio Máximo (%)", value=0.5, step=0.1, format="%.2f")
        return {'cambio_min': cambio_min, 'cambio_max': cambio_max}
    
    else:  # Constante
        return {}

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
                elif sim['type'] == 'mixta':
                    st.write(f"**Tasa Fija:** {sim['tasa_fija']:.2f}% ({sim['anos_fijos']} años)")
                    st.write(f"**Spread Variable:** {sim['spread']:.2f}%")
                    st.write(f"**Euribor Inicial:** {sim['euribor_inicial']:.2f}%")
                    st.write(f"**Simulaciones:** {sim['num_simulaciones']}")
                
                if sim['inyecciones']:
                    st.write(f"**Inyecciones:** {len(sim['inyecciones'])} configuradas")
            
            with col2:
                if st.button(f"🗑️ Eliminar", key=f"delete_{i}"):
                    st.session_state.comparison_simulations.pop(i)
                    st.session_state.comparison_results = None
                    st.rerun()

def run_all_simulations(bank_name: str):
    """Run all configured simulations"""
    
    if not st.session_state.comparison_simulations:
        st.error("❌ No hay simulaciones configuradas")
        return
    
    with st.spinner("🔄 Ejecutando simulaciones..."):
        try:
            # Create comparison instance
            comparison = MortgageComparison(bank_name)
            
            # Add all simulations
            for sim_config in st.session_state.comparison_simulations:
                if sim_config['type'] == 'fija':
                    comparison.add_fixed_simulation(
                        name=sim_config['name'],
                        capital=sim_config['capital'],
                        tasa_interes=sim_config['tasa_interes'],
                        plazo_anos=sim_config['plazo_anos'],
                        inyecciones=sim_config['inyecciones']
                    )
                
                elif sim_config['type'] == 'variable':
                    comparison.add_variable_simulation(
                        name=sim_config['name'],
                        capital=sim_config['capital'],
                        spread=sim_config['spread'],
                        plazo_anos=sim_config['plazo_anos'],
                        euribor_inicial=sim_config['euribor_inicial'],
                        distribucion_tipo=sim_config['distribucion_tipo'],
                        parametros_distribucion=sim_config['parametros_distribucion'],
                        num_simulaciones=sim_config['num_simulaciones'],
                        inyecciones=sim_config['inyecciones']
                    )
                
                elif sim_config['type'] == 'mixta':
                    comparison.add_mixed_simulation(
                        name=sim_config['name'],
                        capital=sim_config['capital'],
                        tasa_fija=sim_config['tasa_fija'],
                        anos_fijos=sim_config['anos_fijos'],
                        spread=sim_config['spread'],
                        plazo_anos=sim_config['plazo_anos'],
                        euribor_inicial=sim_config['euribor_inicial'],
                        distribucion_tipo=sim_config['distribucion_tipo'],
                        parametros_distribucion=sim_config['parametros_distribucion'],
                        num_simulaciones=sim_config['num_simulaciones'],
                        inyecciones=sim_config['inyecciones']
                    )
            
            # Run simulations
            results = comparison.run_simulations()
            st.session_state.comparison_results = {
                'comparison': comparison,
                'results': results
            }
            
            st.success(f"✅ {len(results)} simulaciones ejecutadas correctamente")
            
        except Exception as e:
            st.error(f"❌ Error ejecutando simulaciones: {str(e)}")

def display_comparison_results(bank_name: str):
    """Display comparison results"""
    
    if not st.session_state.comparison_results:
        return
    
    comparison = st.session_state.comparison_results['comparison']
    results = st.session_state.comparison_results['results']
    
    st.subheader(f"📈 Resultados de Comparación - {bank_name}")
    
    # Summary table
    st.subheader("📊 Resumen Comparativo")
    summary_data = []
    for name, res in results.items():
        if res['type'] == 'fixed':
            summary_data.append({
                'Simulación': name,
                'Tipo': 'Fija',
                'Cuota Inicial': res['cuota_inicial'],
                'Total Pagado': res['total_pagado'],
                'Total Intereses': res['total_intereses'],
                'Ahorro Intereses': res.get('ahorro_intereses', 0)
            })
        else:
            stats = res['estadisticas']
            summary_data.append({
                'Simulación': name,
                'Tipo': res['type'].title(),
                'Cuota Inicial': stats['cuota_inicial_promedio'],
                'Total Pagado': stats['total_pagado_promedio'],
                'Total Intereses': stats['total_intereses_promedio'],
                'Ahorro Intereses': stats.get('ahorro_intereses_promedio', 0)
            })
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Export buttons
    st.subheader("💾 Exportar Resultados Detallados")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Descargar Excel Detallado", type="secondary", use_container_width=True):
            try:
                excel_buffer = comparison.export_to_excel_detailed()
                st.download_button(
                    label="⬇️ Descargar archivo Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"comparacion_detallada_{bank_name.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Error generando Excel: {str(e)}")
    
    with col2:
        if st.button("📄 Descargar CSV Detallado", type="secondary", use_container_width=True):
            try:
                csv_data = comparison.export_to_csv_detailed()
                st.download_button(
                    label="⬇️ Descargar archivo CSV",
                    data=csv_data,
                    file_name=f"comparacion_detallada_{bank_name.replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Error generando CSV: {str(e)}")
    
    # Visualization
    create_comparison_charts(results)
    
    # Detailed results
    st.subheader("🔍 Resultados Detallados")
    
    selected_sim = st.selectbox(
        "Selecciona una simulación para ver detalles:",
        list(results.keys())
    )
    
    if selected_sim:
        display_detailed_results(selected_sim, results[selected_sim])

def create_comparison_charts(results: Dict[str, Any]):
    """Create comparison charts"""
    
    st.subheader("📈 Gráficos Comparativos")
    
    # Prepare data for charts
    chart_data = []
    
    for name, result in results.items():
        if result['type'] == 'fixed':
            chart_data.append({
                'Simulación': name,
                'Tipo': 'Fija',
                'Total Pagado': result['total_pagado'],
                'Total Intereses': result['total_intereses'],
                'Cuota Inicial': result['cuota_inicial']
            })
        else:
            stats = result['estadisticas']
            chart_data.append({
                'Simulación': name,
                'Tipo': result['type'].title(),
                'Total Pagado': stats['total_pagado_promedio'],
                'Total Intereses': stats['total_intereses_promedio'],
                'Cuota Inicial': stats['cuota_inicial_promedio']
            })
    
    chart_df = pd.DataFrame(chart_data)
    
    # Total paid comparison
    fig_total = px.bar(
        chart_df,
        x='Simulación',
        y='Total Pagado',
        color='Tipo',
        title='Comparación: Total Pagado por Simulación',
        labels={'Total Pagado': 'Total Pagado (€)'},
        text='Total Pagado'
    )
    fig_total.update_traces(texttemplate='%{text:,.0f}€', textposition='outside')
    fig_total.update_layout(height=500)
    st.plotly_chart(fig_total, use_container_width=True)
    
    # Interest comparison
    fig_interest = px.bar(
        chart_df,
        x='Simulación',
        y='Total Intereses',
        color='Tipo',
        title='Comparación: Total de Intereses por Simulación',
        labels={'Total Intereses': 'Total Intereses (€)'},
        text='Total Intereses'
    )
    fig_interest.update_traces(texttemplate='%{text:,.0f}€', textposition='outside')
    fig_interest.update_layout(height=500)
    st.plotly_chart(fig_interest, use_container_width=True)
    
    # Monthly payment comparison
    fig_payment = px.bar(
        chart_df,
        x='Simulación',
        y='Cuota Inicial',
        color='Tipo',
        title='Comparación: Cuota Mensual Inicial por Simulación',
        labels={'Cuota Inicial': 'Cuota Inicial (€)'},
        text='Cuota Inicial'
    )
    fig_payment.update_traces(texttemplate='%{text:,.0f}€', textposition='outside')
    fig_payment.update_layout(height=500)
    st.plotly_chart(fig_payment, use_container_width=True)

def display_detailed_results(sim_name: str, result: Dict[str, Any]):
    """Display detailed results for a specific simulation"""
    
    st.write(f"### 📋 Detalles: {sim_name}")
    
    if result['type'] == 'fixed':
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cuota Mensual", f"{result['cuota_inicial']:,.2f} €")
        with col2:
            st.metric("Total Pagado", f"{result['total_pagado']:,.2f} €")
        with col3:
            st.metric("Total Intereses", f"{result['total_intereses']:,.2f} €")
        with col4:
            st.metric("Ahorro Intereses", f"{result['ahorro_intereses']:,.2f} €")
    
    else:
        stats = result['estadisticas']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Cuota Inicial Promedio",
                f"{stats['cuota_inicial_promedio']:,.2f} €",
                delta=f"± {stats['cuota_inicial_std']:,.2f} €"
            )
            st.metric(
                "Total Pagado Promedio",
                f"{stats['total_pagado_promedio']:,.2f} €",
                delta=f"± {stats['total_pagado_std']:,.2f} €"
            )
        
        with col2:
            st.metric(
                "Total Intereses Promedio",
                f"{stats['total_intereses_promedio']:,.2f} €",
                delta=f"± {stats['total_intereses_std']:,.2f} €"
            )
            st.metric(
                "Ahorro Intereses Promedio",
                f"{stats.get('ahorro_intereses_promedio', 0):,.2f} €"
            )
        
        # Risk analysis
        st.write("**📊 Análisis de Riesgo:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Escenario Optimista (P5)", f"{stats['total_pagado_p5']:,.2f} €")
        with col2:
            st.metric("Escenario Medio (P50)", f"{stats['total_pagado_p50']:,.2f} €")
        with col3:
            st.metric("Escenario Pesimista (P95)", f"{stats['total_pagado_p95']:,.2f} €")
    
    # Show injections if any
    if result['inyecciones']:
        st.write("**💰 Inyecciones de Capital:**")
        injections_df = pd.DataFrame([
            {
                'Mes': inj[0],
                'Cantidad (€)': f"{inj[1]:,.2f}",
                'Estrategia': inj[2]
            }
            for inj in result['inyecciones']
        ])
        st.dataframe(injections_df, use_container_width=True)

if __name__ == "__main__":
    mostrar_pagina_comparacion()