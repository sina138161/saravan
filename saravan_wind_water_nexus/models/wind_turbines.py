"""
Compatibility wrapper for wind turbine models
Provides backward compatibility for old imports
"""

from .wind import HAWT, Bladeless


class WindTurbineModels:
    """
    Wrapper class providing interface to wind turbine models

    Provides backward compatibility for network_builder_simple.py
    """

    def __init__(self):
        """Initialize turbine instances"""
        self.hawt = HAWT()
        self.bladeless = Bladeless()

    def calculate_power_output(self, turbine_type: str, wind_speed: float,
                              dust_pm10: float = 0, temperature: float = None) -> float:
        """
        Calculate power output for a single turbine

        Args:
            turbine_type: 'HAWT' or 'Bladeless'
            wind_speed: Wind speed (m/s)
            dust_pm10: Dust concentration (µg/m³)
            temperature: Temperature (°C) - ignored, kept for compatibility

        Returns:
            Power output (kW)
        """
        if turbine_type == 'HAWT':
            # HAWT returns scalar value directly
            return self.hawt.calculate_power_output(wind_speed, dust_pm10)
        elif turbine_type == 'Bladeless':
            # Bladeless also returns scalar value
            return self.bladeless.calculate_power_output(wind_speed)
        else:
            raise ValueError(f"Unknown turbine type: {turbine_type}")

    def get_turbine_specs(self, turbine_type: str) -> dict:
        """
        Get turbine specifications

        Args:
            turbine_type: 'HAWT' or 'Bladeless'

        Returns:
            Specifications dictionary
        """
        if turbine_type == 'HAWT':
            specs = self.hawt.specs
            return {
                'capacity': specs['capacity'],
                'capex': specs['capex']
            }
        elif turbine_type == 'Bladeless':
            specs = self.bladeless.specs
            return {
                'capacity': specs['capacity'],
                'capex': specs['capex']
            }
        else:
            raise ValueError(f"Unknown turbine type: {turbine_type}")
