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
    
    def add_fixed_simulation(self, name: str, capital: float, tasa_interes: float, 
                           plazo_anos: int, inyecciones: List = None):
        """Add a fixed rate mortgage simulation"""
        if inyecciones is None:
            inyecciones = []
        
        self.simulations[name] = {
            'type': 'fixed',
            'capital': capital,
            'tasa_interes': tasa_interes,
            'plazo_anos': plazo_anos,
            'inyecciones': inyecciones
        }
    
    def add_variable_simulation(self, name: str, capital: float, spread: float,
                              plazo_anos: int, euribor_inicial: float,
                              distribucion_tipo: str, parametros_distribucion: Dict,
                              num_simulaciones: int, inyecciones: List = None):
        """Add a variable rate mortgage simulation"""
        if inyecciones is None:
            inyecciones = []
        
        self.simulations[name] = {
            'type': 'variable',
            'capital': capital,
            'spread': spread,
            'plazo_anos': plazo_anos,
            'euribor_inicial': euribor_inicial,
            'distribucion_tipo': distribucion_tipo,
            'parametros_distribucion': parametros_distribucion,
            'num_simulaciones': num_simulaciones,
            'inyecciones': inyecciones
        }
    
    def add_mixed_simulation(self, name: str, capital: float, tasa_fija: float,
                           anos_fijos: int, spread: float, plazo_anos: int,
                           euribor_inicial: float, distribucion_tipo: str,
                           parametros_distribucion: Dict, num_simulaciones: int,
                           inyecciones: List = None):
        """Add a mixed rate mortgage simulation"""
        if inyecciones is None:
            inyecciones = []
        
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
            'inyecciones': inyecciones
        }
    
    def run_simulations(self) -> Dict[str, Any]:
        """Run all configured simulations and return results"""
        results = {}
        
        for name, sim_config in self.simulations.items():
            try:
                if sim_config['type'] == 'fixed':
                    results[name] = self._run_fixed_simulation(name, sim_config)
                elif sim_config['type'] == 'variable':
                    results[name] = self._run_variable_simulation(name, sim_config)
                elif sim_config['type'] == 'mixed':
                    results[name] = self._run_mixed_simulation(name, sim_config)
            except Exception as e:
                results[name] = {'error': str(e)}
        
        self.results = results
        return results
    
    def _run_fixed_simulation(self, name: str, config: Dict) -> Dict[str, Any]:
        """Run a fixed rate mortgage simulation"""
        # Convert inyecciones format if needed
        inyecciones_formatted = []
        for inj in config['inyecciones']:
            if isinstance(inj, dict):
                inyecciones_formatted.append(inj)
            else:
                # Handle tuple format (mes, cantidad, estrategia)
                inyecciones_formatted.append({
                    'mes_inyeccion': inj[0],
                    'capital_inyectado': inj[1],
                    'tipo_inyeccion': inj[2]
                })
        
        # Calculate initial monthly payment
        cuota_inicial = cuota_mensual(config['capital'], config['tasa_interes'], config['plazo_anos'])
        
        # Run simulation
        resultado = simulacion_hipoteca_multiple_inyeccion(
            capital_inicial=config['capital'],
            tasa=config['tasa_interes'],
            plazo_inicial=config['plazo_anos'] * 12,  # Convert years to months
            cuota_inicial=cuota_inicial,
            inyecciones=inyecciones_formatted
        )
        
        # Calculate metrics
        cuota_inicial = cuota_mensual(config['capital'], config['tasa_interes'], config['plazo_anos'])
        total_intereses = sum(row['Intereses_mensuales'] for row in resultado)
        total_pagado = config['capital'] + total_intereses
        ahorro_intereses = sum(inj.get('capital_inyectado', 0) for inj in inyecciones_formatted)
        
        return {
            'type': 'fixed',
            'data': resultado,
            'cuota_inicial': cuota_inicial,
            'total_pagado': total_pagado,
            'total_intereses': total_intereses,
            'ahorro_intereses': ahorro_intereses,
            'inyecciones': [(inj['mes_inyeccion'], inj['capital_inyectado'], inj['tipo_inyeccion']) 
                           for inj in inyecciones_formatted]
        }
    
    def _run_variable_simulation(self, name: str, config: Dict) -> Dict[str, Any]:
        """Run a variable rate mortgage simulation"""
        # Convert inyecciones format if needed
        inyecciones_formatted = []
        for inj in config['inyecciones']:
            if isinstance(inj, dict):
                inyecciones_formatted.append(inj)
            else:
                inyecciones_formatted.append({
                    'mes_inyeccion': inj[0],
                    'capital_inyectado': inj[1],
                    'tipo_inyeccion': inj[2]
                })
        
        # Run Monte Carlo simulation
        all_results = run_monte_carlo_simulation(
            capital_inicial=config['capital'],
            spread=config['spread'],
            plazo_anos=config['plazo_anos'],
            initial_euribor=config['euribor_inicial'],
            distribution_type=config['distribucion_tipo'],
            num_simulations=config['num_simulaciones'],
            inyecciones=inyecciones_formatted,
            **config['parametros_distribucion']
        )
        
        # Calculate statistics
        estadisticas = calculate_simulation_statistics(all_results)
        
        return {
            'type': 'variable',
            'data': all_results,
            'estadisticas': estadisticas,
            'inyecciones': [(inj['mes_inyeccion'], inj['capital_inyectado'], inj['tipo_inyeccion']) 
                           for inj in inyecciones_formatted]
        }
    
    def _run_mixed_simulation(self, name: str, config: Dict) -> Dict[str, Any]:
        """Run a mixed rate mortgage simulation"""
        # Convert inyecciones format if needed
        inyecciones_formatted = []
        for inj in config['inyecciones']:
            if isinstance(inj, dict):
                inyecciones_formatted.append(inj)
            else:
                inyecciones_formatted.append({
                    'mes_inyeccion': inj[0],
                    'capital_inyectado': inj[1],
                    'tipo_inyeccion': inj[2]
                })
        
        # Run mixed Monte Carlo simulation
        all_results = run_mixed_monte_carlo_simulation(
            capital_inicial=config['capital'],
            tasa_fija=config['tasa_fija'],
            spread=config['spread'],
            plazo_anos=config['plazo_anos'],
            anos_fijos=config['anos_fijos'],
            initial_euribor=config['euribor_inicial'],
            distribution_type=config['distribucion_tipo'],
            num_simulations=config['num_simulaciones'],
            inyecciones=inyecciones_formatted,
            **config['parametros_distribucion']
        )
        
        # Calculate statistics
        estadisticas = calculate_mixed_simulation_statistics(all_results)
        
        return {
            'type': 'mixed',
            'data': all_results,
            'estadisticas': estadisticas,
            'inyecciones': [(inj['mes_inyeccion'], inj['capital_inyectado'], inj['tipo_inyeccion']) 
                           for inj in inyecciones_formatted]
        }
    
    def export_to_excel_detailed(self) -> io.BytesIO:
        """Export detailed results to Excel format"""
        if not self.results:
            raise ValueError("No hay resultados para exportar. Ejecuta las simulaciones primero.")
        
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for name, result in self.results.items():
                if 'error' in result:
                    continue
                    
                if result['type'] == 'fixed':
                    summary_data.append({
                        'Banco': self.bank_name,
                        'Simulación': name,
                        'Tipo': 'Fija',
                        'Cuota Inicial (€)': result['cuota_inicial'],
                        'Total Pagado (€)': result['total_pagado'],
                        'Total Intereses (€)': result['total_intereses'],
                        'Ahorro Intereses (€)': result['ahorro_intereses']
                    })
                else:
                    stats = result['estadisticas']
                    summary_data.append({
                        'Banco': self.bank_name,
                        'Simulación': name,
                        'Tipo': result['type'].title(),
                        'Cuota Inicial (€)': stats['cuota_inicial_promedio'],
                        'Total Pagado (€)': stats['total_pagado_promedio'],
                        'Total Intereses (€)': stats['total_intereses_promedio'],
                        'Ahorro Intereses (€)': stats.get('ahorro_intereses_promedio', 0)
                    })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Detailed sheets for each simulation
            for name, result in self.results.items():
                if 'error' in result:
                    continue
                    
                if result['type'] == 'fixed':
                    # Convert to DataFrame
                    df = pd.DataFrame(result['data'])
                    df['Banco'] = self.bank_name
                    df['Simulación'] = name
                    # Reorder columns
                    cols = ['Banco', 'Simulación'] + [col for col in df.columns if col not in ['Banco', 'Simulación']]
                    df = df[cols]
                    df.to_excel(writer, sheet_name=f'{name[:30]}', index=False)
                else:
                    # For variable/mixed simulations, export the raw data
                    df = result['data'].copy()
                    df['Banco'] = self.bank_name
                    df['Simulación'] = name
                    # Reorder columns
                    cols = ['Banco', 'Simulación'] + [col for col in df.columns if col not in ['Banco', 'Simulación']]
                    df = df[cols]
                    df.to_excel(writer, sheet_name=f'{name[:30]}', index=False)
        
        buffer.seek(0)
        return buffer
    
    def export_to_csv_detailed(self) -> str:
        """Export detailed results to CSV format"""
        if not self.results:
            raise ValueError("No hay resultados para exportar. Ejecuta las simulaciones primero.")
        
        # Combine all simulation data into a single DataFrame
        all_data = []
        
        for name, result in self.results.items():
            if 'error' in result:
                continue
                
            if result['type'] == 'fixed':
                df = pd.DataFrame(result['data'])
                df['Banco'] = self.bank_name
                df['Simulación'] = name
                df['Tipo'] = 'Fija'
                df['Simulation'] = 0  # Fixed simulations don't have multiple runs
            else:
                df = result['data'].copy()
                df['Banco'] = self.bank_name
                df['Simulación'] = name
                df['Tipo'] = result['type'].title()
            
            # Reorder columns
            base_cols = ['Banco', 'Simulación', 'Tipo']
            other_cols = [col for col in df.columns if col not in base_cols]
            df = df[base_cols + other_cols]
            
            all_data.append(df)
        
        if not all_data:
            return "No hay datos para exportar"
        
        # Combine all DataFrames
        combined_df = pd.concat(all_data, ignore_index=True, sort=False)
        
        # Convert to CSV
        return combined_df.to_csv(index=False)