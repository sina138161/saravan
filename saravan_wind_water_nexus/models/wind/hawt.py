"""
Horizontal Axis Wind Turbine (HAWT) Model
Conventional wind turbine with horizontal rotor axis
"""

import numpy as np
from typing import Dict
from ..base import TechnologyBase


class HAWT(TechnologyBase):
    """
    Horizontal Axis Wind Turbine (HAWT)

    Conventional wind turbine design with:
    - Horizontal rotor axis
    - Three-blade configuration
    - Yaw control system
    - Higher dust sensitivity
    """

    def _define_specs(self) -> Dict:
        """
        Define HAWT specifications

        Based on: IEC 61400 standards and manufacturer data
        """
        return {
            'name': 'Conventional_HAWT_500kW',
            'capacity': 500,  # kW
            'hub_height': 80,  # meters
            'rotor_diameter': 50,  # meters
            'land_requirement': 10000,  # m² per turbine (wake spacing included)
            'dust_sensitivity': 0.85,  # Performance multiplier under dust (85% = 15% loss)
            'capex': 1200,  # $/kW
            'opex': 40,  # $/kW/year
            'lifetime': 20,  # years
            'cut_in_speed': 3,  # m/s
            'rated_speed': 12,  # m/s
            'cut_out_speed': 25,  # m/s
            'power_coefficient': 0.45,  # Betz limit consideration
            'maintenance_factor_dust': 1.5,  # 50% more maintenance in dusty conditions
            'availability': 0.95  # 95% uptime
        }

    def calculate_power_output(self, wind_speed: float,
                               dust_concentration: float = 0) -> float:
        """
        Calculate power output for given conditions

        Args:
            wind_speed: Wind speed in m/s (v(t))
            dust_concentration: PM10 concentration in μg/m³

        Returns:
            Power output in kW (p_wt(t))
        """
        # Calculate base power using HAWT power curve with constraints
        power_base = self._hawt_power_curve(wind_speed)

        # Apply dust impact
        dust_reduction = self._dust_impact_model(wind_speed, dust_concentration)

        # Apply availability
        power_actual = power_base * dust_reduction * self.specs['availability']

        return power_actual

    def _hawt_power_curve(self, v: float) -> float:
        """
        HAWT power curve with exact cubic formula and constraints

        Formula (Eq. 19):
                 ⎧  0                                      if v < v_in  OR  v > v_out
        p_wt(t) =⎨  [(v³ - v_in³) / (v_r³ - v_in³)] × P_wt  if v_in ≤ v ≤ v_r
                 ⎩  P_wt                                   if v_r ≤ v < v_out

        Args:
            v: Real-time wind speed v(t) in m/s

        Returns:
            Power output p_wt(t) in kW
        """
        v_in = self.specs['cut_in_speed']      # v_in: cut-in wind speed
        v_r = self.specs['rated_speed']        # v_r: rated wind speed
        v_out = self.specs['cut_out_speed']    # v_out: cut-out wind speed
        P_wt = self.specs['capacity']          # P_wt: rated output power

        # Constraint 1: Outside operating range
        if v < v_in or v > v_out:
            return 0.0

        # Constraint 2: Between cut-in and rated (cubic region)
        elif v_in <= v <= v_r:
            # Exact cubic formula: [(v³ - v_in³) / (v_r³ - v_in³)] × P_wt
            power = P_wt * ((v**3 - v_in**3) / (v_r**3 - v_in**3))
            return power

        # Constraint 3: Between rated and cut-out (rated power)
        else:  # v_r <= v < v_out
            return P_wt

    def _dust_impact_model(self, wind_speed: float, dust_concentration: float) -> float:
        """
        Novel dust impact model for HAWT

        Models power reduction due to dust accumulation on blades

        Based on:
        - Khalfallah & Koliub (2007) - Dust effects on wind turbines
        - Field data from Middle Eastern wind farms
        - Saravan-specific measurements

        Args:
            wind_speed: Current wind speed (m/s)
            dust_concentration: PM10 concentration (μg/m³)

        Returns:
            Power reduction factor (0-1)
        """
        if dust_concentration == 0:
            return 1.0

        # Normalize dust concentration (typical Saravan: 50-300 μg/m³)
        dust_norm = dust_concentration / 100.0

        # HAWT parameters - High impact due to horizontal rotation
        alpha = 0.15
        beta = 1.2
        gamma = 10

        # Dust impact formula
        # reduction = 1 - α * (PM10/100)^β * exp(-v_wind/γ)
        reduction = 1 - alpha * (dust_norm ** beta) * np.exp(-wind_speed / gamma)

        return max(0.5, min(1.0, reduction))  # Limit between 50% and 100%

    def calculate_annual_energy(self, wind_speed_series: np.ndarray,
                                dust_series: np.ndarray = None) -> Dict:
        """
        Calculate annual energy production

        Args:
            wind_speed_series: Hourly wind speeds for full year (8760 values)
            dust_series: Hourly PM10 concentrations (optional)

        Returns:
            Dictionary with energy statistics
        """
        if dust_series is None:
            dust_series = np.zeros_like(wind_speed_series)

        hourly_power = np.array([
            self.calculate_power_output(v, d)
            for v, d in zip(wind_speed_series, dust_series)
        ])

        # Annual statistics
        annual_energy = np.sum(hourly_power)  # kWh
        capacity_factor = annual_energy / (self.specs['capacity'] * 8760)

        # Hours at different power levels
        hours_zero = np.sum(hourly_power == 0)
        hours_partial = np.sum((hourly_power > 0) & (hourly_power < self.specs['capacity']))
        hours_rated = np.sum(hourly_power == self.specs['capacity'])

        # Dust impact statistics
        dust_loss_hours = np.sum(dust_series > 100)  # Hours with significant dust
        avg_dust_reduction = np.mean([
            1 - self._dust_impact_model(v, d)
            for v, d in zip(wind_speed_series, dust_series)
        ])

        return {
            'annual_energy_kwh': annual_energy,
            'capacity_factor': capacity_factor,
            'hours_zero_power': hours_zero,
            'hours_partial_power': hours_partial,
            'hours_rated_power': hours_rated,
            'hours_significant_dust': dust_loss_hours,
            'avg_dust_loss_pct': avg_dust_reduction * 100,
            'max_hourly_power': np.max(hourly_power),
            'avg_hourly_power': np.mean(hourly_power)
        }

    def calculate_land_use(self, n_turbines: int, layout: str = 'grid') -> float:
        """
        Calculate total land area required for turbine array

        Args:
            n_turbines: Number of turbines
            layout: 'grid', 'linear', or 'optimized'

        Returns:
            Total land area in m²
        """
        base_area = self.specs['land_requirement']

        if layout == 'grid':
            # Standard grid layout with spacing
            total_area = base_area * n_turbines
        elif layout == 'linear':
            # Linear array (along prevailing wind)
            total_area = base_area * n_turbines * 0.7  # 30% savings
        else:  # optimized
            # Optimized layout for specific site
            total_area = base_area * n_turbines * 0.85  # 15% savings

        return total_area
