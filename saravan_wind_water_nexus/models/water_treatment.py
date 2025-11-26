"""
Compatibility wrapper for water system models
Provides backward compatibility for old imports
"""

from typing import Dict


class WaterSystemModel:
    """
    Wrapper class providing interface to water treatment systems

    Provides backward compatibility for network_builder_simple.py
    """

    def __init__(self):
        """Initialize water system specifications"""
        self.quality_system = self._define_quality_system()

    def _define_quality_system(self) -> Dict:
        """
        Define water quality treatment system specifications

        Returns:
            Dictionary with treatment system specs
        """
        return {
            'groundwater_well': {
                'extraction_limit_m3_per_hour': 500,  # Maximum well capacity
                'depth_m': 100,  # Well depth
                'pumping_energy_kwh_per_m3': 1.2,  # Energy for pumping
                'water_quality': 'raw'
            },

            'primary_treatment': {
                'purpose': 'Groundwater → Agricultural quality',
                'process': 'Filtration + Chlorination',
                'energy_kwh_per_m3': 0.15,  # Energy for treatment
                'removal_efficiency': 0.85,  # 85% contaminant removal
                'output_quality': 'agricultural'
            },

            'secondary_treatment': {
                'purpose': 'Agricultural → Potable quality',
                'process': 'Advanced filtration + UV + RO',
                'energy_kwh_per_m3': 0.50,  # Higher energy for advanced treatment
                'removal_efficiency': 0.95,  # 95% contaminant removal
                'output_quality': 'potable'
            },

            'wastewater_primary_treatment': {
                'purpose': 'Wastewater → Agricultural reuse',
                'process': 'Screening + Settling + Filtration',
                'energy_kwh_per_m3': 0.25,
                'recovery_rate': 0.85,  # 85% water recovery
                'sludge_production_kg_per_m3': 0.075,  # 75 g sludge per m³
                'output_quality': 'agricultural'
            },

            'wastewater_secondary_treatment': {
                'purpose': 'Wastewater → Potable reuse',
                'process': 'Biological + Advanced filtration + UV + RO',
                'energy_kwh_per_m3': 0.60,
                'recovery_rate': 0.75,  # 75% water recovery (lower due to stricter treatment)
                'sludge_production_kg_per_m3': 0.090,  # 90 g sludge per m³
                'output_quality': 'potable'
            }
        }
