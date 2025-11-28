"""
Scenario Definitions for Saravan Wind-Water-Energy-Carbon Nexus Model

This module defines all comparative scenarios for analysis:
- S1: Baseline (Current)
- S2: High Renewable
- S3: Carbon Market
- S4: Dust Impact
- S5: Optimal Nexus

Each scenario represents a different configuration of the system
to analyze various aspects like technology mix, carbon markets,
environmental impacts, and integrated nexus optimization.
"""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ScenarioConfig:
    """
    Configuration for a single scenario

    This dataclass defines all parameters that can vary between scenarios,
    including technology mix, storage sizing, carbon market participation,
    environmental conditions, and economic parameters.
    """

    # ===== IDENTIFICATION =====
    id: str                                 # Scenario ID (S1, S2, etc.)
    name: str                               # Short name
    description: str                        # Detailed description

    # ===== TECHNOLOGY MIX =====
    wind_capacity_multiplier: float = 1.0  # Multiplier for wind capacity (1.0 = base)
    wind_hawt_count: int = 5               # Number of HAWT turbines
    wind_bladeless_count: int = 15         # Number of Bladeless turbines

    gas_turbine_enabled: bool = True       # Enable gas microturbine
    gas_turbine_capacity_kw: float = 200   # Gas turbine capacity

    biogas_enabled: bool = True            # Enable biogas system
    biogas_digester_m3: float = 1000       # Anaerobic digester volume

    grid_enabled: bool = True              # Enable grid connection
    grid_max_kw: float = 5000              # Maximum grid capacity

    # ===== ENERGY STORAGE =====
    battery_kwh: float = 1000              # Battery capacity (0 = disabled)
    battery_power_kw: float = 500          # Battery charge/discharge rate
    thermal_storage_kwh: float = 500       # Thermal storage capacity (0 = disabled)

    # ===== WATER SYSTEM =====
    water_tank_m3: float = 2500            # Water storage tank capacity
    smart_pumping: bool = True             # Enable smart pumping (off-peak)
    groundwater_well_depth_m: float = 100  # Well depth

    # ===== CARBON MARKET =====
    carbon_tier: Optional[str] = None      # None, 'VCC', 'CCC', 'PGC'
    carbon_water_bonus: bool = False       # Water access improvement bonus

    # ===== ENVIRONMENTAL CONDITIONS =====
    dust_severity: str = 'moderate'        # 'low', 'moderate', 'severe'
    dust_impact_factor: float = 0.85       # Efficiency reduction (1.0 = no impact, 0.5 = 50% reduction)
    dust_storm_frequency: float = 0.15     # Storms per day (0.15 = realistic for Saravan)

    # ===== ECONOMIC PARAMETERS =====
    elec_price_usd_kwh: float = 0.01       # Electricity price ($/kWh)
    gas_price_usd_kwh: float = 0.005       # Natural gas price ($/kWh)
    grid_import_cost: float = 0.01         # Cost to import from grid ($/kWh)
    grid_export_price: float = 0.008       # Price to export to grid ($/kWh)

    # ===== OPERATIONAL PARAMETERS =====
    optimization_objective: str = 'cost'   # 'cost', 'emissions', 'multi-objective'
    curtailment_allowed: bool = True       # Allow renewable curtailment
    load_shedding_allowed: bool = False    # Allow load shedding (emergency)

    def get_folder_name(self) -> str:
        """Generate folder name for results"""
        clean_name = self.name.lower().replace(' ', '_').replace('(', '').replace(')', '')
        return f"scenario_{self.id}_{clean_name}"

    def get_display_info(self) -> str:
        """Get formatted display information for this scenario"""
        info = f"""
{'='*70}
SCENARIO: {self.id} - {self.name}
{'='*70}
Description: {self.description}

Technology Mix:
  - Wind: {self.wind_hawt_count} HAWT + {self.wind_bladeless_count} Bladeless (×{self.wind_capacity_multiplier})
  - Gas Turbine: {'Enabled' if self.gas_turbine_enabled else 'Disabled'} ({self.gas_turbine_capacity_kw} kW)
  - Biogas: {'Enabled' if self.biogas_enabled else 'Disabled'} ({self.biogas_digester_m3} m³)
  - Grid: {'Enabled' if self.grid_enabled else 'Disabled'} (max {self.grid_max_kw} kW)

Storage:
  - Battery: {self.battery_kwh} kWh
  - Thermal: {self.thermal_storage_kwh} kWh
  - Water Tank: {self.water_tank_m3} m³

Carbon Market: {self.carbon_tier if self.carbon_tier else 'None'}
  - Water Bonus: {'Yes' if self.carbon_water_bonus else 'No'}

Environmental:
  - Dust Severity: {self.dust_severity}
  - Impact Factor: {self.dust_impact_factor:.2%}
  - Storm Frequency: {self.dust_storm_frequency:.2f}/day

Economics:
  - Electricity: ${self.elec_price_usd_kwh:.3f}/kWh
  - Gas: ${self.gas_price_usd_kwh:.3f}/kWh
  - Grid Import: ${self.grid_import_cost:.3f}/kWh

Operations:
  - Smart Pumping: {'Yes' if self.smart_pumping else 'No'}
  - Objective: {self.optimization_objective}
{'='*70}
        """
        return info


