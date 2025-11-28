"""
Scenario Runner for Saravan Wind-Water-Energy-Carbon Nexus Model

This module handles:
- Applying scenario configurations to the network
- Running complete scenario simulations
- Saving scenario-specific results
"""

import numpy as np
import pandas as pd
import copy
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime

from scenarios import ScenarioConfig, get_scenario
from config import config


def apply_scenario_to_dataset(scenario: ScenarioConfig, dataset: Dict) -> Dict:
    """
    Apply scenario environmental conditions to dataset

    Args:
        scenario: Scenario configuration
        dataset: Generated dataset

    Returns:
        Modified dataset with scenario-specific conditions
    """
    # Make a deep copy to avoid modifying original
    modified_dataset = copy.deepcopy(dataset)

    # ===== APPLY DUST IMPACT =====
    if scenario.dust_severity != 'moderate' or scenario.dust_impact_factor != 0.85:
        # Adjust wind speed based on dust impact
        # Higher dust = lower effective wind speed for turbines
        wind_speed = modified_dataset['wind']['speed_ms'].values
        modified_dataset['wind']['speed_ms'] = wind_speed * scenario.dust_impact_factor

        # Adjust dust parameters
        if scenario.dust_severity == 'severe':
            # Increase dust concentration
            modified_dataset['dust']['pm10_ugm3'] = modified_dataset['dust']['pm10_ugm3'] * 1.5
        elif scenario.dust_severity == 'low':
            # Decrease dust concentration
            modified_dataset['dust']['pm10_ugm3'] = modified_dataset['dust']['pm10_ugm3'] * 0.6

    return modified_dataset


def apply_scenario_to_technologies(scenario: ScenarioConfig, technologies: Dict) -> Dict:
    """
    Apply scenario configuration to technology models

    Args:
        scenario: Scenario configuration
        technologies: Dictionary of technology instances

    Returns:
        Modified technologies dictionary
    """
    # Make a deep copy
    modified_technologies = copy.deepcopy(technologies)

    # ===== CARBON MARKET CONFIGURATION =====
    if 'carbon_market' in modified_technologies:
        carbon_model = modified_technologies['carbon_market']
        if scenario.carbon_tier:
            # Set active tier
            carbon_model.active_tier = scenario.carbon_tier
            # Enable water bonus if specified
            if scenario.carbon_water_bonus:
                carbon_model.water_access_improvement = True

    # ===== BATTERY CONFIGURATION =====
    if 'battery_ess' in modified_technologies:
        battery_model = modified_technologies['battery_ess']
        # Update capacity
        battery_model.specs['P_ESS_cap'] = scenario.battery_kwh
        battery_model.specs['P_ESS_max'] = scenario.battery_power_kw

    # ===== THERMAL STORAGE CONFIGURATION =====
    if 'thermal_storage' in modified_technologies:
        thermal_model = modified_technologies['thermal_storage']
        thermal_model.specs['Q_TSS_cap'] = scenario.thermal_storage_kwh

    # ===== BIOGAS CONFIGURATION =====
    if 'anaerobic_digester' in modified_technologies:
        biogas_model = modified_technologies['anaerobic_digester']
        if not scenario.biogas_enabled:
            # Disable by setting capacity to 0
            biogas_model.specs['V_digester'] = 0
        else:
            biogas_model.specs['V_digester'] = scenario.biogas_digester_m3

    # ===== GAS TURBINE CONFIGURATION =====
    if 'gas_microturbine' in modified_technologies:
        gas_model = modified_technologies['gas_microturbine']
        if not scenario.gas_turbine_enabled:
            gas_model.specs['rated_capacity_kw'] = 0
        else:
            gas_model.specs['rated_capacity_kw'] = scenario.gas_turbine_capacity_kw

    # ===== WATER TANK CONFIGURATION =====
    if 'elevated_storage' in modified_technologies:
        water_model = modified_technologies['elevated_storage']
        water_model.specs['V_awt_max'] = scenario.water_tank_m3

    return modified_technologies


