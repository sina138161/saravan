"""
BI-LEVEL Optimization for Saravan Energy System

This module implements two-level optimization:
- Level 1 (Upper): Capacity planning for 30 years
- Level 2 (Lower): Operational optimization for year 30 (8760 hours)

Approach: PyPSA with extendable capacity for all technologies
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pypsa
import json
from typing import Dict, Tuple

# Add project directory to path
project_dir = Path(__file__).parent / 'saravan_wind_water_nexus'
sys.path.insert(0, str(project_dir))

from config import config
from bi_level_config import BI_LEVEL_CONFIG
from scenarios import ScenarioConfig
from scenario_runner import apply_scenario_to_dataset


class BiLevelOptimizer:
    """
    BI-LEVEL Optimizer for Scenario-Specific Capacity Planning

    این کلاس برای هر سناریو جداگانه:
    1. Level 1: بهینه‌ترین ظرفیت تکنولوژی‌ها را پیدا می‌کند
    2. Level 2: عملکرد ساعتی سیستم را برای سال 30 optimize می‌کند
    3. NPV 30 ساله محاسبه می‌کند
    """

    def __init__(
        self,
        scenario: ScenarioConfig,
        dataset: Dict,
        snapshots: pd.DatetimeIndex,
        config_bilevel = None
    ):
        """
        Initialize BI-LEVEL Optimizer

        Args:
            scenario: پیکربندی سناریو
            dataset: داده‌های time series (برای سال 30)
            snapshots: زمان‌های optimization (8760 ساعت)
            config_bilevel: پیکربندی اقتصادی (پیش‌فرض: BI_LEVEL_CONFIG)
        """
        self.scenario = scenario
        self.dataset = dataset
        self.snapshots = snapshots
        self.config_bilevel = config_bilevel or BI_LEVEL_CONFIG

        # Apply scenario constraints to dataset
        self.modified_dataset = apply_scenario_to_dataset(scenario, dataset)

        # Initialize network
        self.network = None
        self.results = None

    def build_expansion_network(self) -> pypsa.Network:
        """
        ساخت شبکه PyPSA با قابلیت توسعه ظرفیت

        همه تکنولوژی‌ها با p_nom_extendable=True یا e_nom_extendable=True
        تعریف می‌شوند تا optimizer بهینه‌ترین ظرفیت را پیدا کند.

        Returns:
            PyPSA Network object
        """
        print("\n" + "="*70)
        print(f"BUILDING BI-LEVEL EXPANSION NETWORK FOR: {self.scenario.name}")
        print("="*70)

        network = pypsa.Network()
        network.set_snapshots(self.snapshots)

        hours = len(self.snapshots)
        cfg = self.config_bilevel

        # ==================== BUS ====================
        network.add("Bus", "Main_Bus", carrier="AC")
        network.add("Bus", "Heat_Bus", carrier="heat")
        network.add("Bus", "Water_Bus", carrier="water")
        network.add("Bus", "Gas_Bus", carrier="gas")
        network.add("Bus", "Biogas_Bus", carrier="biogas")

        print("\n✅ Buses created")

        # ==================== WIND GENERATION (EXTENDABLE) ====================

        # Wind capacity factor (weighted average of HAWT and Bladeless profiles)
        wind_speed = self.modified_dataset['wind']['wind_speed_ms'].values

        # HAWT capacity factor
        hawt_cf = np.minimum(1.0, np.maximum(0.0, (wind_speed - 3) / (12 - 3)))

        # Bladeless capacity factor (lower performance)
        bladeless_cf = hawt_cf * 0.4  # Bladeless performs at ~40% of HAWT

        # Weighted average (optimizer will decide the mix)
        wind_cf = (hawt_cf + bladeless_cf) / 2.0  # Simple average

        # Annualized CAPEX
        wind_capex_annualized = cfg.calculate_annualized_capex(
            cfg.hawt_capex_usd_per_kw,  # Use HAWT as baseline
            cfg.hawt_lifetime_years
        )

        network.add(
            "Generator",
            "Wind_Total",
            bus="Main_Bus",
            p_nom_extendable=True,
            p_nom_max=cfg.hawt_max_capacity_kw + cfg.bladeless_max_capacity_kw,
            capital_cost=wind_capex_annualized,  # $/kW/year
            marginal_cost=cfg.hawt_om_usd_per_kw_year / 8760,  # Convert to $/kWh
            p_max_pu=wind_cf,
            carrier="wind"
        )

        print(f"  🌬️ Wind (extendable): Max {cfg.hawt_max_capacity_kw + cfg.bladeless_max_capacity_kw} kW")

        # ==================== BATTERY STORAGE (EXTENDABLE) ====================

        battery_capex_annualized = cfg.calculate_annualized_capex(
            cfg.battery_capex_usd_per_kwh * self.scenario.battery_capex_multiplier,
            cfg.battery_lifetime_years
        )

        network.add(
            "Bus",
            "Battery_Bus",
            carrier="battery"
        )

        network.add(
            "Store",
            "Battery",
            bus="Battery_Bus",
            e_nom_extendable=True,
            e_nom_max=cfg.battery_max_capacity_kwh,
            capital_cost=battery_capex_annualized,  # $/kWh/year
            marginal_cost=cfg.battery_om_usd_per_kwh_year / 8760,
            standing_loss=0.001,  # 0.1% per hour
            carrier="battery"
        )

        # Battery charger (AC to battery)
        network.add(
            "Link",
            "Battery_Charger",
            bus0="Main_Bus",
            bus1="Battery_Bus",
            p_nom_extendable=True,
            p_nom_max=cfg.battery_max_power_kw,
            efficiency=cfg.battery_efficiency,
            capital_cost=0,  # Included in battery cost
        )

        # Battery discharger (battery to AC)
        network.add(
            "Link",
            "Battery_Discharger",
            bus0="Battery_Bus",
            bus1="Main_Bus",
            p_nom_extendable=True,
            p_nom_max=cfg.battery_max_power_kw,
            efficiency=cfg.battery_efficiency,
            capital_cost=0,
        )

        print(f"  🔋 Battery (extendable): Max {cfg.battery_max_capacity_kwh} kWh")

        # ==================== GAS SUPPLY ====================

        # Gas availability (affected by scenario)
        gas_availability = self.modified_dataset['gas_availability']['availability_mwh'].values

        network.add(
            "Generator",
            "Gas_Supply",
            bus="Gas_Bus",
            p_nom=np.max(gas_availability) * 1.2,  # Slightly higher than max
            p_max_pu=gas_availability / (np.max(gas_availability) * 1.2),
            marginal_cost=cfg.gas_fuel_cost_usd_per_kwh * self.scenario.gas_price_multiplier,
            carrier="gas"
        )

        print(f"  ⛽ Gas supply: Max {np.max(gas_availability):.0f} kWh/h")

        # ==================== GAS MICROTURBINE (EXTENDABLE) ====================

        turbine_capex_annualized = cfg.calculate_annualized_capex(
            cfg.gas_turbine_capex_usd_per_kw,
            cfg.gas_turbine_lifetime_years
        )

        # Add carbon cost to marginal cost
        carbon_cost_per_kwh = (
            self.scenario.carbon_tax_usd_per_ton * cfg.gas_co2_intensity_ton_per_mwh / 1000
        )

        network.add(
            "Link",
            "Gas_Microturbine",
            bus0="Gas_Bus",
            bus1="Main_Bus",
            bus2="Heat_Bus",  # Waste heat recovery
            p_nom_extendable=True,
            p_nom_max=cfg.gas_turbine_max_capacity_kw,
            capital_cost=turbine_capex_annualized,  # $/kW/year
            marginal_cost=cfg.gas_turbine_om_usd_per_kwh + carbon_cost_per_kwh,
            efficiency=cfg.gas_turbine_efficiency,
            efficiency2=0.50,  # Heat recovery ratio
            carrier="gas"
        )

        print(f"  ⚡ Gas Turbine (extendable): Max {cfg.gas_turbine_max_capacity_kw} kW")

        # ==================== GAS BOILER (EXTENDABLE) ====================

        boiler_capex_annualized = cfg.calculate_annualized_capex(
            cfg.gas_boiler_capex_usd_per_kw,
            cfg.gas_boiler_lifetime_years
        )

        network.add(
            "Link",
            "Gas_Boiler",
            bus0="Gas_Bus",
            bus1="Heat_Bus",
            p_nom_extendable=True,
            p_nom_max=cfg.gas_boiler_max_capacity_kw,
            capital_cost=boiler_capex_annualized,
            marginal_cost=cfg.gas_boiler_om_usd_per_kwh,
            efficiency=cfg.gas_boiler_efficiency,
            carrier="gas"
        )

        print(f"  🔥 Gas Boiler (extendable): Max {cfg.gas_boiler_max_capacity_kw} kW")

        # ==================== BIOGAS SYSTEM ====================

        # Biomass availability
        if 'biomass_availability' in self.modified_dataset:
            biomass_available = self.modified_dataset['biomass_availability']['biomass_ton_h'].values
            biogas_potential = biomass_available * 100  # Rough conversion to kWh
        else:
            biogas_potential = np.ones(hours) * 50  # Default: 50 kWh/h

        network.add(
            "Generator",
            "Biogas_Supply",
            bus="Biogas_Bus",
            p_nom=np.max(biogas_potential) * 1.2,
            p_max_pu=biogas_potential / (np.max(biogas_potential) * 1.2),
            marginal_cost=0.01,  # Very low (waste material)
            carrier="biogas"
        )

        # Biogas to electricity
        biogas_gen_capex = cfg.calculate_annualized_capex(
            cfg.biogas_generator_capex_usd_per_kw,
            cfg.biogas_generator_lifetime_years
        )

        network.add(
            "Link",
            "Biogas_Generator",
            bus0="Biogas_Bus",
            bus1="Main_Bus",
            p_nom_extendable=True,
            p_nom_max=cfg.biogas_generator_max_capacity_kw,
            capital_cost=biogas_gen_capex,
            marginal_cost=0.02,
            efficiency=0.35,
            carrier="biogas"
        )

        print(f"  🌾 Biogas Generator (extendable): Max {cfg.biogas_generator_max_capacity_kw} kW")

        # ==================== GRID CONNECTION ====================

        # Grid availability
        grid_availability = self.modified_dataset['grid_availability']['availability_factor'].values

        # Grid import
        network.add(
            "Generator",
            "Grid_Import",
            bus="Main_Bus",
            p_nom=cfg.grid_max_import_kw,
            p_max_pu=grid_availability,
            marginal_cost=cfg.grid_import_price_usd_per_kwh * self.scenario.grid_price_multiplier,
            carrier="grid"
        )

        # Grid export
        network.add(
            "Load",
            "Grid_Export",
            bus="Main_Bus",
            p_set=-cfg.grid_max_export_kw * np.ones(hours),  # Negative load = export capacity
            carrier="grid"
        )

        print(f"  🔌 Grid: Import {cfg.grid_max_import_kw} kW, Export {cfg.grid_max_export_kw} kW")

        # ==================== WATER SYSTEM (EXTENDABLE) ====================

        water_tank_capex = cfg.calculate_annualized_capex(
            cfg.water_tank_capex_usd_per_m3,
            cfg.water_tank_lifetime_years
        )

        network.add(
            "Store",
            "Water_Tank",
            bus="Water_Bus",
            e_nom_extendable=True,
            e_nom_max=cfg.water_tank_max_volume_m3,
            capital_cost=water_tank_capex,  # $/m³/year
            standing_loss=0.001,
            carrier="water"
        )

        # Water pump (electricity to water)
        network.add(
            "Link",
            "Water_Pump",
            bus0="Main_Bus",
            bus1="Water_Bus",
            p_nom_extendable=True,
            p_nom_max=cfg.water_pump_max_power_kw,
            capital_cost=cfg.calculate_annualized_capex(
                cfg.water_pump_capex_usd_per_kw,
                20  # pump lifetime
            ),
            marginal_cost=0.005,
            efficiency=0.75,  # Electric to hydraulic
            carrier="water"
        )

        print(f"  💧 Water Tank (extendable): Max {cfg.water_tank_max_volume_m3} m³")

        # ==================== LOADS/DEMANDS ====================

        # Electricity demand
        elec_demand = self.modified_dataset['electricity_demand']['total_kwh'].values
        network.add(
            "Load",
            "Electricity_Demand",
            bus="Main_Bus",
            p_set=elec_demand,
            carrier="electricity"
        )

        # Heat demand
        heat_demand = self.modified_dataset['heat_demand']['total_kwh_thermal'].values
        network.add(
            "Load",
            "Heat_Demand",
            bus="Heat_Bus",
            p_set=heat_demand,
            carrier="heat"
        )

        # Water demand
        water_demand = self.modified_dataset['water_demand']['total_m3'].values
        network.add(
            "Load",
            "Water_Demand",
            bus="Water_Bus",
            p_set=water_demand,
            carrier="water"
        )

        print(f"\n📊 Demands:")
        print(f"  Electricity: {np.mean(elec_demand):.1f} kW avg, {np.max(elec_demand):.1f} kW peak")
        print(f"  Heat: {np.mean(heat_demand):.1f} kW avg, {np.max(heat_demand):.1f} kW peak")
        print(f"  Water: {np.mean(water_demand):.1f} m³/h avg, {np.max(water_demand):.1f} m³/h peak")

        print("\n✅ Network built successfully")
        print("="*70)

        self.network = network
        return network

    def optimize(self, solver_name='glpk'):
        """
        اجرای optimization دو سطحی

        PyPSA به صورت همزمان هم ظرفیت و هم dispatch را optimize می‌کند.

        Args:
            solver_name: نام solver (glpk, gurobi, cplex)

        Returns:
            وضعیت optimization
        """
        if self.network is None:
            self.build_expansion_network()

        print(f"\n⚙️ Running BI-LEVEL optimization with {solver_name}...")
        print(f"   Variables: {len(self.network.generators)} generators, {len(self.network.stores)} stores")
        print(f"   Snapshots: {len(self.network.snapshots)}")

        status = self.network.optimize(solver_name=solver_name)

        print(f"\n✅ Optimization status: {status}")
        print(f"   Objective value: ${self.network.objective:,.0f}")

        return status

    def extract_results(self) -> Dict:
        """
        استخراج نتایج optimization

        Returns:
            دیکشنری شامل:
            - optimal_capacities: ظرفیت‌های بهینه
            - economics: CAPEX, OPEX, NPV, LCOE
            - operations: آمار عملیاتی
            - emissions: انتشارات
        """
        if self.network is None:
            raise ValueError("Network not optimized yet!")

        cfg = self.config_bilevel
        net = self.network

        print("\n" + "="*70)
        print("EXTRACTING BI-LEVEL OPTIMIZATION RESULTS")
        print("="*70)

        # ==================== OPTIMAL CAPACITIES ====================

        optimal_capacities = {}

        # Wind
        if 'Wind_Total' in net.generators.index:
            optimal_capacities['wind_total_kw'] = net.generators.loc['Wind_Total', 'p_nom_opt']

        # Battery
        if 'Battery' in net.stores.index:
            optimal_capacities['battery_kwh'] = net.stores.loc['Battery', 'e_nom_opt']
            optimal_capacities['battery_charger_kw'] = net.links.loc['Battery_Charger', 'p_nom_opt']
            optimal_capacities['battery_discharger_kw'] = net.links.loc['Battery_Discharger', 'p_nom_opt']

        # Gas turbine
        if 'Gas_Microturbine' in net.links.index:
            optimal_capacities['gas_turbine_kw'] = net.links.loc['Gas_Microturbine', 'p_nom_opt']

        # Gas boiler
        if 'Gas_Boiler' in net.links.index:
            optimal_capacities['gas_boiler_kw'] = net.links.loc['Gas_Boiler', 'p_nom_opt']

        # Biogas
        if 'Biogas_Generator' in net.links.index:
            optimal_capacities['biogas_generator_kw'] = net.links.loc['Biogas_Generator', 'p_nom_opt']

        # Water tank
        if 'Water_Tank' in net.stores.index:
            optimal_capacities['water_tank_m3'] = net.stores.loc['Water_Tank', 'e_nom_opt']

        # Water pump
        if 'Water_Pump' in net.links.index:
            optimal_capacities['water_pump_kw'] = net.links.loc['Water_Pump', 'p_nom_opt']

        print("\n📊 OPTIMAL CAPACITIES:")
        for tech, capacity in optimal_capacities.items():
            print(f"  {tech}: {capacity:.1f}")

        # ==================== ECONOMICS ====================

        # Calculate CAPEX
        total_capex = 0

        if 'wind_total_kw' in optimal_capacities:
            capex_wind = optimal_capacities['wind_total_kw'] * cfg.hawt_capex_usd_per_kw
            total_capex += capex_wind

        if 'battery_kwh' in optimal_capacities:
            capex_battery = optimal_capacities['battery_kwh'] * cfg.battery_capex_usd_per_kwh
            total_capex += capex_battery

        if 'gas_turbine_kw' in optimal_capacities:
            capex_turbine = optimal_capacities['gas_turbine_kw'] * cfg.gas_turbine_capex_usd_per_kw
            total_capex += capex_turbine

        if 'gas_boiler_kw' in optimal_capacities:
            capex_boiler = optimal_capacities['gas_boiler_kw'] * cfg.gas_boiler_capex_usd_per_kw
            total_capex += capex_boiler

        if 'biogas_generator_kw' in optimal_capacities:
            capex_biogas = optimal_capacities['biogas_generator_kw'] * cfg.biogas_generator_capex_usd_per_kw
            total_capex += capex_biogas

        if 'water_tank_m3' in optimal_capacities:
            capex_water_tank = optimal_capacities['water_tank_m3'] * cfg.water_tank_capex_usd_per_m3
            total_capex += capex_water_tank

        # Calculate annual OPEX (from optimization objective)
        # PyPSA objective includes annualized CAPEX + marginal costs
        annual_opex_from_fuel = net.objective / len(net.snapshots) * 8760

        # Calculate 30-year NPV
        npv_opex_30_years = cfg.calculate_npv_opex(annual_opex_from_fuel, 30)
        total_npv = total_capex + npv_opex_30_years

        # Calculate total energy supplied
        total_energy_supplied_mwh = net.loads_t.p['Electricity_Demand'].sum() / 1000

        # LCOE
        lcoe_usd_per_mwh = total_npv / (total_energy_supplied_mwh * 30) if total_energy_supplied_mwh > 0 else 0

        economics = {
            'total_capex_usd': total_capex,
            'annual_opex_usd': annual_opex_from_fuel,
            'npv_opex_30_years_usd': npv_opex_30_years,
            'total_npv_30_years_usd': total_npv,
            'lcoe_usd_per_mwh': lcoe_usd_per_mwh,
        }

        print("\n💰 ECONOMICS (30-year):")
        print(f"  Total CAPEX: ${economics['total_capex_usd']:,.0f}")
        print(f"  Annual OPEX: ${economics['annual_opex_usd']:,.0f}")
        print(f"  NPV OPEX (30y): ${economics['npv_opex_30_years_usd']:,.0f}")
        print(f"  Total NPV: ${economics['total_npv_30_years_usd']:,.0f}")
        print(f"  LCOE: ${economics['lcoe_usd_per_mwh']:.2f}/MWh")

        # ==================== OPERATIONS ====================

        # Generation by source
        wind_gen_total = net.generators_t.p['Wind_Total'].sum() if 'Wind_Total' in net.generators_t.p.columns else 0

        gas_consumption = 0
        if 'Gas_Microturbine' in net.links_t.p0.columns:
            gas_consumption += net.links_t.p0['Gas_Microturbine'].sum()
        if 'Gas_Boiler' in net.links_t.p0.columns:
            gas_consumption += net.links_t.p0['Gas_Boiler'].sum()

        grid_import = net.generators_t.p['Grid_Import'].sum() if 'Grid_Import' in net.generators_t.p.columns else 0

        biogas_gen = 0
        if 'Biogas_Generator' in net.links_t.p1.columns:
            biogas_gen = net.links_t.p1['Biogas_Generator'].sum()

        total_generation = wind_gen_total + biogas_gen + grid_import
        renewable_fraction = (wind_gen_total + biogas_gen) / total_generation if total_generation > 0 else 0

        operations = {
            'wind_generation_kwh': wind_gen_total,
            'biogas_generation_kwh': biogas_gen,
            'grid_import_kwh': grid_import,
            'gas_consumption_kwh': gas_consumption,
            'renewable_fraction_pct': renewable_fraction * 100,
        }

        print("\n⚡ OPERATIONS (Year 30):")
        print(f"  Wind: {operations['wind_generation_kwh']:,.0f} kWh")
        print(f"  Biogas: {operations['biogas_generation_kwh']:,.0f} kWh")
        print(f"  Grid: {operations['grid_import_kwh']:,.0f} kWh")
        print(f"  Renewable: {operations['renewable_fraction_pct']:.1f}%")

        # ==================== EMISSIONS ====================

        co2_from_gas = gas_consumption * cfg.gas_co2_intensity_ton_per_mwh / 1000
        co2_from_grid = grid_import * cfg.grid_co2_intensity_ton_per_mwh / 1000
        total_co2_tons = co2_from_gas + co2_from_grid

        emissions = {
            'co2_from_gas_tons': co2_from_gas,
            'co2_from_grid_tons': co2_from_grid,
            'total_co2_tons': total_co2_tons,
        }

        print("\n🌍 EMISSIONS (Year 30):")
        print(f"  CO2 from gas: {emissions['co2_from_gas_tons']:.1f} tons")
        print(f"  CO2 from grid: {emissions['co2_from_grid_tons']:.1f} tons")
        print(f"  Total CO2: {emissions['total_co2_tons']:.1f} tons")

        print("\n" + "="*70)

        self.results = {
            'scenario': {
                'id': self.scenario.id,
                'name': self.scenario.name,
            },
            'optimal_capacities': optimal_capacities,
            'economics': economics,
            'operations': operations,
            'emissions': emissions,
        }

        return self.results

    def save_results(self, output_dir: Path):
        """ذخیره نتایج"""
        if self.results is None:
            raise ValueError("No results to save. Run optimize() and extract_results() first.")

        output_path = output_dir / f"bilevel_results_{self.scenario.id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to: {output_path}")

        return output_path


if __name__ == "__main__":
    """Test BI-LEVEL optimizer"""
    print("BI-LEVEL Optimizer - Test Mode")
    print("For actual use, run through main.py with BI-LEVEL mode")