# =============================================================================
# SCENARIO DEFINITIONS
# =============================================================================

SCENARIOS: Dict[str, ScenarioConfig] = {

    # =========================================================================
    # S1: BASELINE (CURRENT SITUATION)
    # =========================================================================
    'S1': ScenarioConfig(
        id='S1',
        name='Baseline (Current)',
        description='Grid-dominant system with subsidized energy prices, moderate dust, minimal renewable penetration',

        # Low renewable penetration (only 20% of potential)
        wind_capacity_multiplier=0.2,
        wind_hawt_count=1,              # Only 1 HAWT
        wind_bladeless_count=3,         # Only 3 Bladeless

        # Conventional generation dominant
        gas_turbine_enabled=True,
        gas_turbine_capacity_kw=200,
        biogas_enabled=False,           # No biogas in baseline

        # Grid always available
        grid_enabled=True,
        grid_max_kw=5000,

        # No storage (current situation)
        battery_kwh=0,
        thermal_storage_kwh=0,

        # Basic water system
        water_tank_m3=1000,             # Smaller tank
        smart_pumping=False,            # No optimization

        # No carbon market participation
        carbon_tier=None,
        carbon_water_bonus=False,

        # Moderate dust (realistic)
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        # Heavily subsidized prices (current Iran)
        elec_price_usd_kwh=0.01,
        gas_price_usd_kwh=0.005,
        grid_import_cost=0.01,

        # Basic operation
        optimization_objective='cost',
        smart_pumping=False,
    ),

    # =========================================================================
    # S2: HIGH RENEWABLE
    # =========================================================================
    'S2': ScenarioConfig(
        id='S2',
        name='High Renewable',
        description='80% renewable penetration with energy storage and smart operation',

        # Full renewable capacity
        wind_capacity_multiplier=1.0,
        wind_hawt_count=5,
        wind_bladeless_count=15,

        # Minimal conventional generation
        gas_turbine_enabled=True,       # Keep for backup
        gas_turbine_capacity_kw=200,
        biogas_enabled=True,            # Add biogas
        biogas_digester_m3=1000,

        # Grid as backup only
        grid_enabled=True,
        grid_max_kw=5000,

        # Significant storage
        battery_kwh=2000,               # 2× baseline
        battery_power_kw=1000,
        thermal_storage_kwh=1000,       # 2× baseline

        # Optimized water system
        water_tank_m3=2500,
        smart_pumping=True,             # Pump during cheap hours

        # No carbon market yet
        carbon_tier=None,
        carbon_water_bonus=False,

        # Moderate dust
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        # Still subsidized (current prices)
        elec_price_usd_kwh=0.01,
        gas_price_usd_kwh=0.005,
        grid_import_cost=0.01,

        # Cost optimization
        optimization_objective='cost',
    ),

    # =========================================================================
    # S3: CARBON MARKET
    # =========================================================================
    'S3': ScenarioConfig(
        id='S3',
        name='Carbon Market',
        description='High renewable + Premium carbon pricing (PGC tier) + Partial subsidy removal',

        # Same as S2 for technology
        wind_capacity_multiplier=1.0,
        wind_hawt_count=5,
        wind_bladeless_count=15,

        gas_turbine_enabled=True,
        gas_turbine_capacity_kw=200,
        biogas_enabled=True,
        biogas_digester_m3=1000,

        grid_enabled=True,
        grid_max_kw=5000,

        battery_kwh=2000,
        battery_power_kw=1000,
        thermal_storage_kwh=1000,

        water_tank_m3=2500,
        smart_pumping=True,

        # PREMIUM CARBON MARKET
        carbon_tier='PGC',              # Premium Gold Certified
        carbon_water_bonus=True,        # Water access bonus

        # Moderate dust
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        # PARTIAL SUBSIDY REMOVAL (realistic future scenario)
        elec_price_usd_kwh=0.05,        # 5× current
        gas_price_usd_kwh=0.02,         # 4× current
        grid_import_cost=0.05,
        grid_export_price=0.04,         # Can sell to grid

        # Multi-objective (cost + emissions)
        optimization_objective='multi-objective',
    ),

    # =========================================================================
    # S4: DUST IMPACT
    # =========================================================================
    'S4': ScenarioConfig(
        id='S4',
        name='Dust Impact',
        description='High renewable under severe dust storm conditions (120 days/year)',

        # Same renewable capacity as S2
        wind_capacity_multiplier=1.0,
        wind_hawt_count=5,
        wind_bladeless_count=15,

        gas_turbine_enabled=True,
        gas_turbine_capacity_kw=200,
        biogas_enabled=True,
        biogas_digester_m3=1000,

        # Grid important for dust storms
        grid_enabled=True,
        grid_max_kw=5000,

        # Same storage as S2
        battery_kwh=2000,
        battery_power_kw=1000,
        thermal_storage_kwh=1000,

        water_tank_m3=2500,
        smart_pumping=True,

        # No carbon market
        carbon_tier=None,
        carbon_water_bonus=False,

        # SEVERE DUST CONDITIONS
        dust_severity='severe',
        dust_impact_factor=0.55,        # 45% efficiency reduction!
        dust_storm_frequency=0.33,      # 120 days/year

        # Current prices
        elec_price_usd_kwh=0.01,
        gas_price_usd_kwh=0.005,
        grid_import_cost=0.01,

        # Cost optimization
        optimization_objective='cost',
    ),

    # =========================================================================
    # S5: OPTIMAL NEXUS
    # =========================================================================
    'S5': ScenarioConfig(
        id='S5',
        name='Optimal Nexus',
        description='Fully integrated water-energy-carbon nexus with dust mitigation strategies',

        # Enhanced renewable (more bladeless for dust resistance)
        wind_capacity_multiplier=1.2,   # 20% more capacity
        wind_hawt_count=3,              # Fewer HAWT (affected by dust)
        wind_bladeless_count=20,        # More bladeless (dust resistant)

        gas_turbine_enabled=True,
        gas_turbine_capacity_kw=200,
        biogas_enabled=True,
        biogas_digester_m3=1500,        # Larger biogas

        # Grid as backup
        grid_enabled=True,
        grid_max_kw=5000,

        # MAXIMUM STORAGE
        battery_kwh=3000,               # 3× baseline
        battery_power_kw=1500,
        thermal_storage_kwh=1500,       # 3× baseline

        # OPTIMIZED WATER SYSTEM
        water_tank_m3=3000,             # Larger tank
        smart_pumping=True,
        groundwater_well_depth_m=100,

        # PREMIUM CARBON MARKET
        carbon_tier='PGC',
        carbon_water_bonus=True,

        # DUST MITIGATION IMPLEMENTED
        dust_severity='moderate',
        dust_impact_factor=0.90,        # Better than baseline (cleaning systems)
        dust_storm_frequency=0.15,

        # PARTIAL SUBSIDY REMOVAL
        elec_price_usd_kwh=0.05,
        gas_price_usd_kwh=0.02,
        grid_import_cost=0.05,
        grid_export_price=0.04,

        # MULTI-OBJECTIVE OPTIMIZATION
        optimization_objective='multi-objective',
        curtailment_allowed=True,
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_scenario(scenario_id: str) -> ScenarioConfig:
    """Get scenario configuration by ID"""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario ID: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]


def list_scenarios() -> None:
    """Print list of all available scenarios"""
    print("\n" + "="*70)
    print("AVAILABLE SCENARIOS")
    print("="*70 + "\n")

    for sid, scenario in SCENARIOS.items():
        print(f"  [{sid}] {scenario.name}")
        print(f"      {scenario.description}")
        print()


def compare_scenarios(scenario_ids: list) -> None:
    """Print comparison table of scenarios"""
    if not scenario_ids:
        scenario_ids = list(SCENARIOS.keys())

    print("\n" + "="*100)
    print("SCENARIO COMPARISON")
    print("="*100 + "\n")

    # Key parameters to compare
    params = [
        ('Wind Capacity', 'wind_capacity_multiplier'),
        ('Battery (kWh)', 'battery_kwh'),
        ('Thermal Storage (kWh)', 'thermal_storage_kwh'),
        ('Carbon Tier', 'carbon_tier'),
        ('Dust Severity', 'dust_severity'),
        ('Elec Price ($/kWh)', 'elec_price_usd_kwh'),
        ('Gas Price ($/kWh)', 'gas_price_usd_kwh'),
    ]

    # Header
    print(f"{'Parameter':<25} ", end='')
    for sid in scenario_ids:
        print(f"{sid:<15} ", end='')
    print()
    print("-" * 100)

    # Rows
    for param_name, param_key in params:
        print(f"{param_name:<25} ", end='')
        for sid in scenario_ids:
            scenario = SCENARIOS[sid]
            value = getattr(scenario, param_key)
            if value is None:
                value_str = 'None'
            elif isinstance(value, float):
                value_str = f"{value:.3f}"
            else:
                value_str = str(value)
            print(f"{value_str:<15} ", end='')
        print()

    print("="*100 + "\n")


if __name__ == "__main__":
    # Test scenario definitions
    list_scenarios()
    compare_scenarios(['S1', 'S2', 'S3', 'S4', 'S5'])

    # Print detailed info for S5
    print(SCENARIOS['S5'].get_display_info())
