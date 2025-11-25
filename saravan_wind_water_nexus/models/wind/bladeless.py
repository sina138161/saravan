"""
Bladeless Wind Turbine Model
Vortex-induced vibration wind turbine (no rotating blades)
"""

import numpy as np
from typing import Dict
from ..base import TechnologyBase


class Bladeless(TechnologyBase):
    """
    Bladeless Wind Turbine - Vortex Bladeless Technology

    Features:
    - No rotating blades (vortex-induced vibration)
    - Excellent dust resistance
    - Minimal maintenance
    - Lower power coefficient but more consistent
    - Very quiet operation
    """

    def _define_specs(self) -> Dict:
        """
        Define Bladeless turbine specifications

        Based on: Vortex Bladeless technology white papers
        """
        return {
            'name': 'Vortex_Bladeless_100kW',
            'capacity': 100,  # kW (modular, deploy multiple units)
            'height': 15,  # meters
            'base_diameter': 3,  # meters
            'land_requirement': 500,  # m² per turbine (minimal spacing needed)
            'dust_sensitivity': 0.98,  # Excellent dust resistance (only 2% loss)
            'capex': 1800,  # $/kW (higher initial cost, novel technology)
            'opex': 20,  # $/kW/year (minimal maintenance - no moving parts)
            'lifetime': 30,  # years (no blade wear)
            'cut_in_speed': 1.5,  # m/s (excellent low-speed performance)
            'rated_speed': 10,  # m/s
            'cut_out_speed': 40,  # m/s (can handle extreme winds)
            'power_coefficient': 0.30,  # Lower but consistent
            'oscillation_frequency_range': (2, 20),  # Hz
            'maintenance_factor_dust': 1.05,  # Only 5% more maintenance in dust
            'availability': 0.98,  # 98% uptime (very reliable)
            'noise_level': 20  # dB (virtually silent)
        }

    def calculate_power_output(self, wind_speed: float,
                               dust_concentration: float = 0,
                               temperature: float = 25) -> float:
        """
        Calculate power output for given conditions

        Args:
            wind_speed: Wind speed in m/s
            dust_concentration: PM10 concentration in μg/m³
            temperature: Air temperature in °C

        Returns:
            Power output in kW
        """
        # Check cut-in and cut-out speeds
        if wind_speed < self.specs['cut_in_speed'] or wind_speed > self.specs['cut_out_speed']:
            return 0.0

        # Air density correction for temperature
        rho = 1.225 * (288.15 / (temperature + 273.15))  # kg/m³

        # Calculate base power using Bladeless power curve
        power_base = self._bladeless_power_curve(wind_speed, rho)

        # Apply dust impact (minimal for bladeless)
        dust_reduction = self._dust_impact_model(wind_speed, dust_concentration)

        # Apply availability
        power_actual = power_base * dust_reduction * self.specs['availability']

        return min(power_actual, self.specs['capacity'])

    def _bladeless_power_curve(self, v: float, rho: float) -> float:
        """
        Bladeless turbine power curve - based on vortex-induced vibration

        Reference: Vortex Bladeless technology white papers
        Power ∝ v² (not v³ due to different energy extraction mechanism)

        Args:
            v: Wind speed (m/s)
            rho: Air density (kg/m³)

        Returns:
            Power output (kW)
        """
        v_cut_in = self.specs['cut_in_speed']
        v_rated = self.specs['rated_speed']
        P_rated = self.specs['capacity']

        if v <= v_cut_in:
            return 0
        elif v < v_rated:
            # Quadratic relationship (vortex shedding)
            power = P_rated * ((v - v_cut_in) / (v_rated - v_cut_in)) ** 2
        else:
            # Slight increase beyond rated (can handle higher winds)
            power = P_rated * min(1.1, (v / v_rated) ** 0.5)

        return power

    def _dust_impact_model(self, wind_speed: float, dust_concentration: float) -> float:
        """
        Dust impact model for Bladeless turbine

        Minimal impact - no rotating blades to accumulate dust
        Only slight aerodynamic effect on cylinder

        Args:
            wind_speed: Current wind speed (m/s)
            dust_concentration: PM10 concentration (μg/m³)

        Returns:
            Power reduction factor (0-1)
        """
        if dust_concentration == 0:
            return 1.0

        # Normalize dust concentration
        dust_norm = dust_concentration / 100.0

        # Bladeless parameters - Minimal impact
        alpha = 0.02
        beta = 1.0
        gamma = 20  # Self-cleaning at higher speeds

        # Dust impact formula
        reduction = 1 - alpha * (dust_norm ** beta) * np.exp(-wind_speed / gamma)

        return max(0.5, min(1.0, reduction))

    def calculate_annual_energy(self, wind_speed_series: np.ndarray,
                                dust_series: np.ndarray = None,
                                temperature_series: np.ndarray = None) -> Dict:
        """
        Calculate annual energy production

        Args:
            wind_speed_series: Hourly wind speeds for full year (8760 values)
            dust_series: Hourly PM10 concentrations (optional)
            temperature_series: Hourly temperatures (optional)

        Returns:
            Dictionary with energy statistics
        """
        if dust_series is None:
            dust_series = np.zeros_like(wind_speed_series)
        if temperature_series is None:
            temperature_series = np.ones_like(wind_speed_series) * 25

        hourly_power = np.array([
            self.calculate_power_output(v, d, t)
            for v, d, t in zip(wind_speed_series, dust_series, temperature_series)
        ])

        # Annual statistics
        annual_energy = np.sum(hourly_power)  # kWh
        capacity_factor = annual_energy / (self.specs['capacity'] * 8760)

        # Hours at different power levels
        hours_zero = np.sum(hourly_power == 0)
        hours_partial = np.sum((hourly_power > 0) & (hourly_power < self.specs['capacity']))
        hours_rated = np.sum(hourly_power >= self.specs['capacity'])

        # Dust impact statistics
        dust_loss_hours = np.sum(dust_series > 100)
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

        Bladeless turbines require minimal spacing due to no wake effect

        Args:
            n_turbines: Number of turbines
            layout: 'grid', 'linear', or 'optimized'

        Returns:
            Total land area in m²
        """
        base_area = self.specs['land_requirement']

        if layout == 'grid':
            total_area = base_area * n_turbines
        elif layout == 'linear':
            total_area = base_area * n_turbines * 0.7
        else:  # optimized
            # Can be packed more densely due to no wake effect
            total_area = base_area * n_turbines * 0.6

        return total_area
