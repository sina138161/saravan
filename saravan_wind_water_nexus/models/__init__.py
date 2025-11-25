"""
Technology models for Saravan Wind-Water Nexus

Organized by technology type:
- base: Base classes for all technologies
- wind: Wind turbine models (HAWT, VAWT, Bladeless)
- thermal: Thermal systems (CHP, Gas Boiler)
- biogas: Biogas and sludge management (Composting, Digester, CCU)
- water: Water systems (Wells, Treatment, Storage)
- carbon_market: Carbon market revenue model
"""

# Base classes
from .base import TechnologyBase, EconomicCalculator

# Wind turbines
from .wind import HAWT, VAWT, Bladeless

# Thermal systems
from .thermal import CHP, GasBoiler

# Biogas and sludge management
from .biogas import Composting, AnaerobicDigester, CCU

# Water systems
from .water import GroundwaterWell, WaterTreatment, WastewaterTreatment, ElevatedStorage

# Carbon market
from .carbon_market import CarbonMarket, CarbonMarketTier

__all__ = [
    # Base
    'TechnologyBase',
    'EconomicCalculator',

    # Wind
    'HAWT',
    'VAWT',
    'Bladeless',

    # Thermal
    'CHP',
    'GasBoiler',

    # Biogas
    'Composting',
    'AnaerobicDigester',
    'CCU',

    # Water
    'GroundwaterWell',
    'WaterTreatment',
    'WastewaterTreatment',
    'ElevatedStorage',

    # Carbon
    'CarbonMarket',
    'CarbonMarketTier',
]
