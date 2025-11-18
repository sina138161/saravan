"""
Main execution script for Saravan Wind-Water-Energy Nexus Optimization
Complete workflow from data generation to optimization and results
"""

import os
import json
import numpy as np
from datetime import datetime
from data_generator import SaravanDataGenerator
from network_builder_simple import WindWaterNetworkBuilder
from carbon_market_model import CarbonMarketModel
from wind_turbine_models import WindTurbineModels
from visualization_nexus import NexusVisualizer
from carbon_emissions_visualizer import CarbonEmissionsVisualizer


class SaravanWindWaterOptimizer:
    """
    Main optimizer for Saravan Wind-Water-Energy Nexus

    Complete workflow:
    1. Generate data (wind, dust, temperature, water demand)
    2. Build PyPSA network with turbines, battery, water system
    3. Optimize operations
    4. Calculate carbon revenue
    5. Export results
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize optimizer

        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        self.data_generator = SaravanDataGenerator(random_seed)
        self.carbon_market = CarbonMarketModel()

        # Will be populated during execution
        self.dataset = None
        self.network_builder = None
        self.results = None

    def run_optimization(self,
                        hours: int = 168,
                        turbine_mix: dict = None,
                        battery_size_kwh: float = 500,
                        water_tank_m3: float = 1000,
                        water_tank_elevation_m: float = 25,
                        solver: str = 'highs',
                        export: bool = True) -> dict:
        """
        Run complete optimization workflow

        Args:
            hours: Number of hours to simulate (168=week, 8760=year)
            turbine_mix: Dict with turbine counts, e.g., {'HAWT': 5, 'VAWT': 3, 'Bladeless': 15}
            battery_size_kwh: Battery capacity (kWh)
            water_tank_m3: Water tank size (m³)
            water_tank_elevation_m: Tank elevation (meters)
            solver: Solver name ('highs', 'glpk', 'gurobi', etc.)
            export: Export results to files

        Returns:
            Complete results dictionary
        """

        print("\n" + "="*80)
        print("SARAVAN WIND-WATER-ENERGY NEXUS OPTIMIZATION")
        print("="*80)
        print(f"Duration: {hours} hours ({hours/24:.1f} days)")
        print(f"Solver: {solver}")
        print(f"Export: {export}")

        # Default turbine mix
        if turbine_mix is None:
            if hours <= 168:  # 1 week
                turbine_mix = {'HAWT': 2, 'VAWT': 1, 'Bladeless': 5}
            else:  # Larger system for longer simulations
                turbine_mix = {'HAWT': 5, 'VAWT': 3, 'Bladeless': 15}

        # Step 1: Generate data
        print(f"\n{'='*80}")
        print("STEP 1: DATA GENERATION")
        print(f"{'='*80}")

        self.dataset = self.data_generator.generate_complete_dataset(
            hours=hours,
            start_date="2025-01-01"
        )

        # Step 2: Build network
        print(f"\n{'='*80}")
        print("STEP 2: NETWORK CONSTRUCTION")
        print(f"{'='*80}")

        self.network_builder = WindWaterNetworkBuilder(self.dataset)

        network = self.network_builder.build_network(
            turbine_mix=turbine_mix,
            battery_size_kwh=battery_size_kwh,
            water_tank_capacity_m3=water_tank_m3,
            water_tank_elevation_m=water_tank_elevation_m
        )

        # Step 3: Optimize
        print(f"\n{'='*80}")
        print("STEP 3: OPTIMIZATION")
        print(f"{'='*80}")

        optimization_results = self.network_builder.optimize(solver=solver)

        # Step 4: Calculate carbon revenue
        print(f"\n{'='*80}")
        print("STEP 4: CARBON MARKET ANALYSIS")
        print(f"{'='*80}")

        carbon_results = self._calculate_carbon_revenue(
            turbine_mix,
            hours
        )

        # Compile complete results
        self.results = {
            'configuration': {
                'turbine_mix': turbine_mix,
                'battery_kwh': battery_size_kwh,
                'water_tank_m3': water_tank_m3,
                'water_tank_elevation_m': water_tank_elevation_m,
                'hours': hours,
                'solver': solver
            },
            'optimization': optimization_results,
            'carbon': carbon_results,
            'dataset': {
                'wind_mean_ms': self.dataset['wind']['wind_speed_ms'].mean(),
                'dust_mean_ugm3': self.dataset['dust']['pm10_ugm3'].mean(),
                'temp_mean_c': self.dataset['temperature']['temperature_c'].mean(),
                'water_demand_total_m3': self.dataset['water_demand']['total_m3h'].sum()
            }
        }

        # Step 5: Print summary
        self._print_summary()

        # Step 6: Export results
        if export:
            self._export_results()

        print(f"\n{'='*80}")
        print("✅ OPTIMIZATION COMPLETE!")
        print(f"{'='*80}")

        return self.results

    def _calculate_carbon_revenue(self, turbine_mix: dict, hours: int) -> dict:
        """Calculate carbon credits and revenue"""

        # Calculate annual energy generation
        turbines = WindTurbineModels()
        wind_speeds = self.dataset['wind']['wind_speed_ms'].values
        dust_pm10 = self.dataset['dust']['pm10_ugm3'].values
        temperatures = self.dataset['temperature']['temperature_c'].values

        total_annual_energy = 0

        for turbine_type, n_turbines in turbine_mix.items():
            if n_turbines == 0:
                continue

            # Calculate energy for this turbine type
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
        co2_avoided_tons = self.carbon_market.calculate_avoided_emissions(
            annual_energy_kwh,
            'diesel_generator'
        )

        # Calculate water co-benefit
        annual_water = self.dataset['water_demand']['total_m3h'].sum()
        if hours < 8760:
            annual_water = annual_water * (8760 / hours)

        co2_water_benefit = self.carbon_market.calculate_water_carbon_benefit(
            annual_water,
            'diesel_water_pump'
        )

        total_co2_avoided = co2_avoided_tons + co2_water_benefit

        # Optimize carbon market tier
        tier_optimization = self.carbon_market.optimize_tier_selection(
            total_co2_avoided,
            water_access_improvement=True
        )

        print(f"\nCarbon Impact:")
        print(f"   Annual energy: {annual_energy_kwh:,.0f} kWh")
        print(f"   CO2 from energy: {co2_avoided_tons:,.0f} tons")
        print(f"   CO2 from water: {co2_water_benefit:,.0f} tons")
        print(f"   TOTAL CO2 avoided: {total_co2_avoided:,.0f} tons/year")

        print(f"\nOptimal Carbon Market Tier: {tier_optimization['optimal_tier']}")
        print(f"   Annual revenue: ${tier_optimization['optimal_tier_data']['net_revenue']:,.0f}")

        return {
            'annual_energy_kwh': annual_energy_kwh,
            'co2_avoided_tons': total_co2_avoided,
            'co2_from_energy': co2_avoided_tons,
            'co2_from_water': co2_water_benefit,
            'optimal_tier': tier_optimization['optimal_tier'],
            'carbon_revenue_annual': tier_optimization['optimal_tier_data']['net_revenue'],
            'tier_comparison': tier_optimization['comparison_table'].to_dict()
        }

    def _print_summary(self):
        """Print comprehensive results summary"""

        print(f"\n{'='*80}")
        print("RESULTS SUMMARY")
        print(f"{'='*80}")

        config = self.results['configuration']
        carbon = self.results['carbon']

        print(f"\nConfiguration:")
        print(f"   Turbines:")
        for turbine_type, count in config['turbine_mix'].items():
            print(f"      {turbine_type}: {count} units")
        print(f"   Battery: {config['battery_kwh']} kWh")
        print(f"   Water tank: {config['water_tank_m3']} m³ at {config['water_tank_elevation_m']}m")

        print(f"\nEnergy & Environment:")
        print(f"   Annual generation: {carbon['annual_energy_kwh']:,.0f} kWh")
        print(f"   CO2 avoided: {carbon['co2_avoided_tons']:,.0f} tons/year")
        print(f"   Carbon market tier: {carbon['optimal_tier']}")
        print(f"   Annual carbon revenue: ${carbon['carbon_revenue_annual']:,.0f}")

        print(f"\nData Characteristics:")
        data = self.results['dataset']
        print(f"   Wind speed (avg): {data['wind_mean_ms']:.2f} m/s")
        print(f"   Dust PM10 (avg): {data['dust_mean_ugm3']:.0f} μg/m³")
        print(f"   Temperature (avg): {data['temp_mean_c']:.1f}°C")
        print(f"   Water demand: {data['water_demand_total_m3']:,.0f} m³")

    def _export_results(self):
        """Export results to files"""

        # Create output directory in project folder
        project_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(project_dir, 'results')
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n{'='*80}")
        print("EXPORTING RESULTS")
        print(f"{'='*80}")

        # Export summary JSON
        summary = {
            'configuration': self.results['configuration'],
            'carbon': {
                'annual_energy_kwh': self.results['carbon']['annual_energy_kwh'],
                'co2_avoided_tons': self.results['carbon']['co2_avoided_tons'],
                'optimal_tier': self.results['carbon']['optimal_tier'],
                'carbon_revenue_annual': self.results['carbon']['carbon_revenue_annual']
            },
            'dataset': self.results['dataset'],
            'timestamp': datetime.now().isoformat()
        }

        with open(f"{output_dir}/summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"   ✓ Saved summary.json")

        # Export data CSVs
        data_dir = f"{output_dir}/data"
        os.makedirs(data_dir, exist_ok=True)
        self.data_generator.export_to_csv(self.dataset, data_dir)
        print(f"   ✓ Saved data CSVs")

        # Export network results
        if self.network_builder and self.network_builder.network:
            network_dir = f"{output_dir}/network_results"
            os.makedirs(network_dir, exist_ok=True)
            self.network_builder.network.export_to_csv_folder(network_dir)
            print(f"   ✓ Saved network results")

        # Create comprehensive visualizations
        print(f"\n{'='*80}")
        print("CREATING VISUALIZATIONS")
        print(f"{'='*80}")

        visualizer = NexusVisualizer(
            dataset=self.dataset,
            network=self.network_builder.network,
            results=self.results,
            output_dir=f"{output_dir}/plots"
        )
        visualizer.create_all_plots()

        # Create carbon emissions visualizations
        print(f"\n{'='*80}")
        print("CREATING CARBON EMISSIONS VISUALIZATIONS")
        print(f"{'='*80}")

        carbon_visualizer = CarbonEmissionsVisualizer(
            results=self.results,
            carbon_model=self.carbon_market,
            output_dir=f"{output_dir}/carbon_plots"
        )
        carbon_visualizer.create_all_plots(
            self.network_builder.network,
            self.results['carbon']['co2_avoided_tons']
        )

        print(f"\n✅ All results exported to: {output_dir}")

    def run_scenario_comparison(self, scenarios: list) -> dict:
        """
        Run multiple scenarios and compare

        Args:
            scenarios: List of scenario dictionaries

        Returns:
            Comparison results
        """

        print(f"\n{'='*80}")
        print("SCENARIO COMPARISON")
        print(f"{'='*80}")

        comparison_results = []

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'─'*80}")
            print(f"Scenario {i}: {scenario.get('name', f'Scenario_{i}')}")
            print(f"{'─'*80}")

            result = self.run_optimization(
                hours=scenario.get('hours', 168),
                turbine_mix=scenario.get('turbine_mix'),
                battery_size_kwh=scenario.get('battery_kwh', 500),
                water_tank_m3=scenario.get('water_tank_m3', 1000),
                solver=scenario.get('solver', 'highs'),
                export=False
            )

            comparison_results.append({
                'scenario_name': scenario.get('name', f'Scenario_{i}'),
                'configuration': result['configuration'],
                'carbon_revenue': result['carbon']['carbon_revenue_annual'],
                'co2_avoided': result['carbon']['co2_avoided_tons'],
                'annual_energy': result['carbon']['annual_energy_kwh']
            })

        # Print comparison
        print(f"\n{'='*80}")
        print("SCENARIO COMPARISON SUMMARY")
        print(f"{'='*80}")

        for res in comparison_results:
            print(f"\n{res['scenario_name']}:")
            print(f"   Annual energy: {res['annual_energy']:,.0f} kWh")
            print(f"   CO2 avoided: {res['co2_avoided']:,.0f} tons")
            print(f"   Carbon revenue: ${res['carbon_revenue']:,.0f}")

        return comparison_results


# Main execution
if __name__ == "__main__":
    import numpy as np

    # Create optimizer
    optimizer = SaravanWindWaterOptimizer(random_seed=42)

    # Run single optimization
    results = optimizer.run_optimization(
        hours=168,  # 1 week
        turbine_mix={
            'HAWT': 2,
            'VAWT': 1,
            'Bladeless': 5
        },
        battery_size_kwh=500,
        water_tank_m3=1000,
        water_tank_elevation_m=25,
        solver='highs',
        export=True
    )

    print(f"\n{'='*80}")
    print("✅ SARAVAN WIND-WATER NEXUS OPTIMIZATION COMPLETE!")
    print(f"{'='*80}")
    print(f"\nResults saved to ./saravan_wind_water_nexus/results/")
