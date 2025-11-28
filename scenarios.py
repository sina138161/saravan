"""
Scenario Definitions for Saravan Wind-Water-Energy-Carbon Nexus Model

Policy-Driven Scenarios for Iran's Energy System Analysis:
- S1: Baseline (Business as Usual)
- S2: Winter Gas Shortage
- S3: Winter Gas Shortage + Air Pollution Penalty
- S4: Carbon Pricing Policy
- S5: Climate Change (Extreme Dust)
- S6: Technology Cost Reduction (Future 2030)
- S7: Summer Electricity & Water Crisis

Each scenario modifies constraints, prices, and availability to reflect
real-world policy and environmental conditions. The optimizer then decides
the optimal technology mix and operation strategy.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class ScenarioConfig:
    """
    Policy-driven scenario configuration

    This dataclass defines constraints, prices, and availability factors.
    The optimizer decides technology deployment and operation based on these constraints.

    Key principle: Scenarios modify CONDITIONS, not DECISIONS.
    The model decides how much of each technology to use.
    """

    # ===== IDENTIFICATION =====
    id: str                                 # Scenario ID (S1, S2, etc.)
    name: str                               # Short name
    description: str                        # Detailed description

    # ===== SEASONAL RESOURCE AVAILABILITY =====
    # Seasonal availability factors (0.0 = unavailable, 1.0 = fully available)
    gas_seasonal_availability: Dict[str, float] = field(default_factory=lambda: {
        'spring': 1.0,  # Mar-May
        'summer': 1.0,  # Jun-Aug
        'fall': 1.0,    # Sep-Nov
        'winter': 1.0   # Dec-Feb
    })

    grid_seasonal_availability: Dict[str, float] = field(default_factory=lambda: {
        'spring': 1.0,
        'summer': 1.0,
        'fall': 1.0,
        'winter': 1.0
    })

    # Grid blackout hours (specific hours when grid is unavailable)
    grid_blackout_hours: list = field(default_factory=list)  # e.g., [14, 15, 16, 17] for afternoon blackouts

    # Water availability factor (0.7 = 30% reduction due to drought)
    water_availability_factor: float = 1.0

    # ===== DEMAND MODIFIERS =====
    # Multipliers for seasonal demand changes
    water_demand_multiplier: float = 1.0    # 1.4 = 40% increase in summer
    heat_demand_multiplier: float = 1.0     # 1.3 = 30% increase in winter
    elec_demand_multiplier: float = 1.0     # 1.2 = 20% increase in summer (cooling)

    # ===== ECONOMIC PARAMETERS =====
    # Energy prices
    elec_price_usd_kwh: float = 0.01        # Electricity price ($/kWh)
    gas_price_usd_kwh: float = 0.005        # Natural gas price ($/kWh)
    gas_price_multiplier: float = 1.0       # Multiplier for gas price (5.0 = crisis)
    grid_import_cost: float = 0.01          # Cost to import from grid ($/kWh)
    grid_export_price: float = 0.008        # Revenue from exporting to grid ($/kWh)

    # ===== CARBON MARKET & EMISSIONS =====
    carbon_tier: Optional[str] = None       # None, 'VCC', 'CCC', 'PGC'
    carbon_water_bonus: bool = False        # Water access improvement bonus
    carbon_tax_usd_per_ton: float = 0.0     # Carbon tax ($/ton CO2)
    carbon_credit_usd_per_ton: float = 0.0  # Carbon credit for avoided emissions ($/ton CO2)

    # Mazut emission penalty (when gas unavailable, plants burn mazut - dirty fuel)
    mazut_emission_penalty: float = 0.0     # Extra $/ton for high-emission fuels

    # ===== TECHNOLOGY COSTS (CAPEX) =====
    battery_capex_usd_per_kwh: float = 500  # Battery capital cost ($/kWh) - realistic 2025
    wind_capex_multiplier: float = 1.0      # Wind turbine cost multiplier (0.7 = 30% cheaper)
    solar_capex_multiplier: float = 1.0     # Future expansion

    # ===== ENVIRONMENTAL CONDITIONS =====
    dust_severity: str = 'moderate'         # 'low', 'moderate', 'severe'
    dust_impact_factor: float = 0.85        # Wind efficiency during dust (1.0 = no impact, 0.5 = 50% reduction)
    dust_storm_frequency: float = 0.15      # Storms per day (0.33 = 120 days/year)

    # ===== OPERATIONAL CONSTRAINTS =====
    optimization_objective: str = 'cost'    # 'cost', 'emissions', 'multi-objective'
    curtailment_allowed: bool = True        # Allow renewable curtailment
    load_shedding_allowed: bool = False     # Allow load shedding (emergency only)

    # Technology enable/disable (only for complete removal)
    gas_turbine_enabled: bool = True        # Set False to completely disable gas turbine
    biogas_enabled: bool = True             # Set False to completely disable biogas
    grid_enabled: bool = True               # Set False for islanded operation

    def get_folder_name(self) -> str:
        """Generate folder name for results"""
        clean_name = self.name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'and')
        return f"scenario_{self.id}_{clean_name}"

    def get_display_info(self) -> str:
        """Get formatted display information for this scenario"""
        info = f"""
{'='*80}
SCENARIO: {self.id} - {self.name}
{'='*80}
Description: {self.description}

