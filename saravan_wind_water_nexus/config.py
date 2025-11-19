"""
Configuration file for Saravan Wind-Water-Energy-Carbon Nexus Model

All model parameters and settings are defined here for easy modification
and review. This makes it transparent what assumptions are being used.
"""

from pathlib import Path

class Config:
    """
    Configuration for Saravan Nexus Model

    This class contains all the parameters that define the model setup.
    You can modify these values to run different scenarios.
    """

    # ============================================================================
    # GENERAL SETTINGS
    # ============================================================================

    # Simulation period
    SNAPSHOTS_START = "2025-01-01"
    SNAPSHOTS_END = "2025-01-08"  # 7 days = 168 hours
    SNAPSHOTS_FREQ = "H"  # Hourly

    # Random seed for reproducibility
    RANDOM_SEED = 42

    # ============================================================================
    # RENEWABLE ENERGY (Wind Turbines)
    # ============================================================================

    # Turbine mix: number of each type
    # Note: VAWT removed based on system requirements
    TURBINE_MIX = {
        'HAWT': 5,          # Horizontal Axis Wind Turbines
        'Bladeless': 15,    # Bladeless wind turbines
    }

    # ============================================================================
    # ENERGY STORAGE (Battery)
    # ============================================================================

    BATTERY_CAPACITY_KWH = 1000     # Battery energy capacity (kWh)
    BATTERY_POWER_KW = 500          # Battery power rating (kW)
    BATTERY_EFFICIENCY = 0.92       # Round-trip efficiency (92%)
    BATTERY_SELF_DISCHARGE = 0.01   # Self-discharge per hour (1%)

    # ============================================================================
    # WATER SYSTEM
    # ============================================================================

    # Water tank
    WATER_TANK_CAPACITY_M3 = 2500   # Water storage capacity (m³)
    WATER_TANK_ELEVATION_M = 25     # Tank elevation (meters)

    # Groundwater pumping
    GROUNDWATER_MAX_EXTRACTION = 100  # Max pumping rate (m³/h)
    PUMPING_POWER_PER_M3 = 1.2       # Energy for pumping (kWh/m³)

    # Treatment efficiencies
    PRIMARY_GW_RECOVERY = 0.95       # Primary groundwater treatment (95%)
    SECONDARY_GW_RECOVERY = 0.90     # Secondary groundwater treatment (90%)
    PRIMARY_WW_RECOVERY = 0.85       # Primary wastewater treatment (85%)
    SECONDARY_WW_RECOVERY = 0.75     # Secondary wastewater treatment (75%)

    # ============================================================================
    # THERMAL SYSTEMS
    # ============================================================================

    # CHP (Combined Heat & Power)
    CHP_ELECTRICAL_EFFICIENCY = 0.35    # 35% to electricity
    CHP_THERMAL_EFFICIENCY = 0.45       # 45% to heat
    CHP_TOTAL_EFFICIENCY = 0.80         # 80% total
    CHP_CAPACITY_KW = 500               # Rated capacity

    # Gas Boiler
    BOILER_THERMAL_EFFICIENCY = 0.85    # 85% thermal efficiency
    BOILER_CAPACITY_KW = 300            # Rated capacity

    # ============================================================================
    # CARBON & BIOMASS
    # ============================================================================

    # Sludge management
    SLUDGE_PRODUCTION_KG_PER_M3 = 0.075  # Sludge from wastewater (kg/m³)
    COMPOSTING_RATIO = 0.50              # Output/input ratio
    DIGESTER_BIOGAS_YIELD = 0.4          # m³ biogas per kg sludge

    # Carbon Capture & Utilization (CCU)
    CCU_CAPTURE_EFFICIENCY = 0.90        # 90% capture rate
    CCU_ENERGY_PER_KG_CO2 = 0.30        # kWh per kg CO2 captured

    # Carbon market prices ($/ton CO2)
    CARBON_PRICE_VCC = 15    # Verified Carbon Credit
    CARBON_PRICE_CCC = 35    # Certified Carbon Credit
    CARBON_PRICE_PGC = 50    # Premium Green Credit

    # ============================================================================
    # GRID CONNECTION
    # ============================================================================

    # Power network (gas-fired electricity from grid)
    GRID_CAPACITY_KW = 5000              # Grid connection capacity
    GRID_GAS_TO_ELEC_EFFICIENCY = 0.45   # 45% efficiency (CCGT)
    GRID_MARGINAL_COST = 80              # $/MWh markup

    # Natural gas price
    NATURAL_GAS_PRICE = 40               # $/MWh-thermal

    # ============================================================================
    # SOLVER SETTINGS
    # ============================================================================

    SOLVER = 'highs'                     # Solver: 'highs' or 'glpk' or 'gurobi'
    SOLVER_OPTIONS = {
        'time_limit': 300,               # Maximum solve time (seconds)
        'mip_rel_gap': 0.01,            # 1% optimality gap
    }

    # ============================================================================
    # OUTPUT SETTINGS
    # ============================================================================

    # Output directories
    PROJECT_DIR = Path(__file__).parent
    OUTPUT_DIR = PROJECT_DIR / 'results'
    RESOURCES_DIR = PROJECT_DIR / 'resources'
    DATA_DIR = PROJECT_DIR / 'data'

    # Visualization settings
    PLOT_DPI = 300                       # Figure resolution (DPI)
    CREATE_STANDARD_PLOTS = True         # Create nexus + carbon plots
    CREATE_PUBLICATION_FIGURES = True    # Create 10 publication figures

    # Export settings
    EXPORT_NETWORK_NC = True             # Export PyPSA network to NetCDF
    EXPORT_RESULTS_CSV = True            # Export results to CSV
    EXPORT_SUMMARY_JSON = True           # Export summary to JSON

    # ============================================================================
    # VALIDATION & CHECKS
    # ============================================================================

    def validate(self):
        """
        Validate configuration parameters

        Returns:
            bool: True if valid, raises ValueError otherwise
        """
        # Check positive values
        assert self.BATTERY_CAPACITY_KWH > 0, "Battery capacity must be positive"
        assert self.WATER_TANK_CAPACITY_M3 > 0, "Water tank capacity must be positive"
        assert self.CHP_TOTAL_EFFICIENCY <= 1.0, "CHP efficiency cannot exceed 100%"
        assert self.BOILER_THERMAL_EFFICIENCY <= 1.0, "Boiler efficiency cannot exceed 100%"

        # Check turbine mix
        assert len(self.TURBINE_MIX) > 0, "At least one turbine type required"
        assert all(n >= 0 for n in self.TURBINE_MIX.values()), "Turbine counts must be non-negative"

        return True

    def __repr__(self):
        """String representation of configuration"""
        return f"Config(turbines={self.TURBINE_MIX}, battery={self.BATTERY_CAPACITY_KWH}kWh)"


# Create global config instance
config = Config()

# Validate on import
config.validate()

print(f"✅ Configuration loaded: {config}")
