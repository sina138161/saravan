"""
Battery Energy Storage System (ESS) Model
Electrical energy storage with charge/discharge capabilities
"""

from typing import Dict
from ..base import TechnologyBase


class BatteryESS(TechnologyBase):
    """
    Battery Energy Storage System (ESS)

    Features:
    - Charge/discharge for energy arbitrage
    - Peak shaving and load shifting
    - Renewable energy integration
    - Grid services
    """

    def __init__(self, battery_type: str = 'lithium_ion', capacity_kwh: float = 1000):
        """
        Initialize battery ESS

        Args:
            battery_type: 'lithium_ion', 'lead_acid', or 'flow_battery'
            capacity_kwh: Battery capacity (kWh)
        """
        self.battery_type = battery_type
        self.capacity_kwh = capacity_kwh
        super().__init__()

    def _define_specs(self) -> Dict:
        """
        Define battery ESS specifications
        """
        battery_types = {
            'lithium_ion': {
                'energy_density': 150,  # Wh/kg
                'power_density': 300,  # W/kg
                'cycle_life': 5000,  # cycles
                'charge_efficiency': 0.95,  # σ_E,chr
                'discharge_efficiency': 0.95,  # σ_E,dis
                'self_discharge_rate': 0.00001,  # ϑ_ESS per hour (0.001%/h)
                'depth_of_discharge': 0.90,  # Maximum DOD
                'capex_per_kwh': 300,  # $/kWh
                'opex_per_kwh_year': 10,  # $/kWh/year
                'lifetime': 15,  # years
                'min_soc': 0.10,  # Minimum SOC (10%)
                'max_soc': 0.95,  # Maximum SOC (95%)
            },
            'lead_acid': {
                'energy_density': 40,  # Wh/kg
                'power_density': 100,  # W/kg
                'cycle_life': 1500,  # cycles
                'charge_efficiency': 0.85,
                'discharge_efficiency': 0.85,
                'self_discharge_rate': 0.0001,  # 0.01%/h
                'depth_of_discharge': 0.50,
                'capex_per_kwh': 150,
                'opex_per_kwh_year': 15,
                'lifetime': 10,
                'min_soc': 0.20,
                'max_soc': 0.90,
            },
            'flow_battery': {
                'energy_density': 25,  # Wh/kg
                'power_density': 20,  # W/kg
                'cycle_life': 10000,  # cycles
                'charge_efficiency': 0.75,
                'discharge_efficiency': 0.75,
                'self_discharge_rate': 0.00005,  # 0.005%/h
                'depth_of_discharge': 1.00,
                'capex_per_kwh': 400,
                'opex_per_kwh_year': 20,
                'lifetime': 20,
                'min_soc': 0.00,
                'max_soc': 1.00,
            }
        }

        battery_spec = battery_types[self.battery_type]

        # Calculate CAPEX and OPEX
        total_capex = self.capacity_kwh * battery_spec['capex_per_kwh']
        annual_opex = self.capacity_kwh * battery_spec['opex_per_kwh_year']

        return {
            'name': f'{self.battery_type.replace("_", " ").title()}_Battery_ESS',
            'battery_type': self.battery_type,
            'battery_spec': battery_spec,

            # Exact formula parameters
            'P_ESS_cap': self.capacity_kwh,  # Rated capacity (kWh)
            'sigma_E_chr': battery_spec['charge_efficiency'],  # σ_E,chr: charging efficiency
            'sigma_E_dis': battery_spec['discharge_efficiency'],  # σ_E,dis: discharging efficiency
            'theta_ESS': battery_spec['self_discharge_rate'],  # ϑ_ESS: self-depletion rate
            'soc_min': battery_spec['min_soc'],  # Minimum SOC
            'soc_max': battery_spec['max_soc'],  # Maximum SOC

            # Economics
            'capex': total_capex,
            'opex': annual_opex,
            'lifetime': battery_spec['lifetime']
        }

    def calculate_soc_charging(self, p_ESS_prev: float,
                               p_E_chr: float,
                               delta_t: float = 1.0) -> Dict:
        """
        Calculate battery SOC during charging using exact formula

        Formula (Charging):
            p_ESS,soc(t) = (1 - ϑ_ESS) × p_ESS(t-1) + (p_E,chr(t) × σ_E,chr / P_ESS,cap) × Δt

        Args:
            p_ESS_prev: Previous SOC p_ESS(t-1) (fraction 0-1)
            p_E_chr: Charging power p_E,chr(t) (kW)
            delta_t: Time step Δt (hours, default 1.0)

        Returns:
            Dictionary with SOC and energy details
        """
        # Get specs
        theta_ESS = self.specs['theta_ESS']
        sigma_E_chr = self.specs['sigma_E_chr']
        P_ESS_cap = self.specs['P_ESS_cap']
        soc_min = self.specs['soc_min']
        soc_max = self.specs['soc_max']

        # Formula: p_ESS,soc(t) = (1 - ϑ_ESS) × p_ESS(t-1) + (p_E,chr(t) × σ_E,chr / P_ESS,cap) × Δt
        p_ESS_soc = (1 - theta_ESS) * p_ESS_prev + (p_E_chr * sigma_E_chr / P_ESS_cap) * delta_t

        # Constraint check: soc_min ≤ p_ESS,soc(t) ≤ soc_max
        soc_constraint_met = soc_min <= p_ESS_soc <= soc_max
        violations = []

        if p_ESS_soc < soc_min:
            violations.append(f"SOC {p_ESS_soc:.3f} below minimum {soc_min:.3f}")
        elif p_ESS_soc > soc_max:
            violations.append(f"SOC {p_ESS_soc:.3f} exceeds maximum {soc_max:.3f}")

        # Calculate energy stored
        energy_stored_kwh = p_ESS_soc * P_ESS_cap

        # Self-discharge loss
        self_discharge_loss = theta_ESS * p_ESS_prev * P_ESS_cap

        # Charging losses
        charging_loss = p_E_chr * delta_t * (1 - sigma_E_chr)

        return {
            # Inputs
            'p_ESS_prev': p_ESS_prev,
            'p_E_chr_kw': p_E_chr,
            'delta_t_hours': delta_t,

            # Output
            'p_ESS_soc': p_ESS_soc,
            'soc_pct': p_ESS_soc * 100,
            'energy_stored_kwh': energy_stored_kwh,

            # Parameters
            'theta_ESS': theta_ESS,
            'sigma_E_chr': sigma_E_chr,
            'P_ESS_cap_kwh': P_ESS_cap,

            # Losses
            'self_discharge_loss_kwh': self_discharge_loss,
            'charging_loss_kwh': charging_loss,
            'total_loss_kwh': self_discharge_loss + charging_loss,

            # Constraints
            'soc_min': soc_min,
            'soc_max': soc_max,
            'soc_constraint_met': soc_constraint_met,
            'violations': violations,

            # Formula used
            'mode': 'charging',
            'formula': 'p_ESS,soc(t) = (1 - ϑ_ESS) × p_ESS(t-1) + (p_E,chr(t) × σ_E,chr / P_ESS,cap) × Δt'
        }

    def calculate_soc_discharging(self, p_ESS_prev: float,
                                  p_E_dis: float,
                                  delta_t: float = 1.0) -> Dict:
        """
        Calculate battery SOC during discharging using exact formula

        Formula (Discharging):
            p_ESS,soc(t) = (1 - ϑ_ESS) × p_ESS(t-1) - (p_E,dis(t) / (σ_E,dis × P_ESS,cap)) × Δt

        Args:
            p_ESS_prev: Previous SOC p_ESS(t-1) (fraction 0-1)
            p_E_dis: Discharging power p_E,dis(t) (kW)
            delta_t: Time step Δt (hours, default 1.0)

        Returns:
            Dictionary with SOC and energy details
        """
        # Get specs
        theta_ESS = self.specs['theta_ESS']
        sigma_E_dis = self.specs['sigma_E_dis']
        P_ESS_cap = self.specs['P_ESS_cap']
        soc_min = self.specs['soc_min']
        soc_max = self.specs['soc_max']

        # Formula: p_ESS,soc(t) = (1 - ϑ_ESS) × p_ESS(t-1) - (p_E,dis(t) / (σ_E,dis × P_ESS,cap)) × Δt
        p_ESS_soc = (1 - theta_ESS) * p_ESS_prev - (p_E_dis / (sigma_E_dis * P_ESS_cap)) * delta_t

        # Constraint check: soc_min ≤ p_ESS,soc(t) ≤ soc_max
        soc_constraint_met = soc_min <= p_ESS_soc <= soc_max
        violations = []

        if p_ESS_soc < soc_min:
            violations.append(f"SOC {p_ESS_soc:.3f} below minimum {soc_min:.3f}")
        elif p_ESS_soc > soc_max:
            violations.append(f"SOC {p_ESS_soc:.3f} exceeds maximum {soc_max:.3f}")

        # Calculate energy stored
        energy_stored_kwh = p_ESS_soc * P_ESS_cap

        # Self-discharge loss
        self_discharge_loss = theta_ESS * p_ESS_prev * P_ESS_cap

        # Discharging losses
        discharging_loss = p_E_dis * delta_t * (1 - sigma_E_dis)

        return {
            # Inputs
            'p_ESS_prev': p_ESS_prev,
            'p_E_dis_kw': p_E_dis,
            'delta_t_hours': delta_t,

            # Output
            'p_ESS_soc': p_ESS_soc,
            'soc_pct': p_ESS_soc * 100,
            'energy_stored_kwh': energy_stored_kwh,

            # Parameters
            'theta_ESS': theta_ESS,
            'sigma_E_dis': sigma_E_dis,
            'P_ESS_cap_kwh': P_ESS_cap,

            # Losses
            'self_discharge_loss_kwh': self_discharge_loss,
            'discharging_loss_kwh': discharging_loss,
            'total_loss_kwh': self_discharge_loss + discharging_loss,

            # Constraints
            'soc_min': soc_min,
            'soc_max': soc_max,
            'soc_constraint_met': soc_constraint_met,
            'violations': violations,

            # Formula used
            'mode': 'discharging',
            'formula': 'p_ESS,soc(t) = (1 - ϑ_ESS) × p_ESS(t-1) - (p_E,dis(t) / (σ_E,dis × P_ESS,cap)) × Δt'
        }

    def calculate_round_trip_efficiency(self) -> float:
        """
        Calculate round-trip efficiency

        η_round_trip = σ_E,chr × σ_E,dis

        Returns:
            Round-trip efficiency (fraction)
        """
        return self.specs['sigma_E_chr'] * self.specs['sigma_E_dis']

    def calculate_cycle_life_degradation(self, cycles_completed: int) -> Dict:
        """
        Calculate battery degradation based on cycle count

        Args:
            cycles_completed: Number of charge/discharge cycles completed

        Returns:
            Degradation details
        """
        cycle_life = self.specs['battery_spec']['cycle_life']
        capacity_fade = min(0.20, cycles_completed / cycle_life * 0.20)  # Max 20% capacity loss

        remaining_capacity_pct = (1 - capacity_fade) * 100

        return {
            'cycles_completed': cycles_completed,
            'cycle_life_rated': cycle_life,
            'cycles_remaining': max(0, cycle_life - cycles_completed),
            'capacity_fade_pct': capacity_fade * 100,
            'remaining_capacity_pct': remaining_capacity_pct,
            'end_of_life': cycles_completed >= cycle_life
        }