🔧 RESOURCE AVAILABILITY:
  Gas Availability (Seasonal):
    Spring: {self.gas_seasonal_availability['spring']:.0%}  |  Summer: {self.gas_seasonal_availability['summer']:.0%}
    Fall:   {self.gas_seasonal_availability['fall']:.0%}  |  Winter: {self.gas_seasonal_availability['winter']:.0%}

  Grid Availability (Seasonal):
    Spring: {self.grid_seasonal_availability['spring']:.0%}  |  Summer: {self.grid_seasonal_availability['summer']:.0%}
    Fall:   {self.grid_seasonal_availability['fall']:.0%}  |  Winter: {self.grid_seasonal_availability['winter']:.0%}

  Grid Blackout Hours: {self.grid_blackout_hours if self.grid_blackout_hours else 'None'}
  Water Availability: {self.water_availability_factor:.0%}

📊 DEMAND MODIFIERS:
  Water Demand: ×{self.water_demand_multiplier:.2f}
  Heat Demand:  ×{self.heat_demand_multiplier:.2f}
  Elec Demand:  ×{self.elec_demand_multiplier:.2f}

💰 ECONOMICS:
  Electricity: ${self.elec_price_usd_kwh:.3f}/kWh
  Gas: ${self.gas_price_usd_kwh * self.gas_price_multiplier:.3f}/kWh (base: ${self.gas_price_usd_kwh:.3f} × {self.gas_price_multiplier:.1f})
  Grid Import: ${self.grid_import_cost:.3f}/kWh  |  Grid Export: ${self.grid_export_price:.3f}/kWh

🌍 CARBON & EMISSIONS:
  Carbon Tax: ${self.carbon_tax_usd_per_ton:.0f}/ton CO2
  Carbon Credit: ${self.carbon_credit_usd_per_ton:.0f}/ton CO2 avoided
  Mazut Penalty: ${self.mazut_emission_penalty:.0f}/ton (dirty fuel)
  Carbon Market Tier: {self.carbon_tier if self.carbon_tier else 'None'}

🏭 TECHNOLOGY COSTS:
  Battery CAPEX: ${self.battery_capex_usd_per_kwh:.0f}/kWh
  Wind Cost Multiplier: ×{self.wind_capex_multiplier:.2f}

🌪️  ENVIRONMENTAL:
  Dust Severity: {self.dust_severity}
  Wind Efficiency Loss: {(1-self.dust_impact_factor)*100:.0f}%
  Storm Frequency: {self.dust_storm_frequency:.2f}/day (~{self.dust_storm_frequency*365:.0f} days/year)

