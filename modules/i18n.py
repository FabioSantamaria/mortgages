import streamlit as st

# Simple i18n bundles for common UI text
LANG_BUNDLES = {
    'es': {
        'app.title': '🏠 Calculadora de Hipotecas Avanzada',
        'nav.title': 'Navegación',
        'nav.select': 'Selecciona una opción:',
        'nav.options': [
            'Simulación de hipoteca fija',
            'Amortizaciones hipoteca fija',
            'Simulación de hipoteca variable',
            'Simulación de hipoteca mixta',
            'Comparación de Hipotecas',
            'Costes iniciales',
            'Máximo precio según sueldo'
        ],
        'sidebar.language': 'Idioma',
        'language.es': 'Español',
        'language.en': 'English',
        'footer.note': (
            '💡 **Nota**: Esta calculadora proporciona estimaciones basadas en los parámetros introducidos. '
            'Consulta siempre con un profesional financiero para decisiones importantes.'
        ),
        # Comparison page
        'comparison.title': '🏦 Comparación de Hipotecas',
        'comparison.description': 'Compara diferentes tipos de hipotecas (fija, variable, mixta) para un banco específico',
        'comparison.bank.info.title': '📋 Información del Banco',
        'comparison.bank.name.label': 'Nombre del Banco',
        'comparison.bank.name.placeholder': 'Ej: Banco Santander, BBVA, CaixaBank...',
        'comparison.bank.name.help': 'Introduce el nombre del banco para identificar las simulaciones',
        'comparison.bank.name.warning': '⚠️ Por favor, introduce el nombre del banco para continuar',
        'comparison.sim.config.title': '⚙️ Configuración de Simulaciones',
        'comparison.add.new.sim.expander': '➕ Añadir Nueva Simulación',
        'comparison.simulations.configured.title': '📊 Simulaciones Configuradas',
        'comparison.run.all.button': '🚀 Ejecutar Todas las Simulaciones',
        'comparison.no.sims.info': 'ℹ️ No hay simulaciones configuradas. Añade al menos una simulación para comenzar.',
        'comparison.results.title': '📊 Resultados de Comparación',
        'comparison.summary.title': '📋 Resumen Comparativo',
        'comparison.export.excel': '📊 Exportar a Excel',
        'comparison.download.excel': '⬇️ Descargar Excel',
        'comparison.export.csv': '📄 Exportar a CSV',
        'comparison.download.csv': '⬇️ Descargar CSV',
        'comparison.charts.title': '📈 Gráficos Comparativos',
        'comparison.details.title': '🔍 Detalles por Simulación',
        # Form strings
        'form.sim.type': 'Tipo de Hipoteca',
        'form.sim.type.help': 'Selecciona el tipo de hipoteca a simular',
        'form.parametros.sim.subheader': 'Parámetros de Simulación',
        'form.sim.name': 'Nombre de la Simulación',
        'form.sim.name.placeholder': 'Ej: Fija 3.5%, Variable Euribor+1.2%',
        'form.sim.name.help': 'Nombre descriptivo para identificar esta simulación',
        'form.basic.params': 'Parámetros Básicos',
        'form.capital': 'Capital (€)',
        'form.term_years': 'Plazo (años)',
        'form.fixed.rate': 'Tasa de Interés (%)',
        'form.variable.params': 'Parámetros Variable',
        'form.spread': 'Spread sobre Euribor (%)',
        'form.initial.euribor': 'Euribor Inicial (%)',
        'form.distribution.type': 'Tipo de Distribución del Euribor',
        'form.num.simulations': 'Número de Simulaciones Monte Carlo',
        'form.mixed.params': 'Parámetros Mixta',
        'form.mixed.fixed.rate': 'Tasa Fija (%)',
        'form.fixed.years': 'Años con Tasa Fija',
        'form.mixed.variable.spread': 'Spread Variable (%)',
        'form.add.sim.submit': '🚀 Añadir simulación a la cesta',
        'form.sim.name.required': '❌ El nombre de la simulación es obligatorio',
        'form.sim.name.duplicate': '❌ Ya existe una simulación con ese nombre',
        'form.delete': '🗑️ Eliminar',
    },
    'en': {
        'app.title': '🏠 Advanced Mortgage Calculator',
        'nav.title': 'Navigation',
        'nav.select': 'Choose an option:',
        'nav.options': [
            'Fixed-rate mortgage simulation',
            'Early payments – fixed mortgage',
            'Variable-rate mortgage simulation',
            'Mixed-rate mortgage simulation',
            'Mortgage Comparison',
            'Initial costs',
            'Maximum price by salary'
        ],
        'sidebar.language': 'Language',
        'language.es': 'Spanish',
        'language.en': 'English',
        'footer.note': (
            '💡 Note: This calculator provides estimates based on input parameters. '
            'Always consult a financial professional for important decisions.'
        ),
        # Comparison page
        'comparison.title': '🏦 Mortgage Comparison',
        'comparison.description': 'Compare different mortgage types (fixed, variable, mixed) for a specific bank',
        'comparison.bank.info.title': '📋 Bank Information',
        'comparison.bank.name.label': 'Bank Name',
        'comparison.bank.name.placeholder': 'e.g., Santander, BBVA, CaixaBank...',
        'comparison.bank.name.help': 'Enter the bank name to label simulations',
        'comparison.bank.name.warning': '⚠️ Please enter the bank name to continue',
        'comparison.sim.config.title': '⚙️ Simulation Configuration',
        'comparison.add.new.sim.expander': '➕ Add New Simulation',
        'comparison.simulations.configured.title': '📊 Configured Simulations',
        'comparison.run.all.button': '🚀 Run All Simulations',
        'comparison.no.sims.info': 'ℹ️ No simulations configured. Add at least one to start.',
        'comparison.results.title': '📊 Comparison Results',
        'comparison.summary.title': '📋 Comparative Summary',
        'comparison.export.excel': '📊 Export to Excel',
        'comparison.download.excel': '⬇️ Download Excel',
        'comparison.export.csv': '📄 Export to CSV',
        'comparison.download.csv': '⬇️ Download CSV',
        'comparison.charts.title': '📈 Comparative Charts',
        'comparison.details.title': '🔍 Simulation Details',
        # Form strings
        'form.sim.type': 'Mortgage Type',
        'form.sim.type.help': 'Choose the type of mortgage to simulate',
        'form.parametros.sim.subheader': 'Simulation Parameters',
        'form.sim.name': 'Simulation Name',
        'form.sim.name.placeholder': 'E.g.: Fixed 3.5%, Variable Euribor+1.2%',
        'form.sim.name.help': 'Descriptive name to identify this simulation',
        'form.basic.params': 'Basic Parameters',
        'form.capital': 'Principal (€)',
        'form.term_years': 'Term (years)',
        'form.fixed.rate': 'Interest Rate (%)',
        'form.variable.params': 'Variable Parameters',
        'form.spread': 'Spread over Euribor (%)',
        'form.initial.euribor': 'Initial Euribor (%)',
        'form.distribution.type': 'Euribor Distribution Type',
        'form.num.simulations': 'Number of Monte Carlo Simulations',
        'form.mixed.params': 'Mixed Parameters',
        'form.mixed.fixed.rate': 'Fixed Rate (%)',
        'form.fixed.years': 'Years at Fixed Rate',
        'form.mixed.variable.spread': 'Variable Spread (%)',
        'form.add.sim.submit': '🚀 Add simulation to basket',
        'form.sim.name.required': '❌ Simulation name is required',
        'form.sim.name.duplicate': '❌ A simulation with this name already exists',
        'form.delete': '🗑️ Delete',
    }
}


def get_language() -> str:
    """Return current UI language, defaulting to Spanish."""
    return st.session_state.get('ui_lang', 'es')


def set_language(lang: str) -> None:
    if lang in LANG_BUNDLES:
        st.session_state['ui_lang'] = lang


def t(key: str, default: str = None):
    lang = get_language()
    bundle = LANG_BUNDLES.get(lang, {})
    return bundle.get(key, default if default is not None else key)


def render_language_toggle():
    """Render a language selector in the sidebar and set the language."""
    lang = get_language()
    label = t('sidebar.language', 'Language')
    options = [(t('language.es', 'Spanish'), 'es'), (t('language.en', 'English'), 'en')]
    labels = [opt[0] for opt in options]
    values = {opt[0]: opt[1] for opt in options}
    selected_label = st.sidebar.selectbox(label, labels, index=0 if lang == 'es' else 1)
    set_language(values[selected_label])