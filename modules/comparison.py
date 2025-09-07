import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import io

from .calculations import (
    cuota_mensual,
    simulacion_hipoteca_multiple_inyeccion
)
from .monte_carlo import (
    generate_euribor_scenario,
    simulacion_hipoteca_variable_montecarlo,
    run_monte_carlo_simulation,
    calculate_simulation_statistics
)
from .mixed_mortgage import (
    simulacion_hipoteca_mixta,
    run_mixed_monte_carlo_simulation,
    calculate_mixed_simulation_statistics
)

class MortgageComparison:
    """Class to handle multiple mortgage simulation comparisons"""
    
    def __init__(self, bank_name: str):
        self.bank_name = bank_name
        self.simulations = {}
        self.results = {}
    
    def add_fixed_simulation(self, 
                           name: str,
                           capital: float,
                           tasa_interes: float,
                           plazo_anos: int,
                           inyecciones: Optional[List[Tuple[int, float, str]]] = None) -> None:
        """Add a fixed rate mortgage simulation"""
        
        self.simulations[name] = {
            'type': 'fixed',
            'capital': capital,
            'tasa_interes': tasa_interes,
            'plazo_anos': plazo_anos,
            'inyecciones': inyecciones or []
        }
    
    def add_variable_simulation(self,
                              name: str,
                              capital: float,
                              spread: float,
                              plazo_anos: int,
                              euribor_inicial: float,
                              distribucion_tipo: str,
                              parametros_distribucion: Dict,
                              num_simulaciones: int = 1000,
                              inyecciones: Optional[List[Tuple[int, float, str]]] = None) -> None:
        """Add a variable rate mortgage Monte Carlo simulation"""
        
        self.simulations[name] = {
            'type': 'variable',
            'capital': capital,
            'spread': spread,
            'plazo_anos': plazo_anos,
            'euribor_inicial': euribor_inicial,
            'distribucion_tipo': distribucion_tipo,
            'parametros_distribucion': parametros_distribucion,
            'num_simulaciones': num_simulaciones,
            'inyecciones': inyecciones or []
        }
    
    def add_mixed_simulation(self,
                           name: str,
                           capital: float,
                           tasa_fija: float,
                           anos_fijos: int,
                           spread: float,
                           plazo_anos: int,
                           euribor_inicial: float,
                           distribucion_tipo: str,
                           parametros_distribucion: Dict,
                           num_simulaciones: int = 1000,
                           inyecciones: Optional[List[Tuple[int, float, str]]] = None) -> None:
        """Add a mixed rate mortgage Monte Carlo simulation"""
        
        self.simulations[name] = {
            'type': 'mixed',
            'capital': capital,
            'tasa_fija': tasa_fija,
            'anos_fijos': anos_fijos,
            'spread': spread,
            'plazo_anos': plazo_anos,
            'euribor_inicial': euribor_inicial,
            'distribucion_tipo': distribucion_tipo,
            'parametros_distribucion': parametros_distribucion,
            'num_simulaciones': num_simulaciones,
            'inyecciones': inyecciones or []
        }
    
    def run_simulations(self) -> Dict[str, Any]:
        """Run all configured simulations"""
        
        for name, config in self.simulations.items():
            if config['type'] == 'fixed':
                self.results[name] = self._run_fixed_simulation(config)
            elif config['type'] == 'variable':
                self.results[name] = self._run_variable_simulation(config)
            elif config['type'] == 'mixed':
                self.results[name] = self._run_mixed_simulation(config)
        
        return self.results
    
    def _run_fixed_simulation(self, config: Dict) -> Dict[str, Any]:
        """Run fixed rate mortgage simulation"""
        
        # Calculate basic fixed mortgage
        cuota_mensual_calc = cuota_mensual(
            config['capital'], 
            config['tasa_interes'], 
            config['plazo_anos'] * 12
        )
        
        # Run simulation with injections if provided
        if config['inyecciones']:
            resultado = simulacion_hipoteca_multiple_inyeccion(
                config['capital'],
                config['tasa_interes'],
                config['plazo_anos'] * 12,
                cuota_mensual_calc,
                config['inyecciones']
            )
            
            return {
                'type': 'fixed',
                'cuota_inicial': cuota_mensual_calc,
                'capital_inicial': config['capital'],
                'tasa_interes': config['tasa_interes'],
                'plazo_anos': config['plazo_anos'],
                'total_pagado': resultado['total_pagado'],
                'total_intereses': resultado['total_intereses'],
                'ahorro_intereses': resultado.get('ahorro_intereses', 0),
                'meses_reducidos': resultado.get('meses_reducidos', 0),
                'evolucion_saldo': resultado.get('evolucion_saldo', []),
                'evolucion_cuotas': resultado.get('evolucion_cuotas', []),
                'inyecciones': config['inyecciones']
            }
        else:
            # Simple fixed mortgage without injections
            total_pagado = cuota_mensual_calc * config['plazo_anos'] * 12
            total_intereses = total_pagado - config['capital']
            
            return {
                'type': 'fixed',
                'cuota_inicial': cuota_mensual_calc,
                'capital_inicial': config['capital'],
                'tasa_interes': config['tasa_interes'],
                'plazo_anos': config['plazo_anos'],
                'total_pagado': total_pagado,
                'total_intereses': total_intereses,
                'ahorro_intereses': 0,
                'meses_reducidos': 0,
                'inyecciones': []
            }
    
    def _run_variable_simulation(self, config: Dict) -> Dict[str, Any]:
        """Run variable rate mortgage Monte Carlo simulation"""
        
        resultados = run_monte_carlo_simulation(
            config['capital'],
            config['spread'],
            config['plazo_anos'],
            config['euribor_inicial'],
            config['distribucion_tipo'],
            config['num_simulaciones'],
            config['inyecciones'],
            **config['parametros_distribucion']
        )
        
        estadisticas = calculate_simulation_statistics(resultados)
        
        return {
            'type': 'variable',
            'capital_inicial': config['capital'],
            'spread': config['spread'],
            'plazo_anos': config['plazo_anos'],
            'euribor_inicial': config['euribor_inicial'],
            'num_simulaciones': config['num_simulaciones'],
            'estadisticas': estadisticas,
            'resultados_simulaciones': resultados,
            'inyecciones': config['inyecciones']
        }
    
    def _run_mixed_simulation(self, config: Dict) -> Dict[str, Any]:
        """Run mixed rate mortgage Monte Carlo simulation"""
        
        resultados = run_mixed_monte_carlo_simulation(
            config['capital'],
            config['tasa_fija'],
            config['spread'],
            config['plazo_anos'],
            config['anos_fijos'],
            config['euribor_inicial'],
            config['distribucion_tipo'],
            config['num_simulaciones'],
            config['inyecciones'],
            **config['parametros_distribucion']
        )
        
        estadisticas = calculate_mixed_simulation_statistics(resultados)
        
        return {
            'type': 'mixed',
            'capital_inicial': config['capital'],
            'tasa_fija': config['tasa_fija'],
            'anos_fijos': config['anos_fijos'],
            'spread': config['spread'],
            'plazo_anos': config['plazo_anos'],
            'euribor_inicial': config['euribor_inicial'],
            'num_simulaciones': config['num_simulaciones'],
            'estadisticas': estadisticas,
            'resultados_simulaciones': resultados,
            'inyecciones': config['inyecciones']
        }
    
    def get_comparison_summary(self) -> pd.DataFrame:
        """Generate a summary comparison table"""
        
        if not self.results:
            return pd.DataFrame()
        
        summary_data = []
        
        for name, result in self.results.items():
            if result['type'] == 'fixed':
                summary_data.append({
                    'Simulación': name,
                    'Tipo': 'Fija',
                    'Capital Inicial (€)': f"{result['capital_inicial']:,.2f}",
                    'Tasa/Spread (%)': f"{result['tasa_interes']:.2f}%",
                    'Plazo (años)': result['plazo_anos'],
                    'Cuota Inicial (€)': f"{result['cuota_inicial']:,.2f}",
                    'Total Pagado (€)': f"{result['total_pagado']:,.2f}",
                    'Total Intereses (€)': f"{result['total_intereses']:,.2f}",
                    'Ahorro Intereses (€)': f"{result['ahorro_intereses']:,.2f}",
                    'Inyecciones': 'Sí' if result['inyecciones'] else 'No'
                })
            
            elif result['type'] in ['variable', 'mixed']:
                stats = result['estadisticas']
                tipo_desc = 'Mixta' if result['type'] == 'mixed' else 'Variable'
                
                if result['type'] == 'mixed':
                    tasa_desc = f"Fija: {result['tasa_fija']:.2f}% ({result['anos_fijos']} años), Variable: Euribor + {result['spread']:.2f}%"
                else:
                    tasa_desc = f"Euribor + {result['spread']:.2f}%"
                
                summary_data.append({
                    'Simulación': name,
                    'Tipo': tipo_desc,
                    'Capital Inicial (€)': f"{result['capital_inicial']:,.2f}",
                    'Tasa/Spread (%)': tasa_desc,
                    'Plazo (años)': result['plazo_anos'],
                    'Cuota Inicial (€)': f"{stats['cuota_inicial_promedio']:,.2f} ± {stats['cuota_inicial_std']:,.2f}",
                    'Total Pagado (€)': f"{stats['total_pagado_promedio']:,.2f} ± {stats['total_pagado_std']:,.2f}",
                    'Total Intereses (€)': f"{stats['total_intereses_promedio']:,.2f} ± {stats['total_intereses_std']:,.2f}",
                    'Ahorro Intereses (€)': f"{stats.get('ahorro_intereses_promedio', 0):,.2f}",
                    'Inyecciones': 'Sí' if result['inyecciones'] else 'No'
                })
        
        return pd.DataFrame(summary_data)
    
    def export_to_excel(self, filename: Optional[str] = None) -> io.BytesIO:
        """Export all simulation results to Excel file"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparacion_hipotecas_{self.bank_name}_{timestamp}.xlsx"
        
        # Create BytesIO buffer for in-memory Excel file
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = self.get_comparison_summary()
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Individual simulation sheets
            for name, result in self.results.items():
                sheet_name = name[:31]  # Excel sheet name limit
                
                if result['type'] == 'fixed':
                    # Fixed mortgage details
                    fixed_data = {
                        'Parámetro': ['Tipo', 'Capital Inicial', 'Tasa de Interés', 'Plazo', 'Cuota Mensual', 'Total Pagado', 'Total Intereses', 'Ahorro Intereses'],
                        'Valor': [
                            'Hipoteca Fija',
                            f"{result['capital_inicial']:,.2f} €",
                            f"{result['tasa_interes']:.2f}%",
                            f"{result['plazo_anos']} años",
                            f"{result['cuota_inicial']:,.2f} €",
                            f"{result['total_pagado']:,.2f} €",
                            f"{result['total_intereses']:,.2f} €",
                            f"{result['ahorro_intereses']:,.2f} €"
                        ]
                    }
                    pd.DataFrame(fixed_data).to_excel(writer, sheet_name=sheet_name, index=False)
                
                elif result['type'] in ['variable', 'mixed']:
                    # Monte Carlo simulation statistics
                    stats = result['estadisticas']
                    
                    if result['type'] == 'mixed':
                        sim_type = 'Hipoteca Mixta'
                        rate_info = f"Fija: {result['tasa_fija']:.2f}% ({result['anos_fijos']} años), Variable: Euribor + {result['spread']:.2f}%"
                    else:
                        sim_type = 'Hipoteca Variable'
                        rate_info = f"Euribor + {result['spread']:.2f}%"
                    
                    stats_data = {
                        'Estadística': [
                            'Tipo',
                            'Capital Inicial',
                            'Configuración de Tasas',
                            'Plazo',
                            'Número de Simulaciones',
                            'Cuota Inicial Promedio',
                            'Cuota Inicial Desv. Estándar',
                            'Total Pagado Promedio',
                            'Total Pagado Desv. Estándar',
                            'Total Intereses Promedio',
                            'Total Intereses Desv. Estándar',
                            'Percentil 5% Total Pagado',
                            'Percentil 95% Total Pagado',
                            'Ahorro Intereses Promedio'
                        ],
                        'Valor': [
                            sim_type,
                            f"{result['capital_inicial']:,.2f} €",
                            rate_info,
                            f"{result['plazo_anos']} años",
                            result['num_simulaciones'],
                            f"{stats['cuota_inicial_promedio']:,.2f} €",
                            f"{stats['cuota_inicial_std']:,.2f} €",
                            f"{stats['total_pagado_promedio']:,.2f} €",
                            f"{stats['total_pagado_std']:,.2f} €",
                            f"{stats['total_intereses_promedio']:,.2f} €",
                            f"{stats['total_intereses_std']:,.2f} €",
                            f"{stats['total_pagado_p5']:,.2f} €",
                            f"{stats['total_pagado_p95']:,.2f} €",
                            f"{stats.get('ahorro_intereses_promedio', 0):,.2f} €"
                        ]
                    }
                    pd.DataFrame(stats_data).to_excel(writer, sheet_name=sheet_name, index=False)
        
        buffer.seek(0)
        return buffer
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Export comparison summary to CSV file"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparacion_hipotecas_{self.bank_name}_{timestamp}.csv"
        
        summary_df = self.get_comparison_summary()
        summary_df.to_csv(filename, index=False, encoding='utf-8')
        
        return filename

def create_comparison_from_config(bank_name: str, simulations_config: List[Dict]) -> MortgageComparison:
    """Create a MortgageComparison instance from a configuration list"""
    
    comparison = MortgageComparison(bank_name)
    
    for config in simulations_config:
        sim_type = config['type']
        name = config['name']
        
        if sim_type == 'fixed':
            comparison.add_fixed_simulation(
                name=name,
                capital=config['capital'],
                tasa_interes=config['tasa_interes'],
                plazo_anos=config['plazo_anos'],
                inyecciones=config.get('inyecciones', [])
            )
        
        elif sim_type == 'variable':
            comparison.add_variable_simulation(
                name=name,
                capital=config['capital'],
                spread=config['spread'],
                plazo_anos=config['plazo_anos'],
                euribor_inicial=config['euribor_inicial'],
                distribucion_tipo=config['distribucion_tipo'],
                parametros_distribucion=config['parametros_distribucion'],
                num_simulaciones=config.get('num_simulaciones', 1000),
                inyecciones=config.get('inyecciones', [])
            )
        
        elif sim_type == 'mixed':
            comparison.add_mixed_simulation(
                name=name,
                capital=config['capital'],
                tasa_fija=config['tasa_fija'],
                anos_fijos=config['anos_fijos'],
                spread=config['spread'],
                plazo_anos=config['plazo_anos'],
                euribor_inicial=config['euribor_inicial'],
                distribucion_tipo=config['distribucion_tipo'],
                parametros_distribucion=config['parametros_distribucion'],
                num_simulaciones=config.get('num_simulaciones', 1000),
                inyecciones=config.get('inyecciones', [])
            )
    
    return comparison