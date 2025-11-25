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

            # Feedstock properties - Sludge
            'TS_s': 0.04,                        # Total solids in sludge (4%)
            'VS_s': 0.70,                        # Volatile solids ratio in sludge (70% of TS)
            'Y_s': 0.35,                         # Specific biogas yield for sludge (m³/kg VS)
            'CN_s': 8.0,                         # Carbon-to-nitrogen ratio for sludge

            # Feedstock properties - Biomass
            'TS_bm': 0.25,                       # Total solids in biomass (25%)
            'VS_bm': 0.90,                       # Volatile solids ratio in biomass (90% of TS)
            'Y_bm': 0.55,                        # Specific biogas yield for biomass (m³/kg VS)
            'CN_bm': 30.0,                       # Carbon-to-nitrogen ratio for biomass

            # Digester operating parameters
            'eta_ad': 0.85,                      # Digestion efficiency (85%)
            'TS_digestate': 0.08,                # Target TS in digestate (8%)
            'V_digester': 1000,                  # Digester volume (m³)

            # Heat requirements
            'T_target': 35,                      # Target temperature (°C) mesophilic
            'T_amb': 20,                         # Ambient temperature (°C)
            'Cp_feed': 4.18,                     # Specific heat of feed (kJ/kg·°C) ≈ water
            'alpha_loss_winter': 1.08,           # Heat loss coefficient winter
            'alpha_loss_summer': 1.05,           # Heat loss coefficient summer

            # Constraints
            'OLR_max': 4.0,                      # Maximum Organic Loading Rate (kg VS/m³/day)
            'HRT_min': 15,                       # Minimum Hydraulic Retention Time (days)
            'CN_min': 20,                        # Minimum C/N ratio
            'CN_max': 30,                        # Maximum C/N ratio
            'Delta_Q_bg_max': 50,                # Maximum biogas production change (m³/h)

            # Legacy parameters (kept for compatibility)
            'methane_content': 0.60,             # 60% CH4, 40% CO2
            'biogas_lhv': 6.0,                   # kWh/m³
            'digestate_n_content': 0.03,         # 3% nitrogen (of dry solids)
            'digestate_p_content': 0.015,        # 1.5% phosphorus
            'digestate_k_content': 0.015,        # 1.5% potassium

            # Economics
            'capex': 200000,                     # $ (for digester vessel + equipment)
            'opex': 0.15,                        # $/m³ biogas produced
            'lifetime': 20                       # years
        }

    def calculate_biogas_production_exact(self, m_s_ton_h: float,
                                          m_bm_ton_h: float,
                                          season: str = 'winter',
                                          previous_biogas_m3_h: float = None,
                                          available_biomass_ton_h: float = None) -> Dict:
        """
        Calculate biogas production using exact formulas

        Formulas:
            q_ad,bg(t) = η_ad × (m_s(t)×TS_s×VS_s×Y_s + m_bm(t)×TS_bm×VS_bm×Y_bm)
            v_ad,fw(t) = m_s(t)×[TS_s/TS_digestate - 1] + m_bm(t)×[TS_bm/TS_digestate - 1]
            h_ad(t) = α_loss × [(m_s(t) + m_bm(t) + v_ad,fw(t)) × C_p,feed × (T_target - T_amb)]
            m_ad,d(t) = m_s(t) + m_bm(t) + v_ad,fw(t)

        Args:
            m_s_ton_h: Sludge feed rate (ton/h)
            m_bm_ton_h: Biomass feed rate (ton/h)
            season: 'winter' or 'summer' (for heat loss coefficient)
            previous_biogas_m3_h: Previous biogas production for stability check (m³/h)
            available_biomass_ton_h: Available biomass resource M_bm(t) for constraint

        Returns:
            Dictionary with all outputs and constraint checks
        """
        # Get specs
        TS_s = self.specs['TS_s']
        VS_s = self.specs['VS_s']
        Y_s = self.specs['Y_s']
        CN_s = self.specs['CN_s']

        TS_bm = self.specs['TS_bm']
        VS_bm = self.specs['VS_bm']
        Y_bm = self.specs['Y_bm']
        CN_bm = self.specs['CN_bm']

        eta_ad = self.specs['eta_ad']
        TS_digestate = self.specs['TS_digestate']
        V_digester = self.specs['V_digester']

        T_target = self.specs['T_target']
        T_amb = self.specs['T_amb']
        Cp_feed = self.specs['Cp_feed']
        alpha_loss = self.specs['alpha_loss_winter'] if season == 'winter' else self.specs['alpha_loss_summer']

        # Formula 1: Biogas production
        # q_ad,bg(t) = η_ad × (m_s(t)×TS_s×VS_s×Y_s + m_bm(t)×TS_bm×VS_bm×Y_bm)
        q_ad_bg = eta_ad * (
            m_s_ton_h * TS_s * VS_s * Y_s +
            m_bm_ton_h * TS_bm * VS_bm * Y_bm
        )

        # Formula 2: Fresh water consumption
        # v_ad,fw(t) = m_s(t)×[TS_s/TS_digestate - 1] + m_bm(t)×[TS_bm/TS_digestate - 1]
        v_ad_fw = (
            m_s_ton_h * (TS_s / TS_digestate - 1) +
            m_bm_ton_h * (TS_bm / TS_digestate - 1)
        )

        # Formula 3: Heat input required
        # h_ad(t) = α_loss × [(m_s(t) + m_bm(t) + v_ad,fw(t)) × C_p,feed × (T_target - T_amb)]
        # Note: Cp_feed is in kJ/kg·°C, convert to kWh: 1 kWh = 3600 kJ
        total_mass_ton = m_s_ton_h + m_bm_ton_h + v_ad_fw
        h_ad_kJ = alpha_loss * (total_mass_ton * 1000) * Cp_feed * (T_target - T_amb)
        h_ad = h_ad_kJ / 3600  # Convert to kWh

        # Formula 4: Digestate output
        # m_ad,d(t) = m_s(t) + m_bm(t) + v_ad,fw(t)
        m_ad_d = total_mass_ton

        # Constraint 1: Organic Loading Rate
        # OLR_max ≥ olr(t) = (m_s(t)×TS_s×VS_s + m_bm(t)×TS_bm×VS_bm) / V_digester
        # Convert to daily basis (ton/h × 24 h/day = ton/day, × 1000 = kg/day)
        olr = ((m_s_ton_h * TS_s * VS_s + m_bm_ton_h * TS_bm * VS_bm) * 24 * 1000) / V_digester
        olr_constraint_met = olr <= self.specs['OLR_max']

        # Constraint 2: Hydraulic Retention Time
        # HRT_min ≤ hrt(t) = V_digester / (m_s(t) + m_bm(t) + v_ad,fw(t))
        # Convert to daily basis: V_digester (m³) / (ton/h × 24 h/day × m³/ton)
        # Assume 1 ton ≈ 1 m³ for liquid digestate
        hrt = V_digester / (total_mass_ton * 24) if total_mass_ton > 0 else float('inf')
        hrt_constraint_met = hrt >= self.specs['HRT_min']

        # Constraint 3: C/N ratio
        # C/N_min ≤ (m_s(t)×C/N_s + m_bm(t)×C/N_bm) / (m_s(t) + m_bm(t)) ≤ C/N_max
        total_feed = m_s_ton_h + m_bm_ton_h
        cn_ratio = (m_s_ton_h * CN_s + m_bm_ton_h * CN_bm) / total_feed if total_feed > 0 else 0
        cn_constraint_met = self.specs['CN_min'] <= cn_ratio <= self.specs['CN_max']

        # Constraint 4: Biomass availability
        # m_bm(t) ≤ M_bm(t)
        biomass_constraint_met = True
        if available_biomass_ton_h is not None:
            biomass_constraint_met = m_bm_ton_h <= available_biomass_ton_h

        # Constraint 5: Stability
        # |q_ad,bg(t) - q_ad,bg(t-1)| ≤ ΔQ_bg,max
        stability_constraint_met = True
        biogas_change = 0
        if previous_biogas_m3_h is not None:
            biogas_change = abs(q_ad_bg - previous_biogas_m3_h)
            stability_constraint_met = biogas_change <= self.specs['Delta_Q_bg_max']

        # Calculate methane and CO2
        methane_m3_h = q_ad_bg * self.specs['methane_content']
        co2_m3_h = q_ad_bg * (1 - self.specs['methane_content'])
        biogas_energy_kwh_h = q_ad_bg * self.specs['biogas_lhv']

        return {
            # Inputs
            'm_s_ton_h': m_s_ton_h,
            'm_bm_ton_h': m_bm_ton_h,
            'season': season,

            # Outputs from formulas
            'q_ad_bg_m3_h': q_ad_bg,
            'v_ad_fw_ton_h': v_ad_fw,
            'v_ad_fw_m3_h': v_ad_fw,  # Assuming 1 ton ≈ 1 m³ for water
            'h_ad_kwh_h': h_ad,
            'm_ad_d_ton_h': m_ad_d,
            'm_ad_d_m3_h': m_ad_d,  # Assuming 1 ton ≈ 1 m³

            # Biogas composition
            'methane_m3_h': methane_m3_h,
            'co2_m3_h': co2_m3_h,
            'biogas_energy_kwh_h': biogas_energy_kwh_h,

            # Constraints
            'olr_kg_vs_m3_day': olr,
            'olr_max': self.specs['OLR_max'],
            'olr_constraint_met': olr_constraint_met,

            'hrt_days': hrt,
            'hrt_min': self.specs['HRT_min'],
            'hrt_constraint_met': hrt_constraint_met,

            'cn_ratio': cn_ratio,
            'cn_min': self.specs['CN_min'],
            'cn_max': self.specs['CN_max'],
            'cn_constraint_met': cn_constraint_met,

            'biomass_constraint_met': biomass_constraint_met,
            'available_biomass_ton_h': available_biomass_ton_h,

            'biogas_change_m3_h': biogas_change,
            'delta_q_bg_max': self.specs['Delta_Q_bg_max'],
            'stability_constraint_met': stability_constraint_met,

            # Overall
            'all_constraints_met': (
                olr_constraint_met and
                hrt_constraint_met and
                cn_constraint_met and
                biomass_constraint_met and
                stability_constraint_met
            ),

            # Formulas used
            'formulas': {
                'biogas': 'q_ad,bg(t) = η_ad × (m_s(t)×TS_s×VS_s×Y_s + m_bm(t)×TS_bm×VS_bm×Y_bm)',
                'freshwater': 'v_ad,fw(t) = m_s(t)×[TS_s/TS_digestate - 1] + m_bm(t)×[TS_bm/TS_digestate - 1]',
                'heat': 'h_ad(t) = α_loss × [(m_s(t) + m_bm(t) + v_ad,fw(t)) × C_p,feed × (T_target - T_amb)]',
                'digestate': 'm_ad,d(t) = m_s(t) + m_bm(t) + v_ad,fw(t)'
            }
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
