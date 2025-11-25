"""
Composting System Model
Aerobic composting of sludge and biomass to produce fertilizer
"""

from typing import Dict
from ..base import TechnologyBase


class Composting(TechnologyBase):
    """
    Composting System

    Process:
    Sludge + Biomass → Compost (fertilizer)

    Outputs:
    - Compost (organic fertilizer)
    - CO2 emissions (from decomposition)
    """

    def _define_specs(self) -> Dict:
        """
        Define composting system specifications

        Based on: Commercial composting operations and research
        """
        return {
            'name': 'Aerobic_Composting_System',
            'sludge_input_ratio': 0.70,          # 70% sludge, 30% biomass
            'biomass_input_ratio': 0.30,
            'compost_output_ratio': 0.50,        # 50% mass reduction (moisture loss)
            'duration_days': 60,                 # 60 days composting
            'n_content': 0.02,                   # 2% nitrogen content
            'p_content': 0.01,                   # 1% phosphorus
            'k_content': 0.01,                   # 1% potassium
            'market_price_per_ton': 50,          # $/ton
            'capex': 50000,                      # $ (for composting facility)
            'opex': 10,                          # $/ton processed
            'lifetime': 20                       # years
        }

    def calculate_compost_production(self, sludge_kg: float,
                                    biomass_kg: float) -> Dict:
        """
        Calculate compost production from inputs

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

        # Compost output
        compost_output = total_input * self.specs['compost_output_ratio']

        # Nutrient content
        n_content_kg = compost_output * self.specs['n_content']
        p_content_kg = compost_output * self.specs['p_content']
        k_content_kg = compost_output * self.specs['k_content']

        return {
            'total_input_kg': total_input,
            'sludge_ratio': actual_sludge_ratio,
            'optimal_ratio': optimal_ratio,
            'ratio_deviation': abs(actual_sludge_ratio - optimal_ratio),
            'compost_output_kg': compost_output,
            'compost_output_ton': compost_output / 1000,
            'nitrogen_kg': n_content_kg,
            'phosphorus_kg': p_content_kg,
            'potassium_kg': k_content_kg,
            'duration_days': self.specs['duration_days']
        }

    def calculate_sludge_from_wastewater(self, wastewater_m3: float) -> float:
        """
        Calculate sludge production from wastewater treatment

        Args:
            wastewater_m3: Volume of wastewater treated

        Returns:
            Sludge produced (kg dry solids)
        """
        # Typical sludge production: 50-100 g dry solids per m³ wastewater
        sludge_production_kg_per_m3 = 0.075  # 75 g/m³ (average)
        return wastewater_m3 * sludge_production_kg_per_m3

    def calculate_annual_revenue(self, annual_compost_ton: float) -> Dict:
        """
        Calculate annual revenue from compost sales

        Args:
            annual_compost_ton: Annual compost production (tons)

        Returns:
            Revenue details
        """
        # Market price
        price_per_ton = self.specs['market_price_per_ton']

        # Revenue
        gross_revenue = annual_compost_ton * price_per_ton

        # Operating cost
        operating_cost = annual_compost_ton * self.specs['opex']

        # Net revenue
        net_revenue = gross_revenue - operating_cost

        return {
            'annual_compost_ton': annual_compost_ton,
            'price_per_ton': price_per_ton,
            'gross_revenue': gross_revenue,
            'operating_cost': operating_cost,
            'net_revenue': net_revenue,
            'profit_margin': net_revenue / gross_revenue if gross_revenue > 0 else 0
        }

    def calculate_economics(self, annual_sludge_kg: float,
                           annual_biomass_kg: float,
                           facility_capacity_ton_year: float = 500) -> Dict:
        """
        Calculate complete economics for composting system

        Args:
            annual_sludge_kg: Annual sludge input (kg)
            annual_biomass_kg: Annual biomass input (kg)
            facility_capacity_ton_year: Facility capacity (tons/year)

        Returns:
            Economic analysis
        """
        # Production
        production = self.calculate_compost_production(annual_sludge_kg, annual_biomass_kg)
        annual_compost_ton = production['compost_output_ton']

        # Revenue
        revenue = self.calculate_annual_revenue(annual_compost_ton)

        # CAPEX
        total_capex = self.specs['capex']
        annual_capex = total_capex / self.specs['lifetime']

        # Total annual cost
        total_annual_cost = annual_capex + revenue['operating_cost']

        # NPV calculation (simplified)
        annual_net_cash_flow = revenue['net_revenue']
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

    def calculate_environmental_benefit(self, annual_compost_ton: float) -> Dict:
        """
        Calculate environmental benefits

        Args:
            annual_compost_ton: Annual compost production (tons)

        Returns:
            Environmental benefit metrics
        """
        # Avoided chemical fertilizer (approximate equivalent)
        # 1 ton compost ≈ 0.3 ton synthetic fertilizer (NPK equivalent)
        avoided_synthetic_fertilizer_ton = annual_compost_ton * 0.3

        # CO2 savings from avoiding synthetic fertilizer production
        # ~2 kg CO2 per kg synthetic fertilizer
        co2_saved_kg = avoided_synthetic_fertilizer_ton * 1000 * 2

        # Soil carbon sequestration
        # Compost adds ~0.2 kg C per kg compost applied
        carbon_sequestered_kg = annual_compost_ton * 1000 * 0.2

        return {
            'avoided_synthetic_fertilizer_ton': avoided_synthetic_fertilizer_ton,
            'co2_avoided_production_kg': co2_saved_kg,
            'carbon_sequestered_kg': carbon_sequestered_kg,
            'total_co2_benefit_kg': co2_saved_kg + carbon_sequestered_kg * 3.67  # C to CO2
        }
