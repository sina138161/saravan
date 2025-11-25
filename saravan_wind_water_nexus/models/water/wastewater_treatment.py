"""
Wastewater Treatment System Model
Treatment of municipal wastewater for reuse
"""

from typing import Dict
from ..base import TechnologyBase


class WastewaterTreatment(TechnologyBase):
    """
    Wastewater Treatment System

    Treatment levels:
    - Primary: Municipal wastewater → Agricultural reuse
    - Secondary: Primary treated → Urban reuse/potable
    """

    def __init__(self, treatment_level: str = 'primary'):
        """
        Initialize wastewater treatment system

        Args:
            treatment_level: 'primary' or 'secondary'
        """
        self.treatment_level = treatment_level
        super().__init__()

    def _define_specs(self) -> Dict:
        """
        Define wastewater treatment specifications
        """
        treatment_specs = {
            'primary': {
                'purpose': 'Municipal wastewater → Agricultural reuse',
                'process': 'Screening + Sedimentation + Disinfection',
                'removal_efficiency': 0.70,  # 70% removal
                'energy_kwh_per_m3': 0.25,  # Energy for wastewater treatment
                'capex': 200,  # $ per m³/day capacity
                'opex': 0.12,  # $ per m³
                'output_quality': 'agricultural',
                'recovery_rate': 0.85,  # 85% of wastewater recovered
                'sludge_production_kg_per_m3': 0.075,  # kg dry solids per m³
                'lifetime': 20
            },
            'secondary': {
                'purpose': 'Primary treated wastewater → Urban reuse',
                'process': 'Biological treatment + Membrane filtration',
                'removal_efficiency': 0.90,  # 90% removal
                'energy_kwh_per_m3': 0.60,  # High energy for advanced treatment
                'capex': 450,  # $ per m³/day capacity
                'opex': 0.30,  # $ per m³
                'output_quality': 'potable',
                'recovery_rate': 0.75,  # 75% of input recovered
                'sludge_production_kg_per_m3': 0.090,  # More sludge from biological process
                'lifetime': 20
            }
        }

        specs = treatment_specs[self.treatment_level].copy()
        specs['name'] = f'{self.treatment_level.capitalize()}_Wastewater_Treatment'
        specs['treatment_level'] = self.treatment_level

        return specs

    def calculate_treatment_outputs(self, wastewater_input_m3: float) -> Dict:
        """
        Calculate treatment outputs

        Args:
            wastewater_input_m3: Input wastewater volume (m³)

        Returns:
            Treatment outputs
        """
        # Recovered water
        recovery_rate = self.specs['recovery_rate']
        recovered_water_m3 = wastewater_input_m3 * recovery_rate

        # Sludge production
        sludge_kg = wastewater_input_m3 * self.specs['sludge_production_kg_per_m3']

        # Energy requirement
        energy_kwh = wastewater_input_m3 * self.specs['energy_kwh_per_m3']

        # Water lost (evaporation, sludge moisture, etc.)
        water_lost_m3 = wastewater_input_m3 - recovered_water_m3

        return {
            'wastewater_input_m3': wastewater_input_m3,
            'recovered_water_m3': recovered_water_m3,
            'recovery_rate': recovery_rate,
            'water_lost_m3': water_lost_m3,
            'sludge_produced_kg': sludge_kg,
            'sludge_produced_ton': sludge_kg / 1000,
            'energy_required_kwh': energy_kwh,
            'output_quality': self.specs['output_quality'],
            'treatment_level': self.treatment_level
        }

    def calculate_treatment_cost(self, annual_wastewater_m3: float,
                                electricity_price_per_kwh: float = 0.10) -> Dict:
        """
        Calculate annual treatment cost

        Args:
            annual_wastewater_m3: Annual wastewater treated (m³)
            electricity_price_per_kwh: Electricity price ($/kWh)

        Returns:
            Cost breakdown
        """
        # Treatment outputs
        outputs = self.calculate_treatment_outputs(annual_wastewater_m3)

        # Energy cost
        energy_cost = outputs['energy_required_kwh'] * electricity_price_per_kwh

        # Operating cost
        opex_cost = annual_wastewater_m3 * self.specs['opex']

        # CAPEX (annualized)
        daily_capacity_m3 = annual_wastewater_m3 / 365
        total_capex = daily_capacity_m3 * self.specs['capex']
        annual_capex = total_capex / self.specs['lifetime']

        # Total cost
        total_cost = annual_capex + energy_cost + opex_cost

        # Cost per m³ (input basis)
        cost_per_m3_input = total_cost / annual_wastewater_m3 if annual_wastewater_m3 > 0 else 0

        # Cost per m³ (recovered water basis)
        cost_per_m3_recovered = total_cost / outputs['recovered_water_m3'] if outputs['recovered_water_m3'] > 0 else 0

        return {
            'annual_wastewater_m3': annual_wastewater_m3,
            'annual_recovered_m3': outputs['recovered_water_m3'],
            'daily_capacity_m3': daily_capacity_m3,
            'annual_energy_kwh': outputs['energy_required_kwh'],
            'energy_cost': energy_cost,
            'opex_cost': opex_cost,
            'annual_capex': annual_capex,
            'total_capex': total_capex,
            'total_annual_cost': total_cost,
            'cost_per_m3_input': cost_per_m3_input,
            'cost_per_m3_recovered': cost_per_m3_recovered,
            'sludge_produced_ton': outputs['sludge_produced_ton'],
            'treatment_level': self.treatment_level
        }

    def calculate_water_balance(self, urban_water_supply_m3: float,
                               wastewater_generation_factor: float = 0.80) -> Dict:
        """
        Calculate water balance with wastewater reuse

        Args:
            urban_water_supply_m3: Urban water supply (m³)
            wastewater_generation_factor: Fraction becoming wastewater (default 0.80)

        Returns:
            Water balance
        """
        # Wastewater generated
        wastewater_generated_m3 = urban_water_supply_m3 * wastewater_generation_factor

        # Treatment outputs
        outputs = self.calculate_treatment_outputs(wastewater_generated_m3)

        # Net water demand from source
        net_fresh_water_demand = urban_water_supply_m3 - outputs['recovered_water_m3']

        # Water reuse rate
        reuse_rate = outputs['recovered_water_m3'] / urban_water_supply_m3 if urban_water_supply_m3 > 0 else 0

        return {
            'urban_water_supply_m3': urban_water_supply_m3,
            'wastewater_generated_m3': wastewater_generated_m3,
            'wastewater_generation_factor': wastewater_generation_factor,
            'recovered_water_m3': outputs['recovered_water_m3'],
            'net_fresh_water_demand': net_fresh_water_demand,
            'water_savings_m3': outputs['recovered_water_m3'],
            'water_reuse_rate': reuse_rate,
            'reuse_rate_pct': reuse_rate * 100
        }

    def size_treatment_plant(self, peak_wastewater_m3_h: float,
                            average_wastewater_m3_h: float) -> Dict:
        """
        Size wastewater treatment plant

        Args:
            peak_wastewater_m3_h: Peak hourly wastewater (m³/h)
            average_wastewater_m3_h: Average hourly wastewater (m³/h)

        Returns:
            Plant sizing
        """
        # Design capacity (1.5x peak for wastewater - higher safety factor)
        design_capacity_m3_h = peak_wastewater_m3_h * 1.5

        # Daily capacity
        daily_capacity_m3 = design_capacity_m3_h * 24

        # CAPEX
        total_capex = daily_capacity_m3 * self.specs['capex']

        # Capacity utilization
        avg_utilization = average_wastewater_m3_h / design_capacity_m3_h
        peak_utilization = peak_wastewater_m3_h / design_capacity_m3_h

        # Annual throughput
        annual_throughput_m3 = average_wastewater_m3_h * 8760

        # Outputs
        outputs = self.calculate_treatment_outputs(annual_throughput_m3)

        return {
            'peak_wastewater_m3_h': peak_wastewater_m3_h,
            'average_wastewater_m3_h': average_wastewater_m3_h,
            'design_capacity_m3_h': design_capacity_m3_h,
            'daily_capacity_m3': daily_capacity_m3,
            'total_capex': total_capex,
            'avg_utilization': avg_utilization,
            'peak_utilization': peak_utilization,
            'annual_throughput_m3': annual_throughput_m3,
            'annual_recovered_water_m3': outputs['recovered_water_m3'],
            'annual_sludge_ton': outputs['sludge_produced_ton'],
            'treatment_level': self.treatment_level
        }

    def calculate_environmental_benefit(self, annual_wastewater_treated_m3: float) -> Dict:
        """
        Calculate environmental benefits

        Args:
            annual_wastewater_treated_m3: Annual wastewater treated (m³)

        Returns:
            Environmental benefits
        """
        # Treatment outputs
        outputs = self.calculate_treatment_outputs(annual_wastewater_treated_m3)

        # Water saved (avoided groundwater extraction)
        water_saved_m3 = outputs['recovered_water_m3']

        # Energy saved from not pumping fresh groundwater (assume 1 kWh/m³)
        energy_saved_kwh = water_saved_m3 * 1.0

        # CO2 avoided (if energy from fossil fuels)
        co2_avoided_kg = energy_saved_kwh * 0.5  # kg CO2 per kWh

        # Pollution prevented from entering environment
        # (based on removal efficiency)
        pollution_removed_kg = annual_wastewater_treated_m3 * 0.5 * self.specs['removal_efficiency']

        return {
            'water_saved_m3': water_saved_m3,
            'energy_saved_kwh': energy_saved_kwh,
            'co2_avoided_kg': co2_avoided_kg,
            'pollution_removed_kg': pollution_removed_kg,
            'groundwater_preservation_m3': water_saved_m3
        }
