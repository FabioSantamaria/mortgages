import math
import pandas as pd
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

def calcular_plazo(capital, tasa, cuota):
    """Calculate remaining months to pay the loan"""
    if capital <= 0:
        return 0
    
    tasa_mensual = tasa / 1200
    if cuota <= capital * tasa_mensual:
        raise ValueError("La cuota no cubre los intereses mínimos")
    
    plazo = -math.log(1 - capital * tasa_mensual / cuota) / math.log(1 + tasa_mensual)
    return max(math.ceil(plazo), 1)

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

def simulacion_hipoteca_multiple_inyeccion(capital_inicial, tasa, plazo_inicial,
                                            cuota_inicial, inyecciones):
    """
    Simulación robusta de hipoteca con múltiples inyecciones de capital y tipos de reducción
    definidos para cada inyección a lo largo del tiempo.
    """
    # Validaciones iniciales generales
    if capital_inicial <= 0:
        raise ValueError("El capital inicial debe ser positivo")
    if plazo_inicial <= 0:
        raise ValueError("El plazo inicial debe ser positivo")
    if cuota_inicial <= 0:
        raise ValueError("La cuota inicial debe ser positiva")

    # Validaciones de las inyecciones
    if not isinstance(inyecciones, list):
        raise TypeError("Las inyecciones deben ser una lista de diccionarios")
    
    opcion_reduccion_actual = None
    for inyeccion in inyecciones:
        if not isinstance(inyeccion, dict):
            raise TypeError("Cada inyección debe ser un diccionario")
        if 'mes_inyeccion' not in inyeccion:
            raise ValueError("Cada inyección debe tener 'mes_inyeccion'")
        if 'capital_inyectado' not in inyeccion:
            inyeccion['capital_inyectado'] = 0 # Asumir 0 si no se especifica
        if 'tipo_inyeccion' in inyeccion and inyeccion['tipo_inyeccion'] not in ['cuota', 'plazo']:
            raise ValueError("Tipo de inyección debe ser 'cuota' o 'plazo' o None")

    registros = []
    capital_pendiente = capital_inicial
    cuota_actual = cuota_inicial
    plazo_restante = plazo_inicial
    mes_actual = 0

    for mes in range(1, plazo_inicial + 1):
        mes_actual += 1

        # Verificar si hay inyección/acción este mes
        inyeccion_mes = 0
        tipo_inyeccion_mes = None
        for inyeccion in inyecciones:
            if inyeccion['mes_inyeccion'] == mes_actual:
                inyeccion_mes = inyeccion['capital_inyectado']
                tipo_inyeccion_mes = inyeccion['tipo_inyeccion']

        # Aplicar inyección si existe y validar que no supere el capital restante
        if inyeccion_mes > 0:
            if inyeccion_mes > capital_pendiente:
                raise ValueError(f"Inyección en el mes {mes_actual} supera el capital pendiente.")
            capital_pendiente -= inyeccion_mes

        if capital_pendiente <= 0:
            registros.append({
                'Mes': mes_actual,
                'Capital_pendiente': 0,
                'Cuota_mensual': 0,
                'Intereses_mensuales': 0,
                'Amortizacion_mensual': 0,
                'Inyeccion_capital': inyeccion_mes,
                'Tipo_Reduccion': tipo_inyeccion_mes if tipo_inyeccion_mes else opcion_reduccion_actual
            })
            break

        interes = intereses_mensuales(capital_pendiente, tasa)
        amortizacion = min(cuota_actual - interes, capital_pendiente)

        registros.append({
            'Mes': mes_actual,
            'Capital_pendiente': capital_pendiente,
            'Cuota_mensual': cuota_actual,
            'Intereses_mensuales': interes,
            'Amortizacion_mensual': amortizacion,
            'Inyeccion_capital': inyeccion_mes,
            'Tipo_Reduccion': tipo_inyeccion_mes if tipo_inyeccion_mes else opcion_reduccion_actual
        })

        capital_pendiente -= amortizacion

        # Recalcular cuota o plazo si hubo inyección o cambio de tipo y aún queda préstamo
        if (inyeccion_mes > 0 or tipo_inyeccion_mes) and capital_pendiente > 0:
            if tipo_inyeccion_mes:
                opcion_reduccion_actual = tipo_inyeccion_mes

            nuevo_capital = capital_pendiente

            if opcion_reduccion_actual == 'cuota':
                plazo_restante_recalculo = max(plazo_inicial - mes_actual, 1)
                cuota_actual = cuota_mensual(nuevo_capital, tasa, plazo_restante_recalculo)
            elif opcion_reduccion_actual == 'plazo':
                cuota_actual_recalculo = cuota_actual # Mantenemos la cuota actual RECALCULADA previamente por el euribor
                plazo_restante = calcular_plazo(nuevo_capital, tasa, cuota_actual_recalculo) # Usar la tasa anual ACTUAL
                plazo_inicial = mes_actual + plazo_restante # Ajustamos plazo inicial para futuras inyecciones

    return pd.DataFrame(registros)

def calcular_ahorro_intereses_multiple_inyeccion(capital_inicial, tasa, plazo_inicial,
                                                 cuota_inicial, inyecciones):
    """Calculate total interest savings from multiple injections"""
    # Simulación con inyecciones
    df_con_inyecciones = simulacion_hipoteca_multiple_inyeccion(
        capital_inicial, tasa, plazo_inicial, cuota_inicial, inyecciones)
    intereses_con_inyecciones = df_con_inyecciones['Intereses_mensuales'].sum()

    # Simulación base SIN inyecciones
    df_sin_inyecciones = simulacion_hipoteca_multiple_inyeccion(
        capital_inicial, tasa, plazo_inicial, cuota_inicial, inyecciones=[])
    intereses_sin_inyecciones = df_sin_inyecciones['Intereses_mensuales'].sum()

    ahorro_intereses = intereses_sin_inyecciones - intereses_con_inyecciones
    return ahorro_intereses, intereses_sin_inyecciones, intereses_con_inyecciones