def apply_scenario_to_network(scenario: ScenarioConfig, network, dataset: Dict) -> None:
    """
    Apply scenario configuration to PyPSA network

    Modifies network in-place based on scenario parameters.

    Args:
        scenario: Scenario configuration
        network: PyPSA network object
        dataset: Dataset (for time-varying adjustments)
    """

    hours = len(dataset['wind']['timestamp'])

    # ===== WIND CAPACITY ADJUSTMENT =====
    if scenario.wind_capacity_multiplier != 1.0:
        for gen in network.generators.index:
            if 'Wind_' in gen:
                # Scale capacity
                network.generators.loc[gen, 'p_nom'] *= scenario.wind_capacity_multiplier

    # ===== GRID CONFIGURATION =====
    if 'Grid' in network.generators.index:
        if not scenario.grid_enabled:
            # Remove grid completely
            network.remove('Generator', 'Grid')
        else:
            # Update grid parameters
            network.generators.loc['Grid', 'p_nom'] = scenario.grid_max_kw
            network.generators.loc['Grid', 'marginal_cost'] = scenario.grid_import_cost * 1000  # $/MWh

    # ===== BATTERY STORAGE ADJUSTMENT =====
    if 'Battery' in network.stores.index:
        if scenario.battery_kwh == 0:
            # Remove battery
            network.remove('Store', 'Battery')
            # Also remove battery charger link
            if 'Battery_Charger' in network.links.index:
                network.remove('Link', 'Battery_Charger')
        else:
            # Update capacity
            network.stores.loc['Battery', 'e_nom'] = scenario.battery_kwh
            # Update charger power
            if 'Battery_Charger' in network.links.index:
                network.links.loc['Battery_Charger', 'p_nom'] = scenario.battery_power_kw

    # ===== THERMAL STORAGE ADJUSTMENT =====
    if 'Thermal_Storage' in network.stores.index:
        if scenario.thermal_storage_kwh == 0:
            network.remove('Store', 'Thermal_Storage')
        else:
            network.stores.loc['Thermal_Storage', 'e_nom'] = scenario.thermal_storage_kwh

    # ===== WATER TANK ADJUSTMENT =====
    if 'Water_Tank' in network.stores.index:
        network.stores.loc['Water_Tank', 'e_nom'] = scenario.water_tank_m3

    # ===== GAS TURBINE ADJUSTMENT =====
    if 'Gas_Microturbine' in network.generators.index:
        if not scenario.gas_turbine_enabled:
            network.remove('Generator', 'Gas_Microturbine')
            # Remove related heat recovery link if exists
            if 'Heat_Recovery_WHB' in network.links.index:
                network.remove('Link', 'Heat_Recovery_WHB')
        else:
            network.generators.loc['Gas_Microturbine', 'p_nom'] = scenario.gas_turbine_capacity_kw
            # Update fuel cost
            network.generators.loc['Gas_Microturbine', 'marginal_cost'] = scenario.gas_price_usd_kwh * 1000

    # ===== SMART PUMPING ADJUSTMENT =====
    if scenario.smart_pumping and 'Water_Pump' in network.links.index:
        # Enable time-varying pumping cost (pump during cheap hours)
        # This would be implemented through time-varying marginal costs
        # For now, just flag it
        pass

    print(f"✓ Applied scenario configuration to network")


def run_single_scenario(
    scenario_id: str,
    time_horizon_config: Dict,
    base_technologies: Dict,
    verbose: bool = True
) -> Dict:
    """
    Run a complete scenario simulation

    Args:
        scenario_id: Scenario ID (S1, S2, etc.)
        time_horizon_config: Time horizon configuration from main
        base_technologies: Base technology instances
        verbose: Print detailed progress

    Returns:
        Dictionary containing all results for this scenario
    """

    # Get scenario configuration
    scenario = get_scenario(scenario_id)

    if verbose:
        print(scenario.get_display_info())

    # Import required modules (import here to avoid circular dependencies)
    from data import SaravanDataGenerator
    import pypsa

    # =========================================================================
    # STEP 1: GENERATE DATA
    # =========================================================================
    if verbose:
        print("\n" + "="*70)
        print("STEP 1: GENERATING DATA")
        print("="*70 + "\n")

    data_generator = SaravanDataGenerator(random_seed=config.RANDOM_SEED)
    dataset = data_generator.generate_complete_dataset(
        hours=time_horizon_config['snapshots'],
        start_date=time_horizon_config['start_date']
    )

    # Apply scenario environmental conditions
    dataset = apply_scenario_to_dataset(scenario, dataset)

    if verbose:
        print(f"✓ Generated data for {time_horizon_config['snapshots']} hours")

    # =========================================================================
    # STEP 2: PREPARE TECHNOLOGIES
    # =========================================================================
    if verbose:
        print("\n" + "="*70)
        print("STEP 2: APPLYING SCENARIO TO TECHNOLOGIES")
        print("="*70 + "\n")

    # Apply scenario to technologies
    technologies = apply_scenario_to_technologies(scenario, base_technologies)

    if verbose:
        print(f"✓ Applied scenario configuration to technologies")

    # =========================================================================
    # STEP 3: BUILD NETWORK (import build function from main)
    # =========================================================================
    # This will be called from main.py where build_comprehensive_network is defined

    return {
        'scenario': scenario,
        'dataset': dataset,
        'technologies': technologies,
        'time_horizon': time_horizon_config,
    }


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

    print(f"\n{'='*70}")
    print(f"SAVING RESULTS FOR SCENARIO: {scenario.name}")
    print(f"{'='*70}\n")

    # ===== SAVE SCENARIO CONFIGURATION =====
    import json

    scenario_info = {
        'scenario_id': scenario.id,
        'scenario_name': scenario.name,
        'description': scenario.description,
        'time_horizon': time_description,
        'run_timestamp': datetime.now().isoformat(),
        'configuration': {
            'wind_capacity_multiplier': scenario.wind_capacity_multiplier,
            'battery_kwh': scenario.battery_kwh,
            'thermal_storage_kwh': scenario.thermal_storage_kwh,
            'carbon_tier': scenario.carbon_tier,
            'dust_severity': scenario.dust_severity,
            'dust_impact_factor': scenario.dust_impact_factor,
            'elec_price_usd_kwh': scenario.elec_price_usd_kwh,
            'gas_price_usd_kwh': scenario.gas_price_usd_kwh,
        }
    }

    with open(results_dir / 'scenario_config.json', 'w') as f:
        json.dump(scenario_info, f, indent=2)

    print(f"1. ✓ Saved scenario configuration")

    # ===== SAVE NETWORK =====
    try:
        network_file = results_dir / f'network_{scenario.id}.nc'
        network.export_to_netcdf(str(network_file))
        print(f"2. ✓ Saved PyPSA network: {network_file}")
    except Exception as e:
        print(f"2. ⚠ Could not save network: {e}")

    # ===== SAVE RESULTS =====
    for result_name in ['individual_results', 'combined_results', 'comprehensive_results']:
        if result_name in results:
            result_file = results_dir / f'{result_name}_{scenario.id}.json'
            with open(result_file, 'w') as f:
                json.dump(results[result_name], f, indent=2)
            print(f"3. ✓ Saved {result_name}")

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

    # ===== CREATE VISUALIZATIONS =====
    # Visualizations will be saved to results_dir by the visualization modules

    print(f"\n✅ All results saved to: {results_dir}\n")

    return results_dir


def run_all_scenarios(
    time_horizon_config: Dict,
    base_technologies: Dict,
    scenario_ids: list = None
) -> Dict:
    """
    Run all scenarios (or subset) and compare results

    Args:
        time_horizon_config: Time horizon configuration
        base_technologies: Base technology instances
        scenario_ids: List of scenario IDs to run (None = all)

    Returns:
        Dictionary with results for all scenarios
    """

    if scenario_ids is None:
        from scenarios import SCENARIOS
        scenario_ids = list(SCENARIOS.keys())

    all_results = {}

    print(f"\n{'='*80}")
    print(f"RUNNING {len(scenario_ids)} SCENARIOS")
    print(f"{'='*80}\n")

    for i, sid in enumerate(scenario_ids, 1):
        print(f"\n{'#'*80}")
        print(f"# SCENARIO {i}/{len(scenario_ids)}: {sid}")
        print(f"{'#'*80}\n")

        try:
            result = run_single_scenario(sid, time_horizon_config, base_technologies)
            all_results[sid] = result
            print(f"\n✅ Scenario {sid} completed successfully\n")

        except Exception as e:
            print(f"\n❌ Scenario {sid} failed: {e}\n")
            all_results[sid] = {'error': str(e)}

    return all_results


if __name__ == "__main__":
    print("Scenario Runner Module")
    print("This module should be imported and used from main.py")
