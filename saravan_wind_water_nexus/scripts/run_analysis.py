"""
Main Analysis Runner

Orchestrates the complete workflow for the Saravan Wind-Water-Energy-Carbon
Nexus model: data preparation, network building, optimization, carbon analysis,
and visualization.
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from prepare_data import prepare_data
from build_network import build_network
from solve_network import solve_network
from config import config
from carbon_market_model import CarbonMarketModel
from wind_turbine_models import WindTurbineModels


def calculate_carbon_metrics(dataset, turbine_mix, hours):
    """
    Calculate carbon emissions avoided and revenue potential

    Args:
        dataset: Generated data
        turbine_mix: Turbine configuration
        hours: Simulation hours

    Returns:
        Carbon metrics dictionary
    """

    print("\n" + "="*70)
    print("CARBON MARKET ANALYSIS")
    print("="*70)

    carbon_market = CarbonMarketModel()
    turbines = WindTurbineModels()

    # Extract data
    wind_speeds = dataset['wind']['wind_speed_ms'].values
    dust_pm10 = dataset['dust']['pm10_ugm3'].values
    temperatures = dataset['temperature']['temperature_c'].values

    # Calculate total energy generation
    total_annual_energy = 0

    for turbine_type, n_turbines in turbine_mix.items():
        if n_turbines == 0:
            continue

        hourly_power = np.array([
            turbines.calculate_power_output(turbine_type, v, d, t)
            for v, d, t in zip(wind_speeds, dust_pm10, temperatures)
        ])

        total_power = hourly_power * n_turbines
        total_annual_energy += total_power.sum()

    # Annualize if less than a year
    if hours < 8760:
        annual_energy_kwh = total_annual_energy * (8760 / hours)
    else:
        annual_energy_kwh = total_annual_energy

    # Calculate CO2 avoided
    co2_avoided_tons = carbon_market.calculate_avoided_emissions(
        annual_energy_kwh,
        'diesel_generator'
    )

    # Water co-benefit
    annual_water = dataset['water_demand']['total_m3h'].sum()
    if hours < 8760:
        annual_water = annual_water * (8760 / hours)

    co2_water_benefit = carbon_market.calculate_water_carbon_benefit(
        annual_water,
        'diesel_water_pump'
    )

    total_co2_avoided = co2_avoided_tons + co2_water_benefit

    # Optimize carbon market tier
    tier_optimization = carbon_market.optimize_tier_selection(
        total_co2_avoided,
        water_access_improvement=True
    )

    print(f"\nCarbon Impact:")
    print(f"  Annual energy: {annual_energy_kwh:,.0f} kWh")
    print(f"  CO2 from energy: {co2_avoided_tons:,.0f} tons")
    print(f"  CO2 from water: {co2_water_benefit:,.0f} tons")
    print(f"  TOTAL CO2 avoided: {total_co2_avoided:,.0f} tons/year")

    print(f"\nOptimal Carbon Market Tier: {tier_optimization['optimal_tier']}")
    print(f"  Annual revenue: ${tier_optimization['optimal_tier_data']['net_revenue']:,.0f}")

    return {
        'annual_energy_kwh': annual_energy_kwh,
        'co2_avoided_tons': total_co2_avoided,
        'co2_from_energy': co2_avoided_tons,
        'co2_from_water': co2_water_benefit,
        'optimal_tier': tier_optimization['optimal_tier'],
        'carbon_revenue_annual': tier_optimization['optimal_tier_data']['net_revenue'],
        'tier_comparison': tier_optimization['comparison_table'].to_dict()
    }


def export_results(results, network, dataset):
    """
    Export all results to files

    Args:
        results: Complete results dictionary
        network: PyPSA network
        dataset: Generated data
    """

    print("\n" + "="*70)
    print("EXPORTING RESULTS")
    print("="*70)

    output_dir = config.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export summary JSON
    if config.EXPORT_SUMMARY_JSON:
        summary = {
            'configuration': results['configuration'],
            'carbon': {
                'annual_energy_kwh': results['carbon']['annual_energy_kwh'],
                'co2_avoided_tons': results['carbon']['co2_avoided_tons'],
                'optimal_tier': results['carbon']['optimal_tier'],
                'carbon_revenue_annual': results['carbon']['carbon_revenue_annual']
            },
            'dataset_stats': results.get('dataset_stats', {}),
            'timestamp': datetime.now().isoformat()
        }

        with open(output_dir / 'summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"  ✓ Saved summary.json")

    # Export network to NetCDF
    if config.EXPORT_NETWORK_NC:
        network.export_to_netcdf(str(output_dir / 'network.nc'))
        print(f"  ✓ Saved network.nc")

    # Export network results to CSV
    if config.EXPORT_RESULTS_CSV:
        network_dir = output_dir / 'network_results'
        network_dir.mkdir(exist_ok=True)
        network.export_to_csv_folder(str(network_dir))
        print(f"  ✓ Saved network results")

    print(f"\n✅ Results exported to {output_dir}")


def create_visualizations(results, network, dataset):
    """
    Create all visualizations

    Args:
        results: Complete results dictionary
        network: PyPSA network
        dataset: Generated data
    """

    output_dir = config.OUTPUT_DIR

    # Standard plots
    if config.CREATE_STANDARD_PLOTS:
        print("\n" + "="*70)
        print("CREATING STANDARD VISUALIZATIONS")
        print("="*70)

        from visualization_nexus import NexusVisualizer
        from carbon_emissions_visualizer import CarbonEmissionsVisualizer
        from carbon_market_model import CarbonMarketModel

        visualizer = NexusVisualizer(
            dataset=dataset,
            network=network,
            results=results,
            output_dir=str(output_dir / 'plots')
        )
        visualizer.create_all_plots()

        carbon_market = CarbonMarketModel()
        carbon_visualizer = CarbonEmissionsVisualizer(
            results=results,
            carbon_model=carbon_market,
            output_dir=str(output_dir / 'carbon_plots')
        )
        carbon_visualizer.create_all_plots(
            network,
            results['carbon']['co2_avoided_tons']
        )

    # Publication figures
    if config.CREATE_PUBLICATION_FIGURES:
        print("\n" + "="*70)
        print("CREATING PUBLICATION-READY FIGURES")
        print("="*70)

        from publication_visualizations import PublicationVisualizer

        publication_visualizer = PublicationVisualizer(
            network=network,
            results=results,
            dataset=dataset,
            output_dir=str(output_dir / 'publication_figures')
        )
        publication_visualizer.create_all_publication_figures()


def run_complete_analysis():
    """
    Run complete analysis workflow

    Returns:
        Complete results dictionary
    """

    print("\n" + "="*70)
    print("SARAVAN WIND-WATER-ENERGY-CARBON NEXUS ANALYSIS")
    print("="*70)
    print(f"Configuration: {config}")

    # Step 1: Prepare data
    dataset = prepare_data()

    # Step 2: Build network
    network, network_builder = build_network(dataset)

    # Step 3: Solve optimization
    optimization_results = solve_network(network_builder)

    # Step 4: Calculate carbon metrics
    from pandas import date_range
    snapshots = date_range(
        start=config.SNAPSHOTS_START,
        end=config.SNAPSHOTS_END,
        freq=config.SNAPSHOTS_FREQ
    )
    hours = len(snapshots)

    carbon_results = calculate_carbon_metrics(
        dataset,
        config.TURBINE_MIX,
        hours
    )

    # Compile results
    results = {
        'configuration': {
            'turbine_mix': config.TURBINE_MIX,
            'battery_kwh': config.BATTERY_CAPACITY_KWH,
            'water_tank_m3': config.WATER_TANK_CAPACITY_M3,
            'water_tank_elevation_m': config.WATER_TANK_ELEVATION_M,
            'hours': hours,
            'solver': config.SOLVER
        },
        'optimization': optimization_results,
        'carbon': carbon_results,
        'dataset_stats': {
            'wind_mean_ms': dataset['wind']['wind_speed_ms'].mean(),
            'dust_mean_ugm3': dataset['dust']['pm10_ugm3'].mean(),
            'temp_mean_c': dataset['temperature']['temperature_c'].mean(),
            'water_demand_total_m3': dataset['water_demand']['total_m3h'].sum()
        }
    }

    # Step 5: Export results
    export_results(results, network, dataset)

    # Step 6: Create visualizations
    create_visualizations(results, network, dataset)

    print("\n" + "="*70)
    print("✅ COMPLETE ANALYSIS FINISHED!")
    print("="*70)
    print(f"\nResults saved to: {config.OUTPUT_DIR}")

    return results


if __name__ == "__main__":
    results = run_complete_analysis()
