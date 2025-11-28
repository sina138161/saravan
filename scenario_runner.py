"""
Scenario Runner for Saravan Wind-Water-Energy-Carbon Nexus Model

This module applies policy-driven constraints to the model:
- Seasonal resource availability (gas, grid, water)
- Demand modifiers
- Economic parameters (prices, taxes, credits)
- Technology costs
- Environmental conditions
"""

import numpy as np
import pandas as pd
import copy
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime

from scenarios import ScenarioConfig, get_scenario
from config import config


def get_season_from_month(month: int) -> str:
    """
    Get season from month number

    Args:
        month: Month number (1-12)

    Returns:
        Season string: 'spring', 'summer', 'fall', 'winter'
    """
    if month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    elif month in [9, 10, 11]:
        return 'fall'
    else:  # 12, 1, 2
        return 'winter'


def apply_scenario_to_dataset(scenario: ScenarioConfig, dataset: Dict) -> Dict:
    """
    Apply scenario constraints to dataset

    Modifies:
    - Resource availability (gas, water)
    - Demand levels (heat, water, electricity)
    - Environmental conditions (dust)

    Args:
        scenario: Scenario configuration
        dataset: Generated dataset

    Returns:
        Modified dataset
    """
    # Make a deep copy
    modified_dataset = copy.deepcopy(dataset)

    timestamps = pd.to_datetime(modified_dataset['wind']['timestamp'])
    hours = len(timestamps)

    # ===== APPLY SEASONAL GAS AVAILABILITY =====
    if 'gas_availability' in modified_dataset:
        gas_avail = modified_dataset['gas_availability']['availability'].values.copy()

        for i, ts in enumerate(timestamps):
            season = get_season_from_month(ts.month)
            gas_factor = scenario.gas_seasonal_availability[season]
            gas_avail[i] *= gas_factor

        modified_dataset['gas_availability']['availability'] = gas_avail

    # ===== APPLY WATER AVAILABILITY =====
    if 'groundwater_availability' in modified_dataset:
        gw_avail = modified_dataset['groundwater_availability']['safe_extraction_m3h'].values
        modified_dataset['groundwater_availability']['safe_extraction_m3h'] = gw_avail * scenario.water_availability_factor

    # ===== APPLY DEMAND MODIFIERS =====
    # Water demand
    if 'water_demand' in modified_dataset:
        for col in modified_dataset['water_demand'].columns:
            if col != 'timestamp':
                modified_dataset['water_demand'][col] *= scenario.water_demand_multiplier

    # Heat demand (seasonal)
    if 'heat_demand' in modified_dataset:
        heat_demand = modified_dataset['heat_demand']['total_kwh_thermal'].values.copy()
        for i, ts in enumerate(timestamps):
            season = get_season_from_month(ts.month)
            if season == 'winter':
                heat_demand[i] *= scenario.heat_demand_multiplier
        modified_dataset['heat_demand']['total_kwh_thermal'] = heat_demand

    # Electricity demand (seasonal - cooling in summer)
    if 'electricity_demand' in modified_dataset:
        elec_demand = modified_dataset['electricity_demand']['total_kwh'].values.copy()
        for i, ts in enumerate(timestamps):
            season = get_season_from_month(ts.month)
            if season == 'summer':
                elec_demand[i] *= scenario.elec_demand_multiplier
        modified_dataset['electricity_demand']['total_kwh'] = elec_demand

    # ===== APPLY DUST IMPACT =====
    if scenario.dust_severity != 'moderate' or scenario.dust_impact_factor != 0.85:
        wind_speed = modified_dataset['wind']['speed_ms'].values.copy()

        # Apply dust impact to wind speed (reduces effective generation)
        wind_speed = wind_speed * scenario.dust_impact_factor

        modified_dataset['wind']['speed_ms'] = wind_speed

        # Adjust dust concentration
        dust_pm10 = modified_dataset['dust']['pm10_ugm3'].values.copy()
        if scenario.dust_severity == 'severe':
            dust_pm10 = dust_pm10 * 2.0  # Double PM10 in severe conditions
        elif scenario.dust_severity == 'low':
            dust_pm10 = dust_pm10 * 0.5  # Half PM10 in good conditions

        modified_dataset['dust']['pm10_ugm3'] = dust_pm10

    print(f"✓ Applied scenario environmental conditions")
    return modified_dataset


def apply_scenario_to_network(scenario: ScenarioConfig, network, dataset: Dict) -> None:
    """
    Apply scenario constraints to PyPSA network

    Modifies:
    - Grid availability (seasonal + blackout hours)
    - Gas generator costs and availability
    - Technology costs (CAPEX for expansion)
    - Carbon pricing (via marginal costs)

    Args:
        scenario: Scenario configuration
        network: PyPSA network object
        dataset: Dataset with timestamps
    """

    timestamps = pd.to_datetime(dataset['wind']['timestamp'])
    hours = len(timestamps)

    # ===== APPLY GRID CONSTRAINTS =====
    if 'Grid' in network.generators.index and scenario.grid_enabled:
        # Update grid import cost
        network.generators.loc['Grid', 'marginal_cost'] = scenario.grid_import_cost * 1000  # $/MWh

        # Apply seasonal availability
        grid_max = network.generators.loc['Grid', 'p_nom']
        grid_availability = np.ones(hours)

        for i, ts in enumerate(timestamps):
            season = get_season_from_month(ts.month)
            grid_availability[i] = scenario.grid_seasonal_availability[season]

            # Apply blackout hours
            if ts.hour in scenario.grid_blackout_hours:
                grid_availability[i] = 0.0

        # Set time-varying max capacity
        network.generators_t.p_max_pu['Grid'] = grid_availability

        print(f"  ✓ Grid availability: seasonal + {len(scenario.grid_blackout_hours)} blackout hours")

    elif not scenario.grid_enabled and 'Grid' in network.generators.index:
        # Remove grid completely
        network.remove('Generator', 'Grid')
        print(f"  ✓ Grid disabled")

    # ===== APPLY GAS CONSTRAINTS =====
    if 'Gas_Microturbine' in network.generators.index:
        # Update gas price
        base_gas_cost = scenario.gas_price_usd_kwh * 1000  # $/MWh
        effective_gas_cost = base_gas_cost * scenario.gas_price_multiplier

        # Apply seasonal gas pricing and availability
        gas_cost_timeseries = np.zeros(hours)
        gas_availability = np.ones(hours)

        for i, ts in enumerate(timestamps):
            season = get_season_from_month(ts.month)
            gas_availability[i] = scenario.gas_seasonal_availability[season]

            # Higher price in winter when shortage
            if season == 'winter':
                gas_cost_timeseries[i] = effective_gas_cost
            else:
                gas_cost_timeseries[i] = base_gas_cost

        # Set time-varying marginal cost
        network.generators_t.marginal_cost['Gas_Microturbine'] = gas_cost_timeseries

        # Set time-varying availability
        network.generators_t.p_max_pu['Gas_Microturbine'] = gas_availability

        print(f"  ✓ Gas turbine: seasonal price (×{scenario.gas_price_multiplier:.1f}) and availability")

    # ===== APPLY CARBON PRICING =====
    # Carbon tax increases marginal cost of fossil generators
    if scenario.carbon_tax_usd_per_ton > 0:
        # Gas turbine: ~0.2 kg CO2/kWh → 0.2 ton/MWh
        if 'Gas_Microturbine' in network.generators.index:
            carbon_cost = scenario.carbon_tax_usd_per_ton * 0.2  # $/MWh
            current_cost = network.generators.loc['Gas_Microturbine', 'marginal_cost']
            network.generators.loc['Gas_Microturbine', 'marginal_cost'] = current_cost + carbon_cost

        # Grid (assume grid has emissions too)
        if 'Grid' in network.generators.index:
            carbon_cost = scenario.carbon_tax_usd_per_ton * 0.5  # Assume 0.5 ton/MWh for grid
            current_cost = network.generators.loc['Grid', 'marginal_cost']
            network.generators.loc['Grid', 'marginal_cost'] = current_cost + carbon_cost

        print(f"  ✓ Carbon tax: ${scenario.carbon_tax_usd_per_ton:.0f}/ton CO2 applied to generators")

    # Carbon credits reduce effective cost of renewables (negative marginal cost)
    if scenario.carbon_credit_usd_per_ton > 0:
        # Wind turbines get carbon credits
        for gen in network.generators.index:
            if 'Wind_' in gen:
                # Assume 0.5 ton CO2 avoided per MWh from wind
                credit_value = -scenario.carbon_credit_usd_per_ton * 0.5  # Negative = revenue
                network.generators.loc[gen, 'marginal_cost'] = credit_value

        print(f"  ✓ Carbon credit: ${scenario.carbon_credit_usd_per_ton:.0f}/ton CO2 avoided for renewables")

    # ===== APPLY MAZUT PENALTY =====
    # When gas unavailable, penalty for using dirty backup fuel
    if scenario.mazut_emission_penalty > 0:
        if 'Grid' in network.generators.index:
            # Add mazut penalty to grid (simulates grid using mazut)
            mazut_cost = scenario.mazut_emission_penalty * 0.8  # 0.8 ton/MWh for mazut
            current_cost = network.generators.loc['Grid', 'marginal_cost']
            network.generators.loc['Grid', 'marginal_cost'] = current_cost + mazut_cost

        print(f"  ✓ Mazut penalty: ${scenario.mazut_emission_penalty:.0f}/ton for dirty fuel")

    # ===== TECHNOLOGY CAPEX (for future expansion analysis) =====
    # Note: PyPSA optimization uses these for investment decisions if enabled
    # For now, we just log them - can be used for economic analysis
    if scenario.battery_capex_usd_per_kwh != 500:
        print(f"  ✓ Battery CAPEX: ${scenario.battery_capex_usd_per_kwh:.0f}/kWh")

    if scenario.wind_capex_multiplier != 1.0:
        print(f"  ✓ Wind CAPEX: ×{scenario.wind_capex_multiplier:.2f}")

    print(f"✓ Applied scenario constraints to network")


def save_scenario_results(
    scenario: ScenarioConfig,
    network,
    dataset: Dict,
    results: Dict,
    time_description: str
) -> Path:
    """
    Save all results for a scenario to its dedicated folder

    Args:
        scenario: Scenario configuration
        network: PyPSA network with optimization results
        dataset: Time series data
        results: Calculated results dictionary
        time_description: Time horizon description

    Returns:
        Path to results directory
    """

    # Create scenario-specific results directory
    results_dir = config.OUTPUT_DIR / scenario.get_folder_name()
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"SAVING RESULTS FOR SCENARIO: {scenario.name}")
    print(f"{'='*80}\n")

    # ===== SAVE SCENARIO CONFIGURATION =====
    import json

    scenario_info = {
        'scenario_id': scenario.id,
        'scenario_name': scenario.name,
        'description': scenario.description,
        'time_horizon': time_description,
        'run_timestamp': datetime.now().isoformat(),
        'configuration': {
            # Resource availability
            'gas_seasonal_availability': scenario.gas_seasonal_availability,
            'grid_seasonal_availability': scenario.grid_seasonal_availability,
            'water_availability_factor': scenario.water_availability_factor,
            'grid_blackout_hours': scenario.grid_blackout_hours,

            # Demand modifiers
            'water_demand_multiplier': scenario.water_demand_multiplier,
            'heat_demand_multiplier': scenario.heat_demand_multiplier,
            'elec_demand_multiplier': scenario.elec_demand_multiplier,

            # Economics
            'elec_price_usd_kwh': scenario.elec_price_usd_kwh,
            'gas_price_usd_kwh': scenario.gas_price_usd_kwh,
            'gas_price_multiplier': scenario.gas_price_multiplier,
            'grid_import_cost': scenario.grid_import_cost,

            # Carbon
            'carbon_tax_usd_per_ton': scenario.carbon_tax_usd_per_ton,
            'carbon_credit_usd_per_ton': scenario.carbon_credit_usd_per_ton,
            'mazut_emission_penalty': scenario.mazut_emission_penalty,
            'carbon_tier': scenario.carbon_tier,

            # Technology costs
            'battery_capex_usd_per_kwh': scenario.battery_capex_usd_per_kwh,
            'wind_capex_multiplier': scenario.wind_capex_multiplier,

            # Environment
            'dust_severity': scenario.dust_severity,
            'dust_impact_factor': scenario.dust_impact_factor,
            'dust_storm_frequency': scenario.dust_storm_frequency,
        }
    }

    with open(results_dir / 'scenario_config.json', 'w') as f:
        json.dump(scenario_info, f, indent=2)

    print(f"1. ✓ Saved scenario configuration")

    # ===== SAVE NETWORK =====
    try:
        network_file = results_dir / f'network_{scenario.id}.nc'
        network.export_to_netcdf(str(network_file))
        print(f"2. ✓ Saved PyPSA network: {network_file.name}")
    except Exception as e:
        print(f"2. ⚠ Could not save network: {e}")

    # ===== SAVE RESULTS =====
    for result_name in ['individual', 'combined', 'comprehensive']:
        if result_name in results:
            result_file = results_dir / f'{result_name}_results_{scenario.id}.json'
            with open(result_file, 'w') as f:
                json.dump(results[result_name], f, indent=2)
            print(f"3. ✓ Saved {result_name}_results")

    # ===== SAVE TIME SERIES =====
    try:
        # Generation time series
        gen_ts = network.generators_t.p
        gen_ts.to_csv(results_dir / f'generation_timeseries_{scenario.id}.csv')

        # Storage time series
        if len(network.stores_t.e.columns) > 0:
            storage_ts = network.stores_t.e
            storage_ts.to_csv(results_dir / f'storage_timeseries_{scenario.id}.csv')

        print(f"4. ✓ Saved time series data")
    except Exception as e:
        print(f"4. ⚠ Could not save time series: {e}")

    print(f"\n✅ All results saved to: {results_dir}\n")

    return results_dir


if __name__ == "__main__":
    print("Scenario Runner Module")
    print("This module should be imported and used from main.py")
