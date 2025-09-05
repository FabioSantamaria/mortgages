import streamlit as st
from modules.calculations import maximo_precio_piso_segun_sueldo, cuota_mensual

def show_page():
    st.header("💰 Máximo precio de vivienda según sueldo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sueldo_neto = st.number_input("Sueldo neto mensual (€)", min_value=1000, value=4000, step=100)
        relacion_cuota = st.slider("Porcentaje máximo del sueldo para la cuota", 0.2, 0.5, 0.33, 0.01)
        porcentaje_entrada = st.slider("Porcentaje de entrada (%)", 10, 30, 20, 1)
    
    with col2:
        tasa_interes = st.number_input("Tasa de interés anual (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.1)
        plazo_anos = st.slider("Plazo del préstamo (años)", 10, 40, 30, 1)
        costes_fijos_mensuales = st.number_input("Costes fijos mensuales (€)", min_value=0, value=50, step=10, help="Seguros obligatorios, comisiones, etc.")
    
    if st.button("Calcular precio máximo"):
        precio_maximo = maximo_precio_piso_segun_sueldo(
            sueldo_neto, relacion_cuota, porcentaje_entrada, tasa_interes, plazo_anos * 12, costes_fijos_mensuales
        )
        
        if precio_maximo > 0:
            st.success(f"**Precio máximo de vivienda: {precio_maximo:,.0f} €**")
            
            # Desglose
            entrada_necesaria = precio_maximo * (porcentaje_entrada / 100)
            capital_prestamo = precio_maximo - entrada_necesaria
            cuota_mensual_calc = cuota_mensual(capital_prestamo, tasa_interes, plazo_anos * 12, costes_fijos_mensuales)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Entrada necesaria", f"{entrada_necesaria:,.0f} €")
            with col2:
                st.metric("Capital del préstamo", f"{capital_prestamo:,.0f} €")
            with col3:
                st.metric("Cuota mensual", f"{cuota_mensual_calc:,.0f} €")
            with col4:
                st.metric("Costes fijos/mes", f"{costes_fijos_mensuales:,.0f} €")
        else:
            st.error("⚠️ Los costes fijos mensuales son demasiado altos para el sueldo disponible. Reduce los costes fijos o aumenta el porcentaje del sueldo destinado a la hipoteca.")