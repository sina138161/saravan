"""
Anaerobic Digester Model
Anaerobic digestion of sludge and biomass to produce biogas and digestate
"""

from typing import Dict
from ..base import TechnologyBase


class AnaerobicDigester(TechnologyBase):
    """
    Anaerobic Digester System

    Inputs:
    - Sludge (from wastewater treatment)
    - Biomass
    - Agricultural water (process water + recycled water from dewatering)
    - Heat (for maintaining digester temperature at 35°C)

    Outputs:
    - Biogas (CH4 + CO2)
    - Digestate (liquid, goes to dewatering unit)
    """

    def _define_specs(self) -> Dict:
        """
        Define anaerobic digester specifications

        Based on: Commercial biogas plants and research data
        """
        return {
            'name': 'Anaerobic_Digester_Biogas',

            # Input ratios
            'sludge_input_ratio': 0.40,          # 40% sludge (dry weight basis)
            'biomass_input_ratio': 0.60,         # 60% biomass (dry weight basis)

            # Biogas production
            'biogas_yield_m3_per_kg_dry': 0.40,  # 0.4 m³ biogas per kg dry organic matter
            'methane_content': 0.60,             # 60% CH4, 40% CO2
            'biogas_lhv': 6.0,                   # kWh/m³

            # Digestate output
            'digestate_output_ratio': 0.85,      # 85% of input mass (including water)
            'digestate_solids_content': 0.05,    # 5% solids (very liquid)
            'digestate_n_content': 0.03,         # 3% nitrogen (of dry solids)
            'digestate_p_content': 0.015,        # 1.5% phosphorus
            'digestate_k_content': 0.015,        # 1.5% potassium

            # Water requirements
            'water_to_solids_ratio': 10,         # 10 kg water per kg dry solids
            'process_water_consumption': 1.2,    # Including losses (evaporation, etc.)

            # Heat requirements
            'digester_temperature': 35,          # °C (mesophilic digestion)
            'heat_loss_kwh_per_m3_day': 2.0,    # Heat loss from digester
            'heat_for_feedstock_kwh_per_kg': 0.05,  # Heating feedstock from 20°C to 35°C

            # Operating parameters
            'retention_time_days': 20,           # 20 days hydraulic retention time
            'organic_loading_rate': 3.0,         # kg VS/m³/day (volatile solids)
            'mixing_intensity': 'medium',        # No electricity needed (passive mixing via biogas)

            # Economics
            'capex': 200000,                     # $ (for digester vessel + equipment)
            'opex': 0.15,                        # $/m³ biogas produced
            'lifetime': 20                       # years
        }

    def calculate_biogas_production(self, sludge_kg_dry: float,
                                   biomass_kg_dry: float,
                                   process_water_m3: float,
                                   heat_input_kwh: float) -> Dict:
        """
        Calculate biogas and digestate production

        Args:
            sludge_kg_dry: Sludge input (kg dry solids)
            biomass_kg_dry: Biomass input (kg dry matter)
            process_water_m3: Process water input including recycled water (m³)
            heat_input_kwh: Heat input for maintaining temperature (kWh)

        Returns:
            Dictionary with production details
        """
        # Total dry input
        total_dry_input_kg = sludge_kg_dry + biomass_kg_dry

        # Check ratios
        actual_sludge_ratio = sludge_kg_dry / total_dry_input_kg if total_dry_input_kg > 0 else 0
        optimal_sludge_ratio = self.specs['sludge_input_ratio']

        # Water requirement check
        required_water_m3 = (total_dry_input_kg * self.specs['water_to_solids_ratio']) / 1000
        water_deficit_m3 = max(0, required_water_m3 - process_water_m3)

        # Heat requirement check
        required_heat_kwh = (
            total_dry_input_kg * self.specs['heat_for_feedstock_kwh_per_kg'] +
            (total_dry_input_kg / 1000) * self.specs['heat_loss_kwh_per_m3_day'] * self.specs['retention_time_days']
        )
        heat_deficit_kwh = max(0, required_heat_kwh - heat_input_kwh)

        # Biogas production (if sufficient water and heat)
        if water_deficit_m3 > 0 or heat_deficit_kwh > 0:
            # Reduced production due to insufficient resources
            production_factor = min(
                process_water_m3 / required_water_m3 if required_water_m3 > 0 else 1.0,
                heat_input_kwh / required_heat_kwh if required_heat_kwh > 0 else 1.0
            )
        else:
            production_factor = 1.0

        biogas_m3 = total_dry_input_kg * self.specs['biogas_yield_m3_per_kg_dry'] * production_factor
        biogas_energy_kwh = biogas_m3 * self.specs['biogas_lhv']

        # Methane content
        methane_m3 = biogas_m3 * self.specs['methane_content']
        co2_m3 = biogas_m3 * (1 - self.specs['methane_content'])

        # Digestate production
        # Total mass = dry solids + water
        total_mass_kg = total_dry_input_kg + (process_water_m3 * 1000)
        digestate_kg = total_mass_kg * self.specs['digestate_output_ratio']
        digestate_m3 = digestate_kg / 1000  # Assume density ~1000 kg/m³

        # Dry solids in digestate
        digestate_dry_solids_kg = total_dry_input_kg * 0.70  # 30% degraded
        digestate_moisture = (digestate_kg - digestate_dry_solids_kg) / digestate_kg

        # Nutrients in digestate (dry basis)
        n_content_kg = digestate_dry_solids_kg * self.specs['digestate_n_content']
        p_content_kg = digestate_dry_solids_kg * self.specs['digestate_p_content']
        k_content_kg = digestate_dry_solids_kg * self.specs['digestate_k_content']

        return {
            # Inputs
            'sludge_dry_kg': sludge_kg_dry,
            'biomass_dry_kg': biomass_kg_dry,
            'total_dry_input_kg': total_dry_input_kg,
            'process_water_m3': process_water_m3,
            'heat_input_kwh': heat_input_kwh,
            'sludge_ratio': actual_sludge_ratio,
            'optimal_sludge_ratio': optimal_sludge_ratio,

            # Resource requirements and deficits
            'required_water_m3': required_water_m3,
            'water_deficit_m3': water_deficit_m3,
            'water_sufficient': water_deficit_m3 == 0,
            'required_heat_kwh': required_heat_kwh,
            'heat_deficit_kwh': heat_deficit_kwh,
            'heat_sufficient': heat_deficit_kwh == 0,
            'production_factor': production_factor,

            # Biogas outputs
            'biogas_m3': biogas_m3,
            'biogas_energy_kwh': biogas_energy_kwh,
            'methane_m3': methane_m3,
            'co2_m3': co2_m3,
            'methane_content_pct': self.specs['methane_content'] * 100,

            # Digestate outputs
            'digestate_kg': digestate_kg,
            'digestate_m3': digestate_m3,
            'digestate_ton': digestate_kg / 1000,
            'digestate_dry_solids_kg': digestate_dry_solids_kg,
            'digestate_moisture_pct': digestate_moisture * 100,
            'digestate_solids_pct': (1 - digestate_moisture) * 100,
            'nitrogen_kg': n_content_kg,
            'phosphorus_kg': p_content_kg,
            'potassium_kg': k_content_kg,

            # Process parameters
            'retention_time_days': self.specs['retention_time_days'],
            'digester_temperature_c': self.specs['digester_temperature']
        }

    def calculate_digester_sizing(self, daily_dry_input_kg: float) -> Dict:
        """
        Calculate digester volume requirements

        Args:
            daily_dry_input_kg: Daily organic input (kg dry matter)

        Returns:
            Sizing specifications
        """
        # Retention time
        retention_days = self.specs['retention_time_days']

        # Water needed
        daily_water_m3 = (daily_dry_input_kg * self.specs['water_to_solids_ratio']) / 1000

        # Daily volume (solids + water)
        daily_volume_m3 = (daily_dry_input_kg / 1000) + daily_water_m3

        # Required digester volume
        digester_volume_m3 = daily_volume_m3 * retention_days

        # Add 20% safety factor
        digester_volume_design_m3 = digester_volume_m3 * 1.2

        # Daily biogas production
        daily_biogas_m3 = daily_dry_input_kg * self.specs['biogas_yield_m3_per_kg_dry']

        # Organic loading rate check
        actual_olr = daily_dry_input_kg / digester_volume_m3
        optimal_olr = self.specs['organic_loading_rate']

        return {
            'daily_dry_input_kg': daily_dry_input_kg,
            'retention_days': retention_days,
            'required_volume_m3': digester_volume_m3,
            'design_volume_m3': digester_volume_design_m3,
            'daily_biogas_m3': daily_biogas_m3,
            'daily_water_requirement_m3': daily_water_m3,
            'organic_loading_rate_actual': actual_olr,
            'organic_loading_rate_optimal': optimal_olr,
            'olr_within_limits': abs(actual_olr - optimal_olr) / optimal_olr < 0.2  # Within 20%
        }

    def calculate_annual_economics(self, annual_biogas_m3: float,
                                   biogas_value_per_kwh: float = 0.08) -> Dict:
        """
        Calculate annual economics

        Args:
            annual_biogas_m3: Annual biogas production (m³)
            biogas_value_per_kwh: Value of biogas energy ($/kWh)

        Returns:
            Economic analysis
        """
        # Biogas value
        annual_biogas_energy_kwh = annual_biogas_m3 * self.specs['biogas_lhv']
        biogas_revenue = annual_biogas_energy_kwh * biogas_value_per_kwh

        # Operating cost
        annual_opex = annual_biogas_m3 * self.specs['opex']

        # CAPEX (annualized)
        total_capex = self.specs['capex']
        annual_capex = total_capex / self.specs['lifetime']

        # Total cost
        total_annual_cost = annual_capex + annual_opex

        # Net benefit
        net_benefit = biogas_revenue - total_annual_cost

        return {
            'annual_biogas_m3': annual_biogas_m3,
            'annual_biogas_energy_kwh': annual_biogas_energy_kwh,
            'biogas_value': biogas_revenue,
            'annual_opex': annual_opex,
            'annual_capex': annual_capex,
            'total_annual_cost': total_annual_cost,
            'net_annual_benefit': net_benefit,
            'cost_per_m3_biogas': total_annual_cost / annual_biogas_m3 if annual_biogas_m3 > 0 else 0
        }
