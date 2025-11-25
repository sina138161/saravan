"""
Dewatering Unit Model (آبزدایی)
Separates digestate into solids, wastewater, and recycled water
"""

from typing import Dict
from ..base import TechnologyBase


class Dewatering(TechnologyBase):
    """
    Dewatering Unit (Digestate Separator)

    Separates liquid digestate from anaerobic digester into:
    - Solids → Composting
    - Wastewater → Wastewater treatment
    - Recycled water → Back to digester

    Uses mechanical dewatering (centrifuge or belt press)
    """

    def _define_specs(self) -> Dict:
        """
        Define dewatering unit specifications

        Based on: Commercial digestate dewatering systems
        """
        return {
            'name': 'Digestate_Dewatering_Unit',

            # Separation ratios
            'solids_separation_efficiency': 0.85,  # 85% of solids captured
            'water_recovery_ratio': 0.60,          # 60% recycled to digester
            'wastewater_ratio': 0.25,              # 25% sent to treatment
            'solids_output_ratio': 0.15,           # 15% as solid cake

            # Solid cake properties
            'solid_cake_moisture': 0.25,           # 25% moisture (75% dry solids)
            'solid_cake_organic_content': 0.70,    # 70% organic matter
            'solid_cake_n_content': 0.035,         # 3.5% nitrogen
            'solid_cake_p_content': 0.020,         # 2.0% phosphorus
            'solid_cake_k_content': 0.020,         # 2.0% potassium

            # Wastewater properties
            'wastewater_bod': 2000,                # mg/L BOD
            'wastewater_cod': 4000,                # mg/L COD
            'wastewater_tss': 500,                 # mg/L Total Suspended Solids
            'wastewater_ammonia_n': 1000,          # mg/L Ammonia-N

            # Recycled water properties
            'recycled_water_tss': 100,             # mg/L (relatively clean)
            'recycled_water_nutrient_content': 0.8, # Retains 80% nutrients

            # Energy and costs
            'electricity_kwh_per_m3': 0.15,        # Energy consumption
            'polymer_consumption_kg_per_ton': 2.5, # Polymer for flocculation
            'polymer_price_per_kg': 3.0,           # $/kg
            'capex': 80000,                        # $ (for dewatering equipment)
            'opex_per_m3': 0.10,                   # $/m³ processed
            'lifetime': 15                         # years
        }

    def calculate_dewatering_outputs(self, digestate_input_m3: float,
                                    digestate_solids_content: float = 0.05) -> Dict:
        """
        Calculate dewatering outputs

        Args:
            digestate_input_m3: Digestate input volume (m³)
            digestate_solids_content: Solids content fraction (default 5%)

        Returns:
            Dewatering outputs breakdown
        """
        # Total mass
        # Assume digestate density ≈ 1000 kg/m³
        total_mass_kg = digestate_input_m3 * 1000

        # Solids mass
        solids_mass_kg = total_mass_kg * digestate_solids_content

        # Water mass
        water_mass_kg = total_mass_kg - solids_mass_kg

        # Captured solids (accounting for efficiency)
        captured_solids_kg = solids_mass_kg * self.specs['solids_separation_efficiency']

        # Solid cake output
        # Solid cake has 75% dry solids, 25% moisture
        solid_cake_mass_kg = captured_solids_kg / (1 - self.specs['solid_cake_moisture'])
        solid_cake_water_kg = solid_cake_mass_kg * self.specs['solid_cake_moisture']
        solid_cake_volume_m3 = solid_cake_mass_kg / 800  # Density ~800 kg/m³

        # Remaining water after solid cake removed
        remaining_water_kg = water_mass_kg - solid_cake_water_kg

        # Wastewater output (sent to treatment)
        wastewater_kg = total_mass_kg * self.specs['wastewater_ratio']
        wastewater_m3 = wastewater_kg / 1000

        # Recycled water (back to digester)
        recycled_water_kg = total_mass_kg * self.specs['water_recovery_ratio']
        recycled_water_m3 = recycled_water_kg / 1000

        # Nutrients in solid cake
        n_content_kg = solid_cake_mass_kg * self.specs['solid_cake_n_content']
        p_content_kg = solid_cake_mass_kg * self.specs['solid_cake_p_content']
        k_content_kg = solid_cake_mass_kg * self.specs['solid_cake_k_content']

        # Energy requirement
        electricity_kwh = digestate_input_m3 * self.specs['electricity_kwh_per_m3']

        # Polymer consumption
        # Based on total solids processed
        polymer_kg = (total_mass_kg / 1000) * self.specs['polymer_consumption_kg_per_ton']
        polymer_cost = polymer_kg * self.specs['polymer_price_per_kg']

        return {
            'digestate_input_m3': digestate_input_m3,
            'digestate_input_kg': total_mass_kg,
            'digestate_solids_pct': digestate_solids_content * 100,

            # Solid cake output
            'solid_cake_kg': solid_cake_mass_kg,
            'solid_cake_ton': solid_cake_mass_kg / 1000,
            'solid_cake_volume_m3': solid_cake_volume_m3,
            'solid_cake_dry_solids_kg': captured_solids_kg,
            'solid_cake_moisture_pct': self.specs['solid_cake_moisture'] * 100,
            'nitrogen_in_solids_kg': n_content_kg,
            'phosphorus_in_solids_kg': p_content_kg,
            'potassium_in_solids_kg': k_content_kg,

            # Wastewater output
            'wastewater_m3': wastewater_m3,
            'wastewater_kg': wastewater_kg,
            'wastewater_bod_mg_l': self.specs['wastewater_bod'],
            'wastewater_cod_mg_l': self.specs['wastewater_cod'],

            # Recycled water output
            'recycled_water_m3': recycled_water_m3,
            'recycled_water_kg': recycled_water_kg,
            'recycled_water_nutrients_retained': self.specs['recycled_water_nutrient_content'],

            # Mass balance check
            'mass_balance_check': {
                'input_kg': total_mass_kg,
                'output_kg': solid_cake_mass_kg + wastewater_kg + recycled_water_kg,
                'balanced': abs(total_mass_kg - (solid_cake_mass_kg + wastewater_kg + recycled_water_kg)) < 100
            },

            # Energy and consumables
            'electricity_kwh': electricity_kwh,
            'polymer_kg': polymer_kg,
            'polymer_cost': polymer_cost
        }

    def calculate_annual_operation(self, annual_digestate_m3: float,
                                   digestate_solids_content: float = 0.05,
                                   electricity_price_per_kwh: float = 0.10) -> Dict:
        """
        Calculate annual dewatering operation

        Args:
            annual_digestate_m3: Annual digestate volume (m³)
            digestate_solids_content: Solids content fraction
            electricity_price_per_kwh: Electricity price ($/kWh)

        Returns:
            Annual operation metrics
        """
        # Dewatering outputs
        outputs = self.calculate_dewatering_outputs(
            annual_digestate_m3,
            digestate_solids_content
        )

        # Energy cost
        energy_cost = outputs['electricity_kwh'] * electricity_price_per_kwh

        # Operating cost
        opex_cost = annual_digestate_m3 * self.specs['opex_per_m3']

        # Polymer cost
        polymer_cost = outputs['polymer_cost']

        # Total operating cost
        total_opex = energy_cost + opex_cost + polymer_cost

        # CAPEX (annualized)
        total_capex = self.specs['capex']
        annual_capex = total_capex / self.specs['lifetime']

        # Total annual cost
        total_annual_cost = annual_capex + total_opex

        # Cost per m³ processed
        cost_per_m3 = total_annual_cost / annual_digestate_m3 if annual_digestate_m3 > 0 else 0

        return {
            'annual_digestate_m3': annual_digestate_m3,
            'annual_solid_cake_ton': outputs['solid_cake_ton'],
            'annual_wastewater_m3': outputs['wastewater_m3'],
            'annual_recycled_water_m3': outputs['recycled_water_m3'],
            'annual_electricity_kwh': outputs['electricity_kwh'],
            'energy_cost': energy_cost,
            'polymer_cost': polymer_cost,
            'opex_cost': opex_cost,
            'total_opex': total_opex,
            'annual_capex': annual_capex,
            'total_capex': total_capex,
            'total_annual_cost': total_annual_cost,
            'cost_per_m3': cost_per_m3
        }

    def calculate_water_recovery_benefit(self, annual_digestate_m3: float,
                                         fresh_water_price_per_m3: float = 0.50) -> Dict:
        """
        Calculate benefit of water recycling

        Args:
            annual_digestate_m3: Annual digestate volume
            fresh_water_price_per_m3: Cost of fresh water ($/m³)

        Returns:
            Water recovery benefit
        """
        outputs = self.calculate_dewatering_outputs(annual_digestate_m3)

        # Water saved
        water_saved_m3 = outputs['recycled_water_m3']

        # Value of saved water
        water_value = water_saved_m3 * fresh_water_price_per_m3

        return {
            'water_saved_m3': water_saved_m3,
            'fresh_water_price_per_m3': fresh_water_price_per_m3,
            'annual_water_value': water_value,
            'water_recovery_ratio': self.specs['water_recovery_ratio']
        }

    def size_dewatering_unit(self, peak_digestate_m3_day: float,
                            average_digestate_m3_day: float) -> Dict:
        """
        Size dewatering equipment

        Args:
            peak_digestate_m3_day: Peak daily digestate (m³/day)
            average_digestate_m3_day: Average daily digestate (m³/day)

        Returns:
            Equipment sizing
        """
        # Design capacity (1.3x peak for safety)
        design_capacity_m3_day = peak_digestate_m3_day * 1.3

        # Processing time (assume 8 hours/day operation)
        design_capacity_m3_h = design_capacity_m3_day / 8

        # Capacity utilization
        avg_utilization = average_digestate_m3_day / design_capacity_m3_day

        # CAPEX scaling (base is for ~50 m³/day)
        # Scale with 0.7 power law
        base_capacity = 50  # m³/day
        scaling_factor = (design_capacity_m3_day / base_capacity) ** 0.7
        total_capex = self.specs['capex'] * scaling_factor

        return {
            'peak_digestate_m3_day': peak_digestate_m3_day,
            'average_digestate_m3_day': average_digestate_m3_day,
            'design_capacity_m3_day': design_capacity_m3_day,
            'design_capacity_m3_h': design_capacity_m3_h,
            'avg_utilization': avg_utilization,
            'total_capex': total_capex,
            'operating_hours_per_day': 8
        }
