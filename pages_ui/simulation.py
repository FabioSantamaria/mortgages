import streamlit as st
from modules.calculations import cuota_mensual, simulacion_hipoteca_simple
from modules.plotting import plot_mortgage_simulation
from modules.ui_components import create_mortgage_inputs, display_mortgage_summary

def show_page():
    st.header("📊 Simulación de hipoteca")
    
    capital_inicial, tasa_anual, plazo_anos, costes_fijos_mensuales = create_mortgage_inputs()
    mostrar_tabla = st.checkbox("Mostrar tabla detallada")
    
    if st.button("Simular hipoteca"):
        try:
            cuota_mensual_calc = cuota_mensual(capital_inicial, tasa_anual, plazo_anos * 12, costes_fijos_mensuales)
            
            # Run simulation
            df_simulacion = simulacion_hipoteca_simple(
                capital_inicial, tasa_anual, plazo_anos * 12, cuota_mensual_calc, costes_fijos_mensuales
            )
            
            # Calculate totals
            total_intereses = df_simulacion['Intereses_mensuales'].sum()
            total_costes_fijos = df_simulacion['Costes_fijos_mensuales'].sum()
            total_pagado = capital_inicial + total_intereses + total_costes_fijos
            
            # Display summary
            display_mortgage_summary(
                capital_inicial, tasa_anual, plazo_anos, 
                cuota_mensual_calc, total_intereses, total_pagado, costes_fijos_mensuales
            )
            
            # Plot results
            fig = plot_mortgage_simulation(df_simulacion)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show table if requested
            if mostrar_tabla:
                st.subheader("Tabla de amortización")
                st.dataframe(df_simulacion, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error en la simulación: {str(e)}")