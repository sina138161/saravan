"""
Combined Heat and Power (CHP) Model
Cogeneration system producing both electricity and heat
"""

from typing import Dict, Tuple
from ..base import TechnologyBase


class CHP(TechnologyBase):
    """
    Combined Heat and Power (CHP) System

    Can operate on:
    - Natural gas (from grid)
    - Biogas (from anaerobic digester)

    Outputs:
    - Electricity
    - Heat
    - CO2 emissions
    """

    def _define_specs(self) -> Dict:
        """
        Define CHP specifications

        Based on: Commercial CHP systems and industry standards
        """
        return {
            'name': 'CHP_Cogeneration_System',
            'electrical_efficiency': 0.35,  # 35% electricity
            'thermal_efficiency': 0.45,     # 45% heat
            'total_efficiency': 0.80,        # 80% combined
            'natural_gas_lhv': 10.0,         # kWh/m³ (Lower Heating Value)
            'biogas_lhv': 6.0,               # kWh/m³ (depends on methane content)
            'emissions_natural_gas': 0.20,   # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,         # Biogenic CO2 (carbon neutral)
            'capex': 1500,                   # $/kW electrical
            'opex': 0.02,                    # $/kWh electrical output
            'lifetime': 20,                  # years
            'min_load': 0.30,                # 30% minimum load
            'ramp_rate': 0.10                # 10% per hour
        }

    def calculate_outputs(self, fuel_input_kwh: float,
                         fuel_type: str = 'natural_gas') -> Dict:
        """
        Calculate CHP outputs for given fuel input

        Args:
            fuel_input_kwh: Fuel energy input (kWh thermal)
            fuel_type: 'natural_gas' or 'biogas'

        Returns:
            Dictionary with electricity, heat, and emissions
        """
        # Calculate electricity output
        electricity_output = fuel_input_kwh * self.specs['electrical_efficiency']

        # Calculate heat output
        heat_output = fuel_input_kwh * self.specs['thermal_efficiency']

        # Calculate emissions
        if fuel_type == 'natural_gas':
            co2_emissions = fuel_input_kwh * self.specs['emissions_natural_gas']
        elif fuel_type == 'biogas':
            co2_emissions = fuel_input_kwh * self.specs['emissions_biogas']
        else:
            co2_emissions = 0

        return {
            'electricity_kwh': electricity_output,
            'heat_kwh': heat_output,
            'co2_emissions_kg': co2_emissions,
            'total_output_kwh': electricity_output + heat_output,
            'efficiency': (electricity_output + heat_output) / fuel_input_kwh if fuel_input_kwh > 0 else 0
        }

    def calculate_fuel_requirement(self, electricity_demand_kwh: float,
                                   fuel_type: str = 'natural_gas') -> Dict:
        """
        Calculate fuel requirement for desired electricity output

        Args:
            electricity_demand_kwh: Desired electricity output (kWh)
            fuel_type: 'natural_gas' or 'biogas'

        Returns:
            Dictionary with fuel requirements and co-products
        """
        # Calculate required fuel input
        fuel_input_kwh = electricity_demand_kwh / self.specs['electrical_efficiency']

        # Calculate co-produced heat
        heat_output = fuel_input_kwh * self.specs['thermal_efficiency']

        # Convert to fuel volume
        if fuel_type == 'natural_gas':
            fuel_volume_m3 = fuel_input_kwh / self.specs['natural_gas_lhv']
            co2_emissions = fuel_input_kwh * self.specs['emissions_natural_gas']
        elif fuel_type == 'biogas':
            fuel_volume_m3 = fuel_input_kwh / self.specs['biogas_lhv']
            co2_emissions = 0  # Carbon neutral
        else:
            fuel_volume_m3 = 0
            co2_emissions = 0

        return {
            'fuel_input_kwh': fuel_input_kwh,
            'fuel_volume_m3': fuel_volume_m3,
            'fuel_type': fuel_type,
            'electricity_output_kwh': electricity_demand_kwh,
            'heat_output_kwh': heat_output,
            'co2_emissions_kg': co2_emissions,
            'heat_to_power_ratio': heat_output / electricity_demand_kwh if electricity_demand_kwh > 0 else 0
        }

    def check_operational_constraints(self, load_fraction: float,
                                     previous_load: float = None) -> Dict:
        """
        Check if operation satisfies constraints

        Args:
            load_fraction: Current load as fraction of rated capacity (0-1)
            previous_load: Previous hour load fraction (for ramp rate check)

        Returns:
            Dictionary with constraint check results
        """
        constraints_met = True
        violations = []

        # Minimum load constraint
        if load_fraction > 0 and load_fraction < self.specs['min_load']:
            constraints_met = False
            violations.append(
                f"Load {load_fraction:.1%} below minimum {self.specs['min_load']:.1%}"
            )

        # Ramp rate constraint
        if previous_load is not None:
            load_change = abs(load_fraction - previous_load)
            max_ramp = self.specs['ramp_rate']
            if load_change > max_ramp:
                constraints_met = False
                violations.append(
                    f"Ramp rate {load_change:.1%} exceeds maximum {max_ramp:.1%}"
                )

        return {
            'constraints_met': constraints_met,
            'violations': violations,
            'load_fraction': load_fraction,
            'min_load': self.specs['min_load'],
            'ramp_rate': self.specs['ramp_rate']
        }

    def calculate_annual_costs(self, annual_electricity_kwh: float,
                              fuel_price_per_m3: float,
                              fuel_type: str = 'natural_gas',
                              capacity_kw: float = 1000) -> Dict:
        """
        Calculate annual costs for CHP operation

        Args:
            annual_electricity_kwh: Annual electricity output
            fuel_price_per_m3: Fuel price ($/m³)
            fuel_type: 'natural_gas' or 'biogas'
            capacity_kw: CHP electrical capacity (kW)

        Returns:
            Cost breakdown dictionary
        """
        # Fuel requirements
        fuel_req = self.calculate_fuel_requirement(annual_electricity_kwh, fuel_type)

        # Fuel cost
        fuel_cost = fuel_req['fuel_volume_m3'] * fuel_price_per_m3

        # CAPEX (annualized)
        capex_total = self.calculate_total_capex(capacity_kw)
        annual_capex = capex_total / self.specs['lifetime']

        # OPEX
        annual_opex = self.calculate_annual_opex(annual_electricity_kwh)

        # Total annual cost
        total_cost = annual_capex + annual_opex + fuel_cost

        return {
            'annual_capex': annual_capex,
            'annual_opex': annual_opex,
            'annual_fuel_cost': fuel_cost,
            'total_annual_cost': total_cost,
            'cost_per_kwh_electricity': total_cost / annual_electricity_kwh if annual_electricity_kwh > 0 else 0,
            'co_product_heat_kwh': fuel_req['heat_output_kwh']
        }
