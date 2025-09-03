import streamlit as st
import pandas as pd

def create_mortgage_inputs():
    """Create standard mortgage input components"""
    col1, col2 = st.columns(2)
    
    with col1:
        capital_inicial = st.number_input("Capital inicial (€)", min_value=10000, value=200000, step=5000)
        tasa_anual = st.number_input("Tasa de interés anual (%)", min_value=0.5, max_value=10.0, value=2.00, step=0.01)
    
    with col2:
        plazo_anos = st.slider("Plazo del préstamo (años)", 5, 40, 20, 1)
    
    return capital_inicial, tasa_anual, plazo_anos

def display_mortgage_summary(capital_inicial, tasa_anual, plazo_anos, cuota_mensual_calc, total_intereses, total_pagado):
    """Display mortgage summary metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Capital inicial", f"{capital_inicial:,.0f} €")
    with col2:
        st.metric("Cuota mensual", f"{cuota_mensual_calc:,.2f} €")
    with col3:
        st.metric("Total intereses", f"{total_intereses:,.2f} €")
    with col4:
        st.metric("Total pagado", f"{total_pagado:,.2f} €")

def create_early_payment_inputs(plazo_anos):
    """Create early payment input components"""
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
    return st.session_state.inyecciones