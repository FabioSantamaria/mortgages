import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math
import numpy as np

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
        line=dict(color='black'),
        name='Intereses Mensuales'
    ))
    
    fig.update_layout(
        title='Simulación de Hipoteca',
        xaxis_title="Mes",
        yaxis_title="Importe (euros)",
        font_family="Arial",
        font_color="black",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="white",
            bordercolor="black",
            borderwidth=1
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
    ["Máximo precio según sueldo", "Simulación de hipoteca", "Costes iniciales"]
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