"""
Compatibility wrapper for thermal system models
Provides backward compatibility for old imports
"""

from typing import Dict


class CHPModel:
    """
    CHP (Combined Heat and Power) Model

    Provides backward compatibility for network_builder_simple.py
    """

    def get_specs(self) -> Dict:
        """
        Get CHP system specifications

        Returns:
            CHP specifications dictionary
        """
        return {
            'name': 'CHP_System',
            'rated_capacity_kw_thermal': 1000,  # Thermal input capacity
            'electrical_efficiency': 0.35,  # 35% electrical
            'thermal_efficiency': 0.45,  # 45% thermal
            'total_efficiency': 0.80,  # 80% combined
            'emissions_natural_gas': 0.20,  # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,  # Biogenic CO2
            'capex': 1800,  # $/kW electrical (higher than microturbine)
            'opex': 0.025,  # $/kWh electrical
            'lifetime': 20,  # years
            'min_load': 0.30,  # 30% minimum load
            'ramp_rate': 0.10  # 10% per minute
        }


class GasBoilerModel:
    """
    Gas Boiler Model

    Provides backward compatibility for network_builder_simple.py
    """

    def get_specs(self) -> Dict:
        """
        Get gas boiler specifications

        Returns:
            Boiler specifications dictionary
        """
        return {
            'name': 'Gas_Boiler',
            'thermal_efficiency': 0.85,  # 85% efficiency
            'natural_gas_lhv': 10.0,  # kWh/m³
            'biogas_lhv': 6.0,  # kWh/m³
            'emissions_natural_gas': 0.20,  # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,  # Biogenic CO2
            'capex': 150,  # $/kW thermal
            'opex': 0.01,  # $/kWh heat output
            'lifetime': 20,  # years
            'min_load': 0.20,  # 20% minimum load
            'ramp_rate': 0.20  # 20% per hour
        }
