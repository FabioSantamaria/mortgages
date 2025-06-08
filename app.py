import streamlit as st
from pages_ui import max_price, simulation, early_payments, monte_carlo_page, initial_costs

# Streamlit App Configuration
st.set_page_config(
    page_title="Calculadora de Hipotecas", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏠 Calculadora de Hipotecas Avanzada")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una opción:",
    ["Máximo precio según sueldo", "Simulación de hipoteca", "Amortizaciones anticipadas", 
     "Monte Carlo - Euribor Estocástico", "Costes iniciales"]
)

# Route to appropriate page
if opcion == "Máximo precio según sueldo":
    max_price.show_page()
elif opcion == "Simulación de hipoteca":
    simulation.show_page()
elif opcion == "Amortizaciones anticipadas":
    early_payments.show_page()
elif opcion == "Monte Carlo - Euribor Estocástico":
    monte_carlo_page.show_page()
elif opcion == "Costes iniciales":
    initial_costs.show_page()

# Footer
st.markdown("---")
st.markdown(
    "💡 **Nota**: Esta calculadora proporciona estimaciones basadas en los parámetros introducidos. "
    "Consulta siempre con un profesional financiero para decisiones importantes."
)