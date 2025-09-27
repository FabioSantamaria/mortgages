import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import io
from datetime import datetime

from .calculations import (
    cuota_mensual, 
    simulacion_hipoteca_simple,
    simulacion_hipoteca_multiple_inyeccion,
    calcular_ahorro_intereses_multiple_inyeccion
)
from .monte_carlo import (
    run_monte_carlo_simulation,
    calculate_simulation_statistics
)
from .mixed_mortgage import (
    run_mixed_monte_carlo_simulation,
    calculate_mixed_simulation_statistics
)

class MortgageComparison:
    """Class to handle mortgage comparisons between different simulation types"""
    
    def __init__(self, bank_name: str):
        self.bank_name = bank_name
        self.simulations = []
        self.results = {}
        
    def add_simulation(self, sim_config: Dict[str, Any]) -> None:
        """Add a simulation configuration to the comparison"""
        # Ensure injections are isolated per simulation to avoid leakage
        if 'inyecciones' in sim_config and sim_config['inyecciones'] is not None:
            import copy
            sim_config['inyecciones'] = copy.deepcopy(sim_config['inyecciones'])
        self.simulations.append(sim_config)
    
    def run_fixed_simulation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a fixed rate mortgage simulation"""
        capital = config['capital']
        tasa_interes = config['tasa_interes']
        plazo_anos = config['plazo_anos']
        inyecciones = config.get('inyecciones', [])
        
        plazo_meses = plazo_anos * 12
        cuota_inicial = cuota_mensual(capital, tasa_interes, plazo_meses)
        
        if inyecciones:
            df_simulation = simulacion_hipoteca_multiple_inyeccion(
                capital, tasa_interes, plazo_meses, cuota_inicial, inyecciones
            )
            ahorro_total, intereses_sin, intereses_con = calcular_ahorro_intereses_multiple_inyeccion(
                capital, tasa_interes, plazo_meses, cuota_inicial, inyecciones
            )
        else:
            df_simulation = simulacion_hipoteca_simple(
                capital, tasa_interes, plazo_meses, cuota_inicial
            )
            ahorro_total, intereses_sin, intereses_con = 0, None, None

        total_intereses = df_simulation['Intereses_mensuales'].sum()
        total_pagado = df_simulation['Cuota_mensual'].sum()
        meses_totales = len(df_simulation)
        
        return {
            'type': 'fija',
            'name': config['name'],
            'simulation_data': df_simulation,
            'summary': {
                'capital_inicial': capital,
                'tasa_interes': tasa_interes,
                'plazo_anos': plazo_anos,
                'cuota_mensual': cuota_inicial,
                'total_intereses': total_intereses,
                'total_pagado': total_pagado,
                'meses_totales': meses_totales,
                'ahorro_intereses': ahorro_total,
                'intereses_sin_inyecciones': intereses_sin,
                'intereses_con_inyecciones': intereses_con,
                'inyecciones_totales': sum([inj['capital_inyectado'] for inj in inyecciones])
            }
        }
    
    def run_variable_simulation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a variable rate mortgage simulation with Monte Carlo"""
        capital = config['capital']
        spread = config['spread']
        plazo_anos = config['plazo_anos']
        euribor_inicial = config['euribor_inicial']
        distribution_type = config['distribucion_tipo']
        parametros_distribucion = config['parametros_distribucion']
        num_simulaciones = config['num_simulaciones']
        # Use local copy of injections to avoid accidental mutations
        inyecciones = [dict(inj) for inj in config.get('inyecciones', [])]
        
        # Map parameter names
        dist_params = {}
        if distribution_type == 'Gaussian':
            dist_params = {
                'volatility': parametros_distribucion.get('desviacion', 1.0),
                'drift': parametros_distribucion.get('media', 3.0) - euribor_inicial
            }
        elif distribution_type == 'Mean Reverting':
            dist_params = {
                'mean_level': parametros_distribucion.get('media_largo_plazo', 3.0),
                'reversion_speed': parametros_distribucion.get('velocidad_reversion', 0.1),
                'volatility': parametros_distribucion.get('volatilidad', 0.5)
            }
        elif distribution_type == 'Uniform Random Walk':
            dist_params = {
                'max_change': max(abs(parametros_distribucion.get('cambio_min', -0.5)),
                                abs(parametros_distribucion.get('cambio_max', 0.5)))
            }
        
        df_all_sims = run_monte_carlo_simulation(
            capital, spread, plazo_anos, euribor_inicial,
            distribution_type, num_simulaciones, inyecciones, **dist_params
        )
        
        stats_df = calculate_simulation_statistics(df_all_sims)
        
        stats_df.rename(columns={
            'Cuota_mensual_<lambda_0>': 'Cuota_mensual_percentile5',
            'Cuota_mensual_<lambda_1>': 'Cuota_mensual_percentile95',
            'Intereses_mensuales_<lambda_0>': 'Intereses_mensuales_percentile5',
            'Intereses_mensuales_<lambda_1>': 'Intereses_mensuales_percentile95',
            'Amortizacion_mensual_<lambda_0>': 'Amortizacion_mensual_percentile5',
            'Amortizacion_mensual_<lambda_1>': 'Amortizacion_mensual_percentile95',
            'Euribor_<lambda_0>': 'Euribor_percentile5',
            'Euribor_<lambda_1>': 'Euribor_percentile95',
        }, inplace=True)

        # Calculate per-simulation aggregates for summary
        by_sim = df_all_sims.groupby('Simulation')
        total_intereses_promedio = by_sim['Intereses_mensuales'].sum().mean()
        total_pagado_promedio = by_sim['Cuota_mensual'].sum().mean()
        meses_totales_promedio = by_sim.size().mean()
        
        return {
            'type': 'variable',
            'name': config['name'],
            'simulation_data': df_all_sims,
            'statistics': stats_df,
            'summary': {
                'capital_inicial': capital,
                'spread': spread,
                'euribor_inicial': euribor_inicial,
                'plazo_anos': plazo_anos,
                'num_simulaciones': num_simulaciones,
                'distribucion_detalle': distribution_type,  # English mapping for clarity
                'total_intereses_promedio': total_intereses_promedio,
                'total_pagado_promedio': total_pagado_promedio,
                'meses_totales_promedio': meses_totales_promedio,
                'inyecciones_totales': sum([inj['capital_inyectado'] for inj in inyecciones])
            }
        }
    
    def run_mixed_simulation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a mixed rate mortgage simulation with Monte Carlo"""
        capital = config['capital']
        tasa_fija = config['tasa_fija']
        spread = config['spread']
        plazo_anos = config['plazo_anos']
        anos_fijos = config['anos_fijos']
        euribor_inicial = config['euribor_inicial']
        distribution_type = config['distribucion_tipo']
        parametros_distribucion = config['parametros_distribucion']
        num_simulaciones = config['num_simulaciones']
        # Use local copy of injections to avoid accidental mutations
        inyecciones = [dict(inj) for inj in config.get('inyecciones', [])]
        
        # Map parameter names
        dist_params = {}
        if distribution_type == 'Gaussian':
            dist_params = {
                'volatility': parametros_distribucion.get('desviacion', 1.0),
                'drift': parametros_distribucion.get('media', 3.0) - euribor_inicial
            }
        elif distribution_type == 'Mean Reverting':
            dist_params = {
                'mean_level': parametros_distribucion.get('media_largo_plazo', 3.0),
                'reversion_speed': parametros_distribucion.get('velocidad_reversion', 0.1),
                'volatility': parametros_distribucion.get('volatilidad', 0.5)
            }
        elif distribution_type == 'Uniform Random Walk':
            dist_params = {
                'max_change': max(abs(parametros_distribucion.get('cambio_min', -0.5)),
                                abs(parametros_distribucion.get('cambio_max', 0.5)))
            }
        
        df_all_sims = run_mixed_monte_carlo_simulation(
            capital, tasa_fija, spread, plazo_anos, anos_fijos,
            euribor_inicial, distribution_type, num_simulaciones, inyecciones, **dist_params
        )
        
        stats_df = calculate_mixed_simulation_statistics(df_all_sims)
        
        stats_df.rename(columns={
            'Cuota_mensual_<lambda_0>': 'Cuota_mensual_percentile5',
            'Cuota_mensual_<lambda_1>': 'Cuota_mensual_percentile95',
            'Intereses_mensuales_<lambda_0>': 'Intereses_mensuales_percentile5',
            'Intereses_mensuales_<lambda_1>': 'Intereses_mensuales_percentile95',
            'Amortizacion_mensual_<lambda_0>': 'Amortizacion_mensual_percentile5',
            'Amortizacion_mensual_<lambda_1>': 'Amortizacion_mensual_percentile95',
            'Euribor_<lambda_0>': 'Euribor_percentile5',
            'Euribor_<lambda_1>': 'Euribor_percentile95',
            'Tasa_Anual_<lambda_0>': 'Tasa_anual_percentile5',
            'Tasa_Anual_<lambda_1>': 'Tasa_anual_percentile95',
            'Tipo_Periodo_<lambda>': 'Tipo_periodo',
        }, inplace=True)


        # Calculate per-simulation aggregates for summary
        by_sim = df_all_sims.groupby('Simulation')
        total_intereses_promedio = by_sim['Intereses_mensuales'].sum().mean()
        total_pagado_promedio = by_sim['Cuota_mensual'].sum().mean()
        meses_totales_promedio = by_sim.size().mean()
        
        return {
            'type': 'mixta',
            'name': config['name'],
            'simulation_data': df_all_sims,
            'statistics': stats_df,
            'summary': {
                'capital_inicial': capital,
                'tasa_fija': tasa_fija,
                'anos_fijos': anos_fijos,
                'spread': spread,
                'euribor_inicial': euribor_inicial,
                'plazo_anos': plazo_anos,
                'num_simulaciones': num_simulaciones,
                'distribucion_detalle': distribution_type,  # English mapping for clarity
                'total_intereses_promedio': total_intereses_promedio,
                'total_pagado_promedio': total_pagado_promedio,
                'meses_totales_promedio': meses_totales_promedio,
                'inyecciones_totales': sum([inj['capital_inyectado'] for inj in inyecciones])
            }
        }
    
    def run_all_simulations(self) -> Dict[str, Any]:
        """Run all configured simulations and return results"""
        results = {}
        
        for sim_config in self.simulations:
            sim_type = sim_config['type']
            sim_name = sim_config['name']
            
            try:
                if sim_type == 'fija':
                    result = self.run_fixed_simulation(sim_config)
                elif sim_type == 'variable':
                    result = self.run_variable_simulation(sim_config)
                elif sim_type == 'mixta':
                    result = self.run_mixed_simulation(sim_config)
                else:
                    raise ValueError(f"Tipo de simulación no soportado: {sim_type}")
                
                results[sim_name] = result
                
            except Exception as e:
                results[sim_name] = {
                    'type': sim_type,
                    'name': sim_name,
                    'error': str(e)
                }
        
        self.results = results
        return results
    
    def get_comparison_summary(self) -> pd.DataFrame:
        """Generate a summary comparison table of all simulations"""
        if not self.results:
            return pd.DataFrame()
        
        summary_data = []
        
        for sim_name, result in self.results.items():
            if 'error' in result:
                continue
                
            summary = result['summary']
            sim_type = result['type']
            
            row = {
                'Simulación': sim_name,
                'Tipo': sim_type.title(),
                'Capital Inicial (€)': f"{summary['capital_inicial']:,.0f}",
                'Plazo (años)': summary['plazo_anos']
            }
            
            if sim_type == 'fija':
                row.update({
                    'Tasa/Spread (%)': f"{summary['tasa_interes']:.2f}",
                    'Cuota Mensual (€)': f"{summary['cuota_mensual']:,.2f}",
                    'Total Intereses (€)': f"{summary['total_intereses']:,.0f}",
                    'Total Pagado (€)': f"{summary['total_pagado']:,.0f}",
                    'Meses Totales': summary['meses_totales']
                })
            else:  # variable or mixta
                if sim_type == 'mixta':
                    rate_info = f"Fija: {summary['tasa_fija']:.2f}% ({summary['anos_fijos']}a), Spread: {summary['spread']:.2f}%"
                else:
                    rate_info = f"Spread: {summary['spread']:.2f}%"
                
                # Include distribution type in summary for variable and mixed
                rate_info = rate_info + f" | Dist: {summary.get('distribution_type', '')}"
                
                row.update({
                    'Tasa/Spread (%)': rate_info,
                    'Cuota Mensual (€)': 'Variable',
                    'Total Intereses (€)': f"{summary['total_intereses_promedio']:,.0f} (promedio)",
                    'Total Pagado (€)': f"{summary['total_pagado_promedio']:,.0f} (promedio)",
                    'Meses Totales': f"{summary['meses_totales_promedio']:.0f} (promedio)"
                })
            
            if summary.get('inyecciones_totales', 0) > 0:
                row['Inyecciones Totales (€)'] = f"{summary['inyecciones_totales']:,.0f}"
                row['Ahorro Intereses (€)'] = f"{summary.get('ahorro_intereses', 0):,.0f}"
            else:
                row['Inyecciones Totales (€)'] = "0"
                row['Ahorro Intereses (€)'] = "0"
            
            summary_data.append(row)
        
        return pd.DataFrame(summary_data)
    
    def export_to_excel(self, filename: Optional[str] = None) -> io.BytesIO:
        """Export all simulation results to Excel file"""
        if not self.results:
            raise ValueError("No hay resultados para exportar")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparacion_hipotecas_{self.bank_name}_{timestamp}.xlsx"
        
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = self.get_comparison_summary()
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Individual simulation sheets
            for sim_name, result in self.results.items():
                if 'error' in result:
                    continue
                
                sheet_name = sim_name[:31]  # Excel sheet name limit
                
                if result['type'] == 'fija':
                    result['simulation_data'].to_excel(writer, sheet_name=sheet_name, index=False)
                else:  # variable or mixta
                    # For Monte Carlo simulations, export statistics
                    if 'statistics' in result:
                        result['statistics'].to_excel(writer, sheet_name=f"{sheet_name}_stats", index=True)
                    
                    # Export a sample of simulation data (first 1000 rows to avoid Excel limits)
                    sample_data = result['simulation_data'].head(1000)
                    sample_data.to_excel(writer, sheet_name=f"{sheet_name}_sample", index=False)
        
        buffer.seek(0)
        return buffer
    
    def export_to_csv(self, filename: Optional[str] = None) -> io.StringIO:
        """Export comparison summary to CSV file"""
        if not self.results:
            raise ValueError("No hay resultados para exportar")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparacion_hipotecas_{self.bank_name}_{timestamp}.csv"
        
        summary_df = self.get_comparison_summary()
        
        buffer = io.StringIO()
        summary_df.to_csv(buffer, index=False, encoding='utf-8')
        buffer.seek(0)
        
        return buffer