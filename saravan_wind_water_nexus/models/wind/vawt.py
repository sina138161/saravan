"""
Vertical Axis Wind Turbine (VAWT) Model
Darrieus-type vertical axis wind turbine
"""

import numpy as np
from typing import Dict
from ..base import TechnologyBase


class VAWT(TechnologyBase):
    """
    Vertical Axis Wind Turbine (VAWT) - Darrieus Type

    Features:
    - Vertical rotor axis
    - Better dust performance than HAWT
    - Omnidirectional (no yaw control needed)
    - More linear power curve
    """

    def _define_specs(self) -> Dict:
        """
        Define VAWT specifications

        Based on: Darrieus turbine characteristics and field data
        """
        return {
            'name': 'Darrieus_VAWT_300kW',
            'capacity': 300,  # kW
            'height': 40,  # meters
            'rotor_diameter': 25,  # meters (equatorial diameter)
            'land_requirement': 5000,  # m² per turbine (less wake effect)
            'dust_sensitivity': 0.92,  # Better dust performance (8% loss)
            'capex': 1400,  # $/kW (higher initial cost)
            'opex': 35,  # $/kW/year (lower maintenance)
            'lifetime': 25,  # years
            'cut_in_speed': 2,  # m/s (better low-speed performance)
            'rated_speed': 15,  # m/s
            'cut_out_speed': 30,  # m/s
            'power_coefficient': 0.35,  # Lower than HAWT but more consistent
            'maintenance_factor_dust': 1.2,  # 20% more maintenance in dust
            'availability': 0.96  # 96% uptime (simpler mechanics)
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

        # Calculate base power using VAWT power curve
        power_base = self._vawt_power_curve(wind_speed, rho)

        # Apply dust impact
        dust_reduction = self._dust_impact_model(wind_speed, dust_concentration)

        # Apply availability
        power_actual = power_base * dust_reduction * self.specs['availability']

        return min(power_actual, self.specs['capacity'])

    def _vawt_power_curve(self, v: float, rho: float) -> float:
        """
        VAWT power curve - more linear than HAWT

        Reference: Darrieus turbine characteristics

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
            # More linear relationship (quadratic)
            power = P_rated * ((v - v_cut_in) / (v_rated - v_cut_in)) ** 2
        else:
            power = P_rated

        return power

    def _dust_impact_model(self, wind_speed: float, dust_concentration: float) -> float:
        """
        Dust impact model for VAWT

        VAWT has medium dust impact - vertical rotation helps dust shedding

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

        # VAWT parameters - Medium impact
        alpha = 0.08
        beta = 1.1
        gamma = 15

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
        hours_rated = np.sum(hourly_power == self.specs['capacity'])

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
            total_area = base_area * n_turbines * 0.85

        return total_area
