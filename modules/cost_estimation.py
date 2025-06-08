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