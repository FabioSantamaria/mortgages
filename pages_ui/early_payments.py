import streamlit as st
import pandas as pd
from modules.calculations import cuota_mensual, simulacion_hipoteca_multiple_inyeccion, calcular_ahorro_intereses_multiple_inyeccion
from modules.plotting import plot_comparacion
from modules.ui_components import create_mortgage_inputs, create_early_payment_inputs

def show_page():
    st.header("💰 Amortizaciones anticipadas")

    # Mortgage inputs
    capital_inicial, tasa_anual, plazo_anos, costes_fijos_mensuales = create_mortgage_inputs()

    # Early payment inputs
    inyecciones = create_early_payment_inputs(plazo_anos)
                
    # Botón para simular
    if st.button("🚀 Simular con amortizaciones anticipadas"):
        if not inyecciones:
            st.warning("Agrega al menos una amortización anticipada para comparar.")
        else:
            plazo_meses = plazo_anos * 12
            cuota_inicial = cuota_mensual(capital_inicial, tasa_anual, plazo_meses, costes_fijos_mensuales)
            
            try:
                # Simulación original (sin inyecciones)
                df_original = simulacion_hipoteca_multiple_inyeccion(
                    capital_inicial, tasa_anual, plazo_meses, cuota_inicial, [])
                
                # Simulación con inyecciones
                df_con_inyecciones = simulacion_hipoteca_multiple_inyeccion(
                    capital_inicial, tasa_anual, plazo_meses, cuota_inicial, inyecciones)
                
                # Calcular ahorros
                ahorro_total, intereses_sin, intereses_con = calcular_ahorro_intereses_multiple_inyeccion(
                    capital_inicial, tasa_anual, plazo_meses, cuota_inicial, inyecciones)
                
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
                    st.write(f"- Total pagado: {intereses_con + capital_inicial:,.2f} €")
                    meses_ahorrados = len(df_original) - len(df_con_inyecciones)
                    st.write(f"- Tiempo ahorrado: {meses_ahorrados} meses ({meses_ahorrados/12:.1f} años)")
                
            except Exception as e:
                st.error(f"Error en la simulación: {str(e)}")