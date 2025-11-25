"""
Water Treatment System Model
Treatment of groundwater for agricultural and potable use
"""

from typing import Dict
from ..base import TechnologyBase


class WaterTreatment(TechnologyBase):
    """
    Water Treatment System

    Treatment levels:
    - Primary: Groundwater → Agricultural quality (Filtration + Chlorination)
    - Secondary: Primary → Potable quality (Advanced filtration + UV + RO)
    """

    def __init__(self, treatment_level: str = 'primary'):
        """
        Initialize water treatment system

        Args:
            treatment_level: 'primary' or 'secondary'
        """
        self.treatment_level = treatment_level
        super().__init__()

    def _define_specs(self) -> Dict:
        """
        Define water treatment specifications

        Based on: Commercial water treatment systems
        """
        treatment_specs = {
            'primary': {
                'purpose': 'Groundwater → Agricultural quality',
                'process': 'Filtration + Chlorination',
                'removal_efficiency': 0.85,  # 85% contaminant removal
                'energy_kwh_per_m3': 0.15,  # Energy for primary treatment
                'capex': 120,  # $ per m³/day capacity
                'opex': 0.08,  # $ per m³
                'output_quality': 'agricultural',
                'lifetime': 20
            },
            'secondary': {
                'purpose': 'Primary treated → Potable quality',
                'process': 'Advanced filtration + UV + RO (partial)',
                'removal_efficiency': 0.95,  # 95% contaminant removal
                'energy_kwh_per_m3': 0.50,  # Higher energy for advanced treatment
                'capex': 350,  # $ per m³/day capacity
                'opex': 0.22,  # $ per m³
                'output_quality': 'potable',
                'lifetime': 20
            }
        }

        specs = treatment_specs[self.treatment_level].copy()
        specs['name'] = f'{self.treatment_level.capitalize()}_Water_Treatment'
        specs['treatment_level'] = self.treatment_level

        return specs

    def calculate_treatment_energy(self, flow_rate_m3: float) -> Dict:
        """
        Calculate energy required for water treatment

        Args:
            flow_rate_m3: Water flow rate (m³)

        Returns:
            Energy requirements
        """
        energy_per_m3 = self.specs['energy_kwh_per_m3']
        total_energy = flow_rate_m3 * energy_per_m3

        return {
            'flow_rate_m3': flow_rate_m3,
            'treatment_level': self.treatment_level,
            'energy_per_m3_kwh': energy_per_m3,
            'total_energy_kwh': total_energy
        }

    def calculate_treatment_cost(self, annual_water_m3: float,
                                electricity_price_per_kwh: float = 0.10) -> Dict:
        """
        Calculate annual treatment cost

        Args:
            annual_water_m3: Annual water treated (m³)
            electricity_price_per_kwh: Electricity price ($/kWh)

        Returns:
            Cost breakdown
        """
        # Energy requirement
        annual_energy_kwh = annual_water_m3 * self.specs['energy_kwh_per_m3']

        # Energy cost
        energy_cost = annual_energy_kwh * electricity_price_per_kwh

        # Operating cost (chemicals, maintenance)
        opex_cost = annual_water_m3 * self.specs['opex']

        # CAPEX (annualized)
        daily_capacity_m3 = annual_water_m3 / 365
        total_capex = daily_capacity_m3 * self.specs['capex']
        annual_capex = total_capex / self.specs['lifetime']

        # Total cost
        total_cost = annual_capex + energy_cost + opex_cost

        # Cost per m³
        cost_per_m3 = total_cost / annual_water_m3 if annual_water_m3 > 0 else 0

        return {
            'annual_water_m3': annual_water_m3,
            'daily_capacity_m3': daily_capacity_m3,
            'annual_energy_kwh': annual_energy_kwh,
            'energy_cost': energy_cost,
            'opex_cost': opex_cost,
            'annual_capex': annual_capex,
            'total_capex': total_capex,
            'total_annual_cost': total_cost,
            'cost_per_m3': cost_per_m3,
            'treatment_level': self.treatment_level,
            'output_quality': self.specs['output_quality']
        }

    def calculate_contaminant_removal(self, input_tds: float,
                                     input_volume_m3: float) -> Dict:
        """
        Calculate contaminant removal

        Args:
            input_tds: Input Total Dissolved Solids (mg/L)
            input_volume_m3: Input water volume (m³)

        Returns:
            Removal details
        """
        removal_efficiency = self.specs['removal_efficiency']

        # Output TDS
        output_tds = input_tds * (1 - removal_efficiency)

        # Contaminants removed
        tds_removed_mg_l = input_tds - output_tds

        # Total mass removed
        total_mass_removed_kg = (tds_removed_mg_l * input_volume_m3) / 1000

        return {
            'input_tds_mg_l': input_tds,
            'output_tds_mg_l': output_tds,
            'removal_efficiency': removal_efficiency,
            'tds_removed_mg_l': tds_removed_mg_l,
            'total_mass_removed_kg': total_mass_removed_kg,
            'input_volume_m3': input_volume_m3,
            'treatment_level': self.treatment_level
        }

    def size_treatment_plant(self, peak_demand_m3_h: float,
                            average_demand_m3_h: float) -> Dict:
        """
        Size treatment plant for demand

        Args:
            peak_demand_m3_h: Peak hourly demand (m³/h)
            average_demand_m3_h: Average hourly demand (m³/h)

        Returns:
            Plant sizing recommendations
        """
        # Design capacity (typically 1.2x peak for safety)
        design_capacity_m3_h = peak_demand_m3_h * 1.2

        # Daily capacity
        daily_capacity_m3 = design_capacity_m3_h * 24

        # CAPEX
        total_capex = daily_capacity_m3 * self.specs['capex']

        # Capacity utilization
        avg_utilization = average_demand_m3_h / design_capacity_m3_h
        peak_utilization = peak_demand_m3_h / design_capacity_m3_h

        # Annual throughput
        annual_throughput_m3 = average_demand_m3_h * 8760

        # Energy requirement
        annual_energy_kwh = annual_throughput_m3 * self.specs['energy_kwh_per_m3']

        return {
            'peak_demand_m3_h': peak_demand_m3_h,
            'average_demand_m3_h': average_demand_m3_h,
            'design_capacity_m3_h': design_capacity_m3_h,
            'daily_capacity_m3': daily_capacity_m3,
            'total_capex': total_capex,
            'avg_utilization': avg_utilization,
            'peak_utilization': peak_utilization,
            'annual_throughput_m3': annual_throughput_m3,
            'annual_energy_kwh': annual_energy_kwh,
            'treatment_level': self.treatment_level
        }

    def compare_treatment_levels(self, annual_water_m3: float) -> Dict:
        """
        Compare primary vs secondary treatment

        Args:
            annual_water_m3: Annual water volume

        Returns:
            Comparison results
        """
        # Primary treatment
        primary = WaterTreatment('primary')
        primary_cost = primary.calculate_treatment_cost(annual_water_m3)

        # Secondary treatment
        secondary = WaterTreatment('secondary')
        secondary_cost = secondary.calculate_treatment_cost(annual_water_m3)

        # Cost difference
        cost_difference = secondary_cost['total_annual_cost'] - primary_cost['total_annual_cost']
        cost_increase_pct = (cost_difference / primary_cost['total_annual_cost']) * 100 if primary_cost['total_annual_cost'] > 0 else 0

        return {
            'annual_water_m3': annual_water_m3,
            'primary_cost_per_m3': primary_cost['cost_per_m3'],
            'secondary_cost_per_m3': secondary_cost['cost_per_m3'],
            'primary_total_cost': primary_cost['total_annual_cost'],
            'secondary_total_cost': secondary_cost['total_annual_cost'],
            'cost_difference': cost_difference,
            'cost_increase_pct': cost_increase_pct,
            'primary_quality': 'Agricultural',
            'secondary_quality': 'Potable'
        }