⚙️  OPERATIONS:
  Optimization: {self.optimization_objective}
  Technologies: Gas={self.gas_turbine_enabled}, Biogas={self.biogas_enabled}, Grid={self.grid_enabled}
{'='*80}
        """
        return info


# =============================================================================
# SCENARIO DEFINITIONS
# =============================================================================

SCENARIOS: Dict[str, ScenarioConfig] = {

    # =========================================================================
    # S1: BASELINE (BUSINESS AS USUAL)
    # =========================================================================
    'S1': ScenarioConfig(
        id='S1',
        name='Baseline (Business as Usual)',
        description='Current conditions in Iran: Subsidized energy, full gas access, no carbon pricing',

        # Full resource availability (no constraints)
        gas_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        grid_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        water_availability_factor=1.0,

        # Normal demand
        water_demand_multiplier=1.0,
        heat_demand_multiplier=1.0,
        elec_demand_multiplier=1.0,

        # Heavily subsidized prices (current Iran)
        elec_price_usd_kwh=0.01,
        gas_price_usd_kwh=0.005,
        gas_price_multiplier=1.0,
        grid_import_cost=0.01,
        grid_export_price=0.0,  # No feed-in tariff

        # No carbon pricing
        carbon_tax_usd_per_ton=0.0,
        carbon_credit_usd_per_ton=0.0,
        mazut_emission_penalty=0.0,
        carbon_tier=None,

        # Current technology costs
        battery_capex_usd_per_kwh=500,
        wind_capex_multiplier=1.0,

        # Moderate dust (typical Saravan)
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        # Cost optimization
        optimization_objective='cost',
        gas_turbine_enabled=True,
        biogas_enabled=True,
        grid_enabled=True,
    ),

    # =========================================================================
    # S2: WINTER GAS SHORTAGE
    # =========================================================================
    'S2': ScenarioConfig(
        id='S2',
        name='Winter Gas Shortage',
        description='Severe gas shortage in fall and winter (Iran\'s gas imbalance crisis)',

        # SEVERE gas shortage in cold months
        gas_seasonal_availability={
            'spring': 0.9,   # 90% available
            'summer': 1.0,   # 100% (summer has excess gas)
            'fall': 0.6,     # 60% (shortage starts)
            'winter': 0.3    # 30% (severe shortage in cold winter)
        },
        grid_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        water_availability_factor=1.0,

        # Increased heating demand in winter
        heat_demand_multiplier=1.3,  # 30% more heating demand
        water_demand_multiplier=1.0,
        elec_demand_multiplier=1.0,

        # Higher gas prices due to shortage
        elec_price_usd_kwh=0.01,
        gas_price_usd_kwh=0.005,
        gas_price_multiplier=3.0,    # 3× gas price in winter
        grid_import_cost=0.015,      # Grid also more expensive
        grid_export_price=0.0,

        # No carbon pricing yet
        carbon_tax_usd_per_ton=0.0,
        carbon_credit_usd_per_ton=0.0,
        mazut_emission_penalty=0.0,

        # Same costs as baseline
        battery_capex_usd_per_kwh=500,
        wind_capex_multiplier=1.0,

        # Moderate dust
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        optimization_objective='cost',
        gas_turbine_enabled=True,
        biogas_enabled=True,
        grid_enabled=True,
    ),

    # =========================================================================
    # S3: WINTER GAS SHORTAGE + AIR POLLUTION PENALTY
    # =========================================================================
    'S3': ScenarioConfig(
        id='S3',
        name='Winter Gas + Air Pollution',
        description='Gas shortage forces mazut burning, leading to severe air pollution penalties',

        # Same gas shortage as S2
        gas_seasonal_availability={
            'spring': 0.9,
            'summer': 1.0,
            'fall': 0.6,
            'winter': 0.3
        },
        grid_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        water_availability_factor=1.0,

        # Same demand as S2
        heat_demand_multiplier=1.3,
        water_demand_multiplier=1.0,
        elec_demand_multiplier=1.0,

        # Same prices as S2
        elec_price_usd_kwh=0.01,
        gas_price_usd_kwh=0.005,
        gas_price_multiplier=3.0,
        grid_import_cost=0.015,
        grid_export_price=0.0,

        # HEAVY carbon penalties (air pollution crisis)
        carbon_tax_usd_per_ton=100.0,         # $100/ton CO2
        mazut_emission_penalty=150.0,         # $150/ton for dirty mazut
        carbon_credit_usd_per_ton=0.0,
        carbon_tier=None,

        # Same costs
        battery_capex_usd_per_kwh=500,
        wind_capex_multiplier=1.0,

        # Moderate dust
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        optimization_objective='cost',  # Cost includes penalties
        gas_turbine_enabled=True,
        biogas_enabled=True,
        grid_enabled=True,
    ),

    # =========================================================================
    # S4: CARBON PRICING POLICY
    # =========================================================================
    'S4': ScenarioConfig(
        id='S4',
        name='Carbon Pricing Policy',
        description='Carbon tax + subsidy removal + renewable incentives',

        # Full resource availability
        gas_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        grid_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        water_availability_factor=1.0,

        # Normal demand
        water_demand_multiplier=1.0,
        heat_demand_multiplier=1.0,
        elec_demand_multiplier=1.0,

        # SUBSIDY REMOVAL (real market prices)
        elec_price_usd_kwh=0.08,      # 8× higher
        gas_price_usd_kwh=0.04,       # 8× higher
        gas_price_multiplier=1.0,
        grid_import_cost=0.08,
        grid_export_price=0.06,       # Feed-in tariff enabled

        # Carbon pricing
        carbon_tax_usd_per_ton=50.0,         # Moderate carbon tax
        carbon_credit_usd_per_ton=50.0,      # Incentive for renewables
        mazut_emission_penalty=0.0,
        carbon_tier='CCC',                   # Compliance market

        # Same costs
        battery_capex_usd_per_kwh=500,
        wind_capex_multiplier=1.0,

        # Moderate dust
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        optimization_objective='multi-objective',  # Balance cost and emissions
        gas_turbine_enabled=True,
        biogas_enabled=True,
        grid_enabled=True,
    ),

    # =========================================================================
    # S5: CLIMATE CHANGE (EXTREME DUST)
    # =========================================================================
    'S5': ScenarioConfig(
        id='S5',
        name='Climate Change (Extreme Dust)',
        description='Climate change causes severe dust storms affecting wind turbines',

        # Full resource availability
        gas_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        grid_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        water_availability_factor=1.0,

        # Normal demand
        water_demand_multiplier=1.0,
        heat_demand_multiplier=1.0,
        elec_demand_multiplier=1.0,

        # Current prices
        elec_price_usd_kwh=0.01,
        gas_price_usd_kwh=0.005,
        gas_price_multiplier=1.0,
        grid_import_cost=0.01,
        grid_export_price=0.0,

        # No carbon pricing
        carbon_tax_usd_per_ton=0.0,
        carbon_credit_usd_per_ton=0.0,
        mazut_emission_penalty=0.0,

        # Same costs
        battery_capex_usd_per_kwh=500,
        wind_capex_multiplier=1.0,

        # EXTREME DUST (climate change scenario)
        dust_severity='severe',
        dust_impact_factor=0.50,       # 50% efficiency loss!
        dust_storm_frequency=0.55,     # 200 days/year of dust

        optimization_objective='cost',
        gas_turbine_enabled=True,
        biogas_enabled=True,
        grid_enabled=True,
    ),

    # =========================================================================
    # S6: TECHNOLOGY COST REDUCTION (FUTURE 2030)
    # =========================================================================
    'S6': ScenarioConfig(
        id='S6',
        name='Future 2030 (Cheap Renewables)',
        description='Learning curve: 50% cheaper batteries, 30% cheaper wind turbines',

        # Full resource availability
        gas_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        grid_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        water_availability_factor=1.0,

        # Normal demand
        water_demand_multiplier=1.0,
        heat_demand_multiplier=1.0,
        elec_demand_multiplier=1.0,

        # Partial subsidy removal (transition period)
        elec_price_usd_kwh=0.05,
        gas_price_usd_kwh=0.02,
        gas_price_multiplier=1.0,
        grid_import_cost=0.05,
        grid_export_price=0.04,

        # Moderate carbon pricing
        carbon_tax_usd_per_ton=30.0,
        carbon_credit_usd_per_ton=30.0,
        carbon_tier='VCC',

        # TECHNOLOGY LEARNING CURVE (2030 projection)
        battery_capex_usd_per_kwh=250,  # 50% cheaper (from 500)
        wind_capex_multiplier=0.7,      # 30% cheaper

        # Moderate dust
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        optimization_objective='multi-objective',
        gas_turbine_enabled=True,
        biogas_enabled=True,
        grid_enabled=True,
    ),

    # =========================================================================
    # S7: SUMMER ELECTRICITY & WATER CRISIS
    # =========================================================================
    'S7': ScenarioConfig(
        id='S7',
        name='Summer Crisis (Power + Water)',
        description='Summer peak demand: Grid blackouts + water shortage + high cooling demand',

        # Full gas, limited grid in summer
        gas_seasonal_availability={
            'spring': 1.0,
            'summer': 1.0,
            'fall': 1.0,
            'winter': 1.0
        },
        grid_seasonal_availability={
            'spring': 1.0,
            'summer': 0.5,   # 50% grid availability in summer (blackouts)
            'fall': 1.0,
            'winter': 1.0
        },
        # Afternoon blackouts (peak hours)
        grid_blackout_hours=[12, 13, 14, 15, 16, 17],  # 12pm-6pm blackout

        # Water shortage (drought)
        water_availability_factor=0.7,  # 30% less groundwater

        # SUMMER PEAK DEMAND
        water_demand_multiplier=1.4,    # 40% more water (agriculture + urban)
        heat_demand_multiplier=0.7,     # 30% less heating (it's summer)
        elec_demand_multiplier=1.25,    # 25% more electricity (cooling)

        # Higher prices in summer
        elec_price_usd_kwh=0.02,        # 2× due to shortage
        gas_price_usd_kwh=0.005,
        gas_price_multiplier=1.0,
        grid_import_cost=0.03,          # 3× expensive
        grid_export_price=0.0,

        # No carbon pricing
        carbon_tax_usd_per_ton=0.0,
        carbon_credit_usd_per_ton=0.0,
        mazut_emission_penalty=0.0,

        # Current costs
        battery_capex_usd_per_kwh=500,
        wind_capex_multiplier=1.0,

        # Moderate dust (summer = some dust but not peak season)
        dust_severity='moderate',
        dust_impact_factor=0.85,
        dust_storm_frequency=0.15,

        optimization_objective='cost',
        gas_turbine_enabled=True,
        biogas_enabled=True,
        grid_enabled=True,  # Enabled but limited availability
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
    print("\n" + "="*80)
    print("AVAILABLE SCENARIOS")
    print("="*80 + "\n")

    for sid, scenario in SCENARIOS.items():
        print(f"  [{sid}] {scenario.name}")
        print(f"      {scenario.description}")
        print()


def compare_scenarios(scenario_ids: list = None) -> None:
    """Print comparison table of scenarios"""
    if not scenario_ids:
        scenario_ids = list(SCENARIOS.keys())

    print("\n" + "="*120)
    print("SCENARIO COMPARISON")
    print("="*120 + "\n")

    # Key parameters to compare
    params = [
        ('Gas (Winter)', lambda s: f"{s.gas_seasonal_availability['winter']:.0%}"),
        ('Grid (Summer)', lambda s: f"{s.grid_seasonal_availability['summer']:.0%}"),
        ('Water Avail.', lambda s: f"{s.water_availability_factor:.0%}"),
        ('Elec Price', lambda s: f"${s.elec_price_usd_kwh:.3f}"),
        ('Gas Price Mult', lambda s: f"×{s.gas_price_multiplier:.1f}"),
        ('Carbon Tax', lambda s: f"${s.carbon_tax_usd_per_ton:.0f}"),
        ('Battery Cost', lambda s: f"${s.battery_capex_usd_per_kwh:.0f}"),
        ('Dust Impact', lambda s: f"{s.dust_impact_factor:.0%}"),
    ]

    # Header
    print(f"{'Parameter':<20} ", end='')
    for sid in scenario_ids:
        print(f"{sid:<15} ", end='')
    print()
    print("-" * 120)

    # Rows
    for param_name, param_func in params:
        print(f"{param_name:<20} ", end='')
        for sid in scenario_ids:
            scenario = SCENARIOS[sid]
            value_str = param_func(scenario)
            print(f"{value_str:<15} ", end='')
        print()

    print("="*120 + "\n")


if __name__ == "__main__":
    # Test scenario definitions
    list_scenarios()
    print("\n")
    compare_scenarios()

    # Print detailed info for S7
    print("\n")
    print(SCENARIOS['S7'].get_display_info())
