import streamlit as st
import pandas as pd
from modules.cost_estimation import calcular_costes_iniciales_estimados
from modules.plotting import plot_cost_breakdown

def show_page():
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
        fig_costes = plot_cost_breakdown(costes)
        st.plotly_chart(fig_costes, use_container_width=True)