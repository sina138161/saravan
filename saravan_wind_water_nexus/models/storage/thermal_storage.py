"""
Thermal Energy Storage System Model
Heat storage with charge/discharge capabilities
"""

from typing import Dict
from ..base import TechnologyBase


class ThermalStorage(TechnologyBase):
    """
    Thermal Energy Storage System

    Features:
    - Heat storage for demand buffering
    - Load shifting for thermal energy
    - Integration with heat recovery systems
    - Seasonal/daily storage
    """

    def __init__(self, storage_type: str = 'hot_water_tank', capacity_kwh: float = 5000):
        """
        Initialize thermal storage

        Args:
            storage_type: 'hot_water_tank', 'molten_salt', or 'phase_change_material'
            capacity_kwh: Storage capacity (kWh thermal)
        """
        self.storage_type = storage_type
        self.capacity_kwh = capacity_kwh
        super().__init__()

    def _define_specs(self) -> Dict:
        """
        Define thermal storage specifications
        """
        storage_types = {
            'hot_water_tank': {
                'temperature_range': (60, 90),  # °C (min, max)
                'energy_density': 60,  # kWh/m³
                'charge_efficiency': 0.95,  # σ_T,chr
                'discharge_efficiency': 0.95,  # σ_T,dis
                'thermal_loss_rate': 0.001,  # ϑ_TSS per hour (0.1%/h)
                'insulation_quality': 'good',
                'capex_per_kwh': 30,  # $/kWh
                'opex_per_kwh_year': 1,  # $/kWh/year
                'lifetime': 25,  # years
                'min_soc': 0.10,  # Minimum SOC (10%)
                'max_soc': 0.95,  # Maximum SOC (95%)
            },
            'molten_salt': {
                'temperature_range': (290, 565),  # °C
                'energy_density': 150,  # kWh/m³
                'charge_efficiency': 0.98,
                'discharge_efficiency': 0.98,
                'thermal_loss_rate': 0.0005,  # 0.05%/h
                'insulation_quality': 'excellent',
                'capex_per_kwh': 50,
                'opex_per_kwh_year': 2,
                'lifetime': 30,
                'min_soc': 0.20,
                'max_soc': 0.95,
            },
            'phase_change_material': {
                'temperature_range': (40, 80),  # °C
                'energy_density': 100,  # kWh/m³
                'charge_efficiency': 0.92,
                'discharge_efficiency': 0.92,
                'thermal_loss_rate': 0.0008,  # 0.08%/h
                'insulation_quality': 'very_good',
                'capex_per_kwh': 60,
                'opex_per_kwh_year': 3,
                'lifetime': 20,
                'min_soc': 0.05,
                'max_soc': 0.98,
            }
        }

        storage_spec = storage_types[self.storage_type]

        # Calculate CAPEX and OPEX
        total_capex = self.capacity_kwh * storage_spec['capex_per_kwh']
        annual_opex = self.capacity_kwh * storage_spec['opex_per_kwh_year']

        # Calculate volume
        volume_m3 = self.capacity_kwh / storage_spec['energy_density']

        return {
            'name': f'{self.storage_type.replace("_", " ").title()}_Thermal_Storage',
            'storage_type': self.storage_type,
            'storage_spec': storage_spec,

            # Exact formula parameters (similar to battery)
            'P_TSS_cap': self.capacity_kwh,  # Rated capacity (kWh thermal)
            'sigma_T_chr': storage_spec['charge_efficiency'],  # σ_T,chr: charging efficiency
            'sigma_T_dis': storage_spec['discharge_efficiency'],  # σ_T,dis: discharging efficiency
            'theta_TSS': storage_spec['thermal_loss_rate'],  # ϑ_TSS: thermal loss rate
            'soc_min': storage_spec['min_soc'],  # Minimum SOC
            'soc_max': storage_spec['max_soc'],  # Maximum SOC

            # Physical properties
            'volume_m3': volume_m3,
            'temperature_min_c': storage_spec['temperature_range'][0],
            'temperature_max_c': storage_spec['temperature_range'][1],

            # Economics
            'capex': total_capex,
            'opex': annual_opex,
            'lifetime': storage_spec['lifetime']
        }

    def calculate_soc_charging(self, p_TSS_prev: float,
                               p_T_chr: float,
                               delta_t: float = 1.0) -> Dict:
        """
        Calculate thermal storage SOC during charging using exact formula (similar to battery)

        Formula (Charging):
            p_TSS,soc(t) = (1 - ϑ_TSS) × p_TSS(t-1) + (p_T,chr(t) × σ_T,chr / P_TSS,cap) × Δt

        Args:
            p_TSS_prev: Previous SOC p_TSS(t-1) (fraction 0-1)
            p_T_chr: Charging heat power p_T,chr(t) (kW thermal)
            delta_t: Time step Δt (hours, default 1.0)

        Returns:
            Dictionary with SOC and thermal energy details
        """
        # Get specs
        theta_TSS = self.specs['theta_TSS']
        sigma_T_chr = self.specs['sigma_T_chr']
        P_TSS_cap = self.specs['P_TSS_cap']
        soc_min = self.specs['soc_min']
        soc_max = self.specs['soc_max']

        # Formula: p_TSS,soc(t) = (1 - ϑ_TSS) × p_TSS(t-1) + (p_T,chr(t) × σ_T,chr / P_TSS,cap) × Δt
        p_TSS_soc = (1 - theta_TSS) * p_TSS_prev + (p_T_chr * sigma_T_chr / P_TSS_cap) * delta_t

        # Constraint check: soc_min ≤ p_TSS,soc(t) ≤ soc_max
        soc_constraint_met = soc_min <= p_TSS_soc <= soc_max
        violations = []

        if p_TSS_soc < soc_min:
            violations.append(f"SOC {p_TSS_soc:.3f} below minimum {soc_min:.3f}")
        elif p_TSS_soc > soc_max:
            violations.append(f"SOC {p_TSS_soc:.3f} exceeds maximum {soc_max:.3f}")

        # Calculate energy stored
        energy_stored_kwh = p_TSS_soc * P_TSS_cap

        # Thermal loss
        thermal_loss = theta_TSS * p_TSS_prev * P_TSS_cap

        # Charging losses
        charging_loss = p_T_chr * delta_t * (1 - sigma_T_chr)

        return {
            # Inputs
            'p_TSS_prev': p_TSS_prev,
            'p_T_chr_kw': p_T_chr,
            'delta_t_hours': delta_t,

            # Output
            'p_TSS_soc': p_TSS_soc,
            'soc_pct': p_TSS_soc * 100,
            'energy_stored_kwh': energy_stored_kwh,

            # Parameters
            'theta_TSS': theta_TSS,
            'sigma_T_chr': sigma_T_chr,
            'P_TSS_cap_kwh': P_TSS_cap,

            # Losses
            'thermal_loss_kwh': thermal_loss,
            'charging_loss_kwh': charging_loss,
            'total_loss_kwh': thermal_loss + charging_loss,

            # Constraints
            'soc_min': soc_min,
            'soc_max': soc_max,
            'soc_constraint_met': soc_constraint_met,
            'violations': violations,

            # Formula used
            'mode': 'charging',
            'formula': 'p_TSS,soc(t) = (1 - ϑ_TSS) × p_TSS(t-1) + (p_T,chr(t) × σ_T,chr / P_TSS,cap) × Δt'
        }

    def calculate_soc_discharging(self, p_TSS_prev: float,
                                  p_T_dis: float,
                                  delta_t: float = 1.0) -> Dict:
        """
        Calculate thermal storage SOC during discharging using exact formula (similar to battery)

        Formula (Discharging):
            p_TSS,soc(t) = (1 - ϑ_TSS) × p_TSS(t-1) - (p_T,dis(t) / (σ_T,dis × P_TSS,cap)) × Δt

        Args:
            p_TSS_prev: Previous SOC p_TSS(t-1) (fraction 0-1)
            p_T_dis: Discharging heat power p_T,dis(t) (kW thermal)
            delta_t: Time step Δt (hours, default 1.0)

        Returns:
            Dictionary with SOC and thermal energy details
        """
        # Get specs
        theta_TSS = self.specs['theta_TSS']
        sigma_T_dis = self.specs['sigma_T_dis']
        P_TSS_cap = self.specs['P_TSS_cap']
        soc_min = self.specs['soc_min']
        soc_max = self.specs['soc_max']

        # Formula: p_TSS,soc(t) = (1 - ϑ_TSS) × p_TSS(t-1) - (p_T,dis(t) / (σ_T,dis × P_TSS,cap)) × Δt
        p_TSS_soc = (1 - theta_TSS) * p_TSS_prev - (p_T_dis / (sigma_T_dis * P_TSS_cap)) * delta_t

        # Constraint check: soc_min ≤ p_TSS,soc(t) ≤ soc_max
        soc_constraint_met = soc_min <= p_TSS_soc <= soc_max
        violations = []

        if p_TSS_soc < soc_min:
            violations.append(f"SOC {p_TSS_soc:.3f} below minimum {soc_min:.3f}")
        elif p_TSS_soc > soc_max:
            violations.append(f"SOC {p_TSS_soc:.3f} exceeds maximum {soc_max:.3f}")

        # Calculate energy stored
        energy_stored_kwh = p_TSS_soc * P_TSS_cap

        # Thermal loss
        thermal_loss = theta_TSS * p_TSS_prev * P_TSS_cap

        # Discharging losses
        discharging_loss = p_T_dis * delta_t * (1 - sigma_T_dis)

        return {
            # Inputs
            'p_TSS_prev': p_TSS_prev,
            'p_T_dis_kw': p_T_dis,
            'delta_t_hours': delta_t,

            # Output
            'p_TSS_soc': p_TSS_soc,
            'soc_pct': p_TSS_soc * 100,
            'energy_stored_kwh': energy_stored_kwh,

            # Parameters
            'theta_TSS': theta_TSS,
            'sigma_T_dis': sigma_T_dis,
            'P_TSS_cap_kwh': P_TSS_cap,

            # Losses
            'thermal_loss_kwh': thermal_loss,
            'discharging_loss_kwh': discharging_loss,
            'total_loss_kwh': thermal_loss + discharging_loss,

            # Constraints
            'soc_min': soc_min,
            'soc_max': soc_max,
            'soc_constraint_met': soc_constraint_met,
            'violations': violations,

            # Formula used
            'mode': 'discharging',
            'formula': 'p_TSS,soc(t) = (1 - ϑ_TSS) × p_TSS(t-1) - (p_T,dis(t) / (σ_T,dis × P_TSS,cap)) × Δt'
        }

    def calculate_round_trip_efficiency(self) -> float:
        """
        Calculate round-trip efficiency

        η_round_trip = σ_T,chr × σ_T,dis

        Returns:
            Round-trip efficiency (fraction)
        """
        return self.specs['sigma_T_chr'] * self.specs['sigma_T_dis']

    def calculate_temperature_from_soc(self, soc: float) -> float:
        """
        Estimate storage temperature from SOC

        Args:
            soc: State of charge (fraction 0-1)

        Returns:
            Estimated temperature (°C)
        """
        T_min = self.specs['temperature_min_c']
        T_max = self.specs['temperature_max_c']

        # Linear approximation
        temperature = T_min + (T_max - T_min) * soc

        return temperature

    def calculate_exergy_efficiency(self, T_amb_c: float = 20) -> Dict:
        """
        Calculate exergy efficiency of thermal storage

        Args:
            T_amb_c: Ambient temperature (°C, default 20)

        Returns:
            Exergy analysis
        """
        T_storage_max = self.specs['temperature_max_c']
        T_amb_k = T_amb_c + 273.15
        T_storage_k = T_storage_max + 273.15

        # Carnot efficiency
        carnot_efficiency = 1 - (T_amb_k / T_storage_k)

        # Exergy efficiency (simplified)
        exergy_efficiency = self.calculate_round_trip_efficiency() * carnot_efficiency

        return {
            'T_amb_c': T_amb_c,
            'T_storage_max_c': T_storage_max,
            'carnot_efficiency': carnot_efficiency,
            'round_trip_efficiency': self.calculate_round_trip_efficiency(),
            'exergy_efficiency': exergy_efficiency
        }
