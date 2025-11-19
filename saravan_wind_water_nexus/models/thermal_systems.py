"""
Thermal Systems Models - CHP and Gas Boiler

These systems can operate on:
- Natural gas (from grid)
- Biogas (from anaerobic digester)
"""

import numpy as np
from typing import Dict


class CHPModel:
    """
    Combined Heat and Power (CHP) Model

    Can operate on:
    - Natural gas (from grid)
    - Biogas (from anaerobic digester)

    Outputs:
    - Electricity
    - Heat
    - CO2 emissions
    """

    def __init__(self):
        """Initialize CHP specifications"""
        self.specs = {
            'electrical_efficiency': 0.35,  # 35% electricity
            'thermal_efficiency': 0.45,     # 45% heat
            'total_efficiency': 0.80,        # 80% combined
            'natural_gas_lhv': 10.0,         # kWh/m³ (Lower Heating Value)
            'biogas_lhv': 6.0,               # kWh/m³ (depends on methane content)
            'emissions_natural_gas': 0.20,   # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,         # Biogenic CO2 (carbon neutral)
            'capex': 1500,                   # $/kW electrical
            'opex_per_kwh': 0.02,            # $/kWh
            'min_load': 0.30,                # 30% minimum load
            'ramp_rate': 0.10                # 10% per hour
        }

    def get_specs(self):
        """Get CHP specifications"""
        return self.specs


class GasBoilerModel:
    """
    Gas Boiler Model

    Can operate on:
    - Natural gas (from grid)
    - Biogas (from anaerobic digester)

    Outputs:
    - Heat
    - CO2 emissions
    """

    def __init__(self):
        """Initialize gas boiler specifications"""
        self.specs = {
            'thermal_efficiency': 0.85,      # 85% efficiency
            'natural_gas_lhv': 10.0,         # kWh/m³
            'biogas_lhv': 6.0,               # kWh/m³
            'emissions_natural_gas': 0.20,   # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,         # Biogenic CO2 (carbon neutral)
            'capex': 150,                    # $/kW thermal
            'opex_per_kwh': 0.01,            # $/kWh
            'min_load': 0.20,                # 20% minimum load
        }

    def get_specs(self):
        """Get boiler specifications"""
        return self.specs


# Example usage and testing
if __name__ == "__main__":
    print("="*80)
    print("THERMAL SYSTEMS MODELS")
    print("="*80)

    # CHP Model
    print("\n1. CHP (Combined Heat & Power)")
    print("-"*80)
    chp = CHPModel()
    print(f"Electrical efficiency: {chp.specs['electrical_efficiency']*100}%")
    print(f"Thermal efficiency: {chp.specs['thermal_efficiency']*100}%")
    print(f"Total efficiency: {chp.specs['total_efficiency']*100}%")

    # Example: 1000 kWh natural gas input
    gas_input = 1000  # kWh
    elec_output = gas_input * chp.specs['electrical_efficiency']
    heat_output = gas_input * chp.specs['thermal_efficiency']
    co2_emissions = gas_input * chp.specs['emissions_natural_gas']

    print(f"\nExample: {gas_input} kWh natural gas input:")
    print(f"   Electricity output: {elec_output:.1f} kWh")
    print(f"   Heat output: {heat_output:.1f} kWh")
    print(f"   CO2 emissions: {co2_emissions:.1f} kg")

    # Gas Boiler Model
    print("\n\n2. GAS BOILER")
    print("-"*80)
    boiler = GasBoilerModel()
    print(f"Thermal efficiency: {boiler.specs['thermal_efficiency']*100}%")

    heat_output = gas_input * boiler.specs['thermal_efficiency']
    co2_emissions = gas_input * boiler.specs['emissions_natural_gas']

    print(f"\nExample: {gas_input} kWh natural gas input:")
    print(f"   Heat output: {heat_output:.1f} kWh")
    print(f"   CO2 emissions: {co2_emissions:.1f} kg")
