"""
Data Management for Saravan Wind-Water-Energy-Carbon Nexus

This package contains:
- data_generator.py: Generate time series profiles
- input/: Excel files with generated profiles and parameters

Profiles generated:
- Wind speed (m/s)
- Dust PM10 (μg/m³)
- Temperature (°C)
- Water demand - Agricultural & Urban (m³/h) - NO INDUSTRIAL
- Electricity demand (kWh) - NO INDUSTRIAL
- Heat demand (kWh-thermal)
- Biomass availability (ton/h)
- Gas network availability (MW)
- Groundwater availability (m³/h)

Parameters exported to Excel:
- parameters_economic.xlsx
- parameters_technical.xlsx
- parameters_environmental.xlsx
"""

from .data_generator import SaravanDataGenerator
from .data_loader import DataLoader, load_dataset_from_excel, load_parameters_from_excel

__all__ = [
    'SaravanDataGenerator',
    'DataLoader',
    'load_dataset_from_excel',
    'load_parameters_from_excel'
]
