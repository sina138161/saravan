"""
Anaerobic Digester Model
Anaerobic digestion of sludge and biomass to produce biogas and digestate
"""

from typing import Dict
from ..base import TechnologyBase


class AnaerobicDigester(TechnologyBase):
    """
    Anaerobic Digester System

    Process:
    Sludge + Biomass + Heat + Electricity → Biogas + Digestate (fertilizer)

    Outputs:
    - Biogas (for CHP or boiler)
    - Digestate (organic fertilizer)
    - Heat requirement
    - Electricity requirement
    """

    def _define_specs(self) -> Dict:
        """
        Define anaerobic digester specifications

        Based on: Commercial biogas plants and research data
        """
        return {
            'name': 'Anaerobic_Digester_Biogas',
            'sludge_input_ratio': 0.60,          # 60% sludge, 40% biomass
            'biomass_input_ratio': 0.40,
            'biogas_yield_m3_per_kg': 0.40,      # 0.4 m³ biogas per kg organic matter
            'methane_content': 0.60,             # 60% CH4, 40% CO2
            'biogas_lhv': 6.0,                   # kWh/m³
            'digestate_output_ratio': 0.85,      # 85% of input mass
            'digestate_n_content': 0.03,         # 3% nitrogen
            'digestate_p_content': 0.015,        # 1.5% phosphorus
            'digestate_k_content': 0.015,        # 1.5% potassium
            'digestate_market_price_per_ton': 60, # $/ton (higher quality than compost)
            'electricity_consumption_kwh_per_m3': 0.10,  # For mixing, pumping
            'heat_consumption_kwh_per_m3': 2.0,          # For maintaining 35°C
            'capex': 200000,                     # $ (for digester)
            'opex': 0.15,                        # $/m³ biogas
            'lifetime': 20,                      # years
            'retention_time_days': 20            # 20 days hydraulic retention time
        }

    def calculate_biogas_production(self, sludge_kg: float,
                                   biomass_kg: float) -> Dict:
        """
        Calculate biogas and digestate production

        Args:
            sludge_kg: Sludge input (kg dry solids)
            biomass_kg: Biomass input (kg dry matter)

        Returns:
            Dictionary with production details
        """
        # Total input
        total_input = sludge_kg + biomass_kg

        # Check ratio
        actual_sludge_ratio = sludge_kg / total_input if total_input > 0 else 0
        optimal_ratio = self.specs['sludge_input_ratio']

        # Biogas production
        biogas_m3 = total_input * self.specs['biogas_yield_m3_per_kg']
        biogas_energy_kwh = biogas_m3 * self.specs['biogas_lhv']

        # Methane content
        methane_m3 = biogas_m3 * self.specs['methane_content']

        # Digestate production
        digestate_kg = total_input * self.specs['digestate_output_ratio']

        # Nutrient content
        n_content_kg = digestate_kg * self.specs['digestate_n_content']
        p_content_kg = digestate_kg * self.specs['digestate_p_content']
        k_content_kg = digestate_kg * self.specs['digestate_k_content']

        # Energy requirements
        electricity_required_kwh = biogas_m3 * self.specs['electricity_consumption_kwh_per_m3']
        heat_required_kwh = biogas_m3 * self.specs['heat_consumption_kwh_per_m3']

        return {
            'total_input_kg': total_input,
            'sludge_ratio': actual_sludge_ratio,
            'optimal_ratio': optimal_ratio,
            'biogas_m3': biogas_m3,
            'biogas_energy_kwh': biogas_energy_kwh,
            'methane_m3': methane_m3,
            'methane_content_pct': self.specs['methane_content'] * 100,
            'digestate_kg': digestate_kg,
            'digestate_ton': digestate_kg / 1000,
            'nitrogen_kg': n_content_kg,
            'phosphorus_kg': p_content_kg,
            'potassium_kg': k_content_kg,
            'electricity_required_kwh': electricity_required_kwh,
            'heat_required_kwh': heat_required_kwh,
            'net_energy_kwh': biogas_energy_kwh - electricity_required_kwh - heat_required_kwh,
            'energy_ratio': biogas_energy_kwh / (electricity_required_kwh + heat_required_kwh) if (electricity_required_kwh + heat_required_kwh) > 0 else 0,
            'retention_time_days': self.specs['retention_time_days']
        }

    def calculate_annual_revenue(self, biogas_production: Dict,
                                biogas_value_per_kwh: float = 0.08) -> Dict:
        """
        Calculate annual revenue from biogas and digestate

        Args:
            biogas_production: Production dictionary from calculate_biogas_production()
            biogas_value_per_kwh: Value of biogas energy ($/kWh)

        Returns:
            Revenue details
        """
        # Biogas revenue
        biogas_revenue = biogas_production['biogas_energy_kwh'] * biogas_value_per_kwh

        # Digestate revenue
        digestate_revenue = biogas_production['digestate_ton'] * self.specs['digestate_market_price_per_ton']

        # Operating cost
        operating_cost = biogas_production['biogas_m3'] * self.specs['opex']

        # Gross and net revenue
        gross_revenue = biogas_revenue + digestate_revenue
        net_revenue = gross_revenue - operating_cost

        return {
            'biogas_revenue': biogas_revenue,
            'digestate_revenue': digestate_revenue,
            'gross_revenue': gross_revenue,
            'operating_cost': operating_cost,
            'net_revenue': net_revenue,
            'revenue_split_biogas_pct': biogas_revenue / gross_revenue * 100 if gross_revenue > 0 else 0,
            'revenue_split_digestate_pct': digestate_revenue / gross_revenue * 100 if gross_revenue > 0 else 0
        }

    def calculate_economics(self, annual_sludge_kg: float,
                           annual_biomass_kg: float,
                           biogas_value_per_kwh: float = 0.08) -> Dict:
        """
        Calculate complete economics for anaerobic digester

        Args:
            annual_sludge_kg: Annual sludge input (kg)
            annual_biomass_kg: Annual biomass input (kg)
            biogas_value_per_kwh: Value of biogas energy ($/kWh)

        Returns:
            Economic analysis
        """
        # Production
        production = self.calculate_biogas_production(annual_sludge_kg, annual_biomass_kg)

        # Revenue
        revenue = self.calculate_annual_revenue(production, biogas_value_per_kwh)

        # CAPEX
        total_capex = self.specs['capex']
        annual_capex = total_capex / self.specs['lifetime']

        # Total annual cost
        total_annual_cost = annual_capex + revenue['operating_cost']

        # NPV calculation
        npv = self.calculate_npv(
            capex=total_capex,
            annual_revenue=revenue['gross_revenue'],
            annual_opex=revenue['operating_cost'],
            discount_rate=0.08
        )

        return {
            'production': production,
            'revenue': revenue,
            'capex': total_capex,
            'annual_capex': annual_capex,
            'annual_opex': revenue['operating_cost'],
            'total_annual_cost': total_annual_cost,
            'npv': npv,
            'payback_period': self.calculate_payback_period(
                total_capex,
                revenue['gross_revenue'],
                revenue['operating_cost']
            )
        }

    def compare_with_composting(self, annual_input_kg: float,
                               composting_specs: Dict) -> Dict:
        """
        Compare digester with composting for same input

        Args:
            annual_input_kg: Annual organic input (kg)
            composting_specs: Composting specifications

        Returns:
            Comparison results
        """
        # Split input according to ratios
        sludge_kg = annual_input_kg * self.specs['sludge_input_ratio']
        biomass_kg = annual_input_kg * self.specs['biomass_input_ratio']

        # Digester production
        digester = self.calculate_biogas_production(sludge_kg, biomass_kg)

        # Composting production (approximate)
        compost_kg = annual_input_kg * composting_specs.get('compost_output_ratio', 0.5)

        return {
            'input_kg': annual_input_kg,
            'digester_biogas_kwh': digester['biogas_energy_kwh'],
            'digester_digestate_kg': digester['digestate_kg'],
            'digester_net_energy_kwh': digester['net_energy_kwh'],
            'composting_compost_kg': compost_kg,
            'energy_advantage_digester': True,
            'fertilizer_advantage': 'Similar quality, digester produces more nutrients'
        }

    def calculate_environmental_benefit(self, biogas_production: Dict) -> Dict:
        """
        Calculate environmental benefits

        Args:
            biogas_production: Production dictionary

        Returns:
            Environmental benefit metrics
        """
        # Biogas replaces natural gas
        # Natural gas emissions: ~0.2 kg CO2/kWh
        co2_avoided_biogas = biogas_production['biogas_energy_kwh'] * 0.2

        # Digestate avoids synthetic fertilizer
        # Similar to composting
        avoided_synthetic_fertilizer_ton = biogas_production['digestate_ton'] * 0.4
        co2_avoided_fertilizer = avoided_synthetic_fertilizer_ton * 1000 * 2

        # Total benefit
        total_co2_avoided = co2_avoided_biogas + co2_avoided_fertilizer

        return {
            'co2_avoided_biogas_kg': co2_avoided_biogas,
            'co2_avoided_fertilizer_kg': co2_avoided_fertilizer,
            'total_co2_avoided_kg': total_co2_avoided,
            'avoided_synthetic_fertilizer_ton': avoided_synthetic_fertilizer_ton
        }

    def calculate_digester_sizing(self, daily_input_kg: float) -> Dict:
        """
        Calculate digester volume requirements

        Args:
            daily_input_kg: Daily organic input (kg dry matter)

        Returns:
            Sizing specifications
        """
        # Retention time
        retention_days = self.specs['retention_time_days']

        # Total solids in digester (assume 10% solids content)
        solids_fraction = 0.10
        daily_volume_m3 = daily_input_kg / (solids_fraction * 1000)  # kg/m³

        # Required digester volume
        digester_volume_m3 = daily_volume_m3 * retention_days

        # Add 20% safety factor
        digester_volume_design_m3 = digester_volume_m3 * 1.2

        return {
            'daily_input_kg': daily_input_kg,
            'retention_days': retention_days,
            'required_volume_m3': digester_volume_m3,
            'design_volume_m3': digester_volume_design_m3,
            'daily_biogas_m3': daily_input_kg * self.specs['biogas_yield_m3_per_kg']
        }
