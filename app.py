import streamlit as st
from pages_ui import max_price, simulation, early_payments, monte_carlo_page, initial_costs, mixed_mortgage_page, comparison_page
from modules.i18n import t, render_language_toggle

# Streamlit App Configuration
st.set_page_config(
    page_title="Calculadora de Hipotecas", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

render_language_toggle()
st.title(t('app.title', '🏠 Calculadora de Hipotecas Avanzada'))
st.markdown("---")

# Sidebar for navigation
st.sidebar.title(t('nav.title', 'Navegación'))
opcion = st.sidebar.selectbox(
    t('nav.select', 'Selecciona una opción:'),
    t('nav.options', [
        "Simulación de hipoteca fija", 
        "Amortizaciones hipoteca fija", 
        "Simulación de hipoteca variable",
        "Simulación de hipoteca mixta",
        "Comparación de Hipotecas", 
        "Costes iniciales", 
        "Máximo precio según sueldo"
    ])
)

# Route to appropriate page
if opcion == "Simulación de hipoteca fija":
    simulation.show_page()
elif opcion == "Amortizaciones hipoteca fija":
    early_payments.show_page()
elif opcion == "Simulación de hipoteca variable":
    monte_carlo_page.show_page()
elif opcion == "Simulación de hipoteca mixta":
    mixed_mortgage_page.show_page()
elif opcion == "Comparación de Hipotecas":
    comparison_page.show_page()
elif opcion == "Costes iniciales":
    initial_costs.show_page()
elif opcion == "Máximo precio según sueldo":
    max_price.show_page()

# Footer
st.markdown("---")
st.markdown(t('footer.note', "💡 **Nota**: Esta calculadora proporciona estimaciones basadas en los parámetros introducidos. "
    "Consulta siempre con un profesional financiero para decisiones importantes."))