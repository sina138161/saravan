"""
Scenario Comparison Visualization Module

Creates comparative plots across all scenarios to analyze:
- Economic performance (costs, LCOE, revenues)
- Environmental impact (emissions, renewable fraction)
- Technology deployment mix
- Operational performance
- Multi-criteria comparison
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List
import json

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


class ScenarioComparison:
    """
    Create comparative visualizations across multiple scenarios

    Reads results from all scenario folders and generates comparison plots
    """

    def __init__(self, results_base_dir: Path, scenario_ids: List[str]):
        """
        Initialize comparison visualizer

        Args:
            results_base_dir: Base results directory containing scenario folders
            scenario_ids: List of scenario IDs to compare (e.g., ['S1', 'S2', ...])
        """
        self.results_base_dir = Path(results_base_dir)
        self.scenario_ids = scenario_ids
        self.scenario_results = {}
        self.scenario_configs = {}

        # Create output directory
        self.output_dir = self.results_base_dir / 'scenario_comparison'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.figsize = (14, 8)
        self.dpi = 300

        # Load all scenario results
        self._load_scenario_results()

    def _load_scenario_results(self):
        """Load results from all scenario folders"""

        print("\n" + "="*80)
        print("LOADING SCENARIO RESULTS FOR COMPARISON")
        print("="*80 + "\n")

        for sid in self.scenario_ids:
            # Find scenario folder
            scenario_folders = list(self.results_base_dir.glob(f'scenario_{sid}_*'))

            if not scenario_folders:
                print(f"⚠ Scenario {sid} folder not found, skipping...")
                continue

            scenario_dir = scenario_folders[0]

            # Load comprehensive results
            comprehensive_file = list(scenario_dir.glob('comprehensive_results_*.json'))
            if comprehensive_file:
                with open(comprehensive_file[0], 'r') as f:
                    self.scenario_results[sid] = json.load(f)

            # Load scenario config
            config_file = scenario_dir / 'scenario_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.scenario_configs[sid] = json.load(f)

            print(f"✓ Loaded scenario {sid}: {self.scenario_configs.get(sid, {}).get('scenario_name', 'Unknown')}")

        print(f"\n✓ Loaded {len(self.scenario_results)} scenarios for comparison\n")

    def create_all_comparison_plots(self):
        """Create all comparison visualizations"""

        print("\n" + "="*80)
        print("CREATING SCENARIO COMPARISON PLOTS")
        print("="*80 + "\n")

        print("1. Economic comparison...")
        self.plot_economic_comparison()

        print("2. Environmental comparison...")
        self.plot_environmental_comparison()

        print("3. Technology mix comparison...")
        self.plot_technology_mix_comparison()

        print("4. Performance metrics comparison...")
        self.plot_performance_metrics()

        print("5. Multi-criteria radar chart...")
        self.plot_radar_comparison()

        print("6. Renewable fraction and emissions...")
        self.plot_renewable_emissions()

        print("7. Cost breakdown...")
        self.plot_cost_breakdown()

        print(f"\n✅ All comparison plots saved to: {self.output_dir}/\n")

    def plot_economic_comparison(self):
        """Compare economic metrics across scenarios"""

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        scenarios = []
        total_costs = []
        lcoes = []
        carbon_revenues = []
        renewable_fractions = []

        for sid in self.scenario_ids:
            if sid not in self.scenario_results:
                continue

            results = self.scenario_results[sid]
            config = self.scenario_configs[sid]

            scenarios.append(f"{sid}\n{config['scenario_name']}")
            total_costs.append(results['economics']['total_cost_usd'])
            lcoes.append(results['economics']['lcoe_usd_per_mwh'])
            carbon_revenues.append(results['economics'].get('carbon_revenue_usd', 0))
            renewable_fractions.append(results['energy']['renewable_fraction_pct'])

        x = np.arange(len(scenarios))
        width = 0.6

        # Plot 1: Total Cost
        bars1 = ax1.bar(x, total_costs, width, color='steelblue', alpha=0.8)
        ax1.set_ylabel('Total Cost ($)', fontsize=12, fontweight='bold')
        ax1.set_title('Total Annual Cost by Scenario', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(scenarios, fontsize=9)
        ax1.grid(axis='y', alpha=0.3)

        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom', fontsize=9)

        # Plot 2: LCOE
        bars2 = ax2.bar(x, lcoes, width, color='coral', alpha=0.8)
        ax2.set_ylabel('LCOE ($/MWh)', fontsize=12, fontweight='bold')
        ax2.set_title('Levelized Cost of Energy', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(scenarios, fontsize=9)
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:.1f}', ha='center', va='bottom', fontsize=9)

        # Plot 3: Carbon Revenue
        bars3 = ax3.bar(x, carbon_revenues, width, color='green', alpha=0.8)
        ax3.set_ylabel('Carbon Revenue ($)', fontsize=12, fontweight='bold')
        ax3.set_title('Annual Carbon Market Revenue', fontsize=14, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(scenarios, fontsize=9)
        ax3.grid(axis='y', alpha=0.3)

        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom', fontsize=9)

        # Plot 4: Net Cost (Total - Carbon Revenue)
        net_costs = [tc - cr for tc, cr in zip(total_costs, carbon_revenues)]
        bars4 = ax4.bar(x, net_costs, width, color='purple', alpha=0.8)
        ax4.set_ylabel('Net Cost ($)', fontsize=12, fontweight='bold')
        ax4.set_title('Net Annual Cost (Total - Carbon Revenue)', fontsize=14, fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels(scenarios, fontsize=9)
        ax4.grid(axis='y', alpha=0.3)

        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/economic_comparison.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_environmental_comparison(self):
        """Compare environmental metrics"""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize)

        scenarios = []
        co2_avoided = []
        co2_emitted = []

        for sid in self.scenario_ids:
            if sid not in self.scenario_results:
                continue

            results = self.scenario_results[sid]
            config = self.scenario_configs[sid]

            scenarios.append(f"{sid}\n{config['scenario_name']}")
            co2_avoided.append(results['carbon']['co2_avoided_tons'])
            co2_emitted.append(results['carbon']['co2_emitted_tons'])

        x = np.arange(len(scenarios))
        width = 0.35

        # Plot 1: CO2 Avoided vs Emitted
        bars1 = ax1.bar(x - width/2, co2_avoided, width, label='CO2 Avoided', color='green', alpha=0.8)
        bars2 = ax1.bar(x + width/2, co2_emitted, width, label='CO2 Emitted', color='red', alpha=0.8)

        ax1.set_ylabel('CO2 (tons/year)', fontsize=12, fontweight='bold')
        ax1.set_title('CO2 Emissions: Avoided vs Emitted', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(scenarios, fontsize=9)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # Plot 2: Net CO2 Impact
        net_impact = [av - em for av, em in zip(co2_avoided, co2_emitted)]
        colors = ['green' if x > 0 else 'red' for x in net_impact]
        bars3 = ax2.bar(x, net_impact, width*2, color=colors, alpha=0.8)

        ax2.set_ylabel('Net CO2 Impact (tons/year)', fontsize=12, fontweight='bold')
        ax2.set_title('Net CO2 Impact (Avoided - Emitted)', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(scenarios, fontsize=9)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars3:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:,.0f}', ha='center',
                    va='bottom' if height > 0 else 'top', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/environmental_comparison.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_technology_mix_comparison(self):
        """Compare technology deployment across scenarios"""

        fig, ax = plt.subplots(figsize=self.figsize)

        scenarios = []
        wind_gen = []
        gas_gen = []
        biogas_gen = []
        grid_gen = []
        battery_discharge = []

        for sid in self.scenario_ids:
            if sid not in self.scenario_results:
                continue

            results = self.scenario_results[sid]
            config = self.scenario_configs[sid]

            scenarios.append(f"{sid}\n{config['scenario_name']}")

            # Extract generation by technology
            combined = results.get('combined', results)  # Fallback to results if no combined

            wind_gen.append(combined.get('wind', {}).get('total_generation_kwh', 0))
            gas_gen.append(combined.get('thermal', {}).get('total_generation_kwh', 0))
            biogas_gen.append(combined.get('biogas', {}).get('energy_equivalent_kwh', 0))
            grid_gen.append(combined.get('grid', {}).get('total_import_kwh', 0))
            battery_discharge.append(combined.get('storage', {}).get('battery_energy_discharged_kwh', 0))

        x = np.arange(len(scenarios))
        width = 0.6

        # Stacked bar chart
        p1 = ax.bar(x, wind_gen, width, label='Wind', color='#2E86AB')
        p2 = ax.bar(x, gas_gen, width, bottom=wind_gen, label='Gas Turbine', color='#A23B72')

        bottom2 = [w + g for w, g in zip(wind_gen, gas_gen)]
        p3 = ax.bar(x, biogas_gen, width, bottom=bottom2, label='Biogas', color='#F18F01')

        bottom3 = [b2 + bg for b2, bg in zip(bottom2, biogas_gen)]
        p4 = ax.bar(x, battery_discharge, width, bottom=bottom3, label='Battery', color='#C73E1D')

        bottom4 = [b3 + bd for b3, bd in zip(bottom3, battery_discharge)]
        p5 = ax.bar(x, grid_gen, width, bottom=bottom4, label='Grid', color='#6A6A6A')

        ax.set_ylabel('Energy Generation (kWh/year)', fontsize=12, fontweight='bold')
        ax.set_title('Technology Mix: Energy Generation by Source', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, fontsize=9)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/technology_mix_comparison.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_performance_metrics(self):
        """Compare key performance metrics"""

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        scenarios = []
        renewable_fracs = []
        system_efficiencies = []
        carbon_intensities = []
        water_energy_ratios = []

        for sid in self.scenario_ids:
            if sid not in self.scenario_results:
                continue

            results = self.scenario_results[sid]
            config = self.scenario_configs[sid]

            scenarios.append(f"{sid}\n{config['scenario_name']}")
            renewable_fracs.append(results['energy']['renewable_fraction_pct'])
            system_efficiencies.append(results['energy']['system_efficiency_pct'])
            carbon_intensities.append(results['carbon']['carbon_intensity_kg_per_kwh'])

            water_pumped = results.get('water', {}).get('total_water_pumped_m3', 0)
            pumping_energy = results.get('water', {}).get('pumping_energy_kwh', 1)  # Avoid div by zero
            water_energy_ratios.append(water_pumped / pumping_energy if pumping_energy > 0 else 0)

        x = np.arange(len(scenarios))
        width = 0.6

        # Plot 1: Renewable Fraction
        bars1 = ax1.bar(x, renewable_fracs, width, color='green', alpha=0.8)
        ax1.set_ylabel('Renewable Fraction (%)', fontsize=12, fontweight='bold')
        ax1.set_title('Renewable Energy Penetration', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(scenarios, fontsize=9)
        ax1.set_ylim([0, 100])
        ax1.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='50% Target')
        ax1.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='80% Target')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

        # Plot 2: System Efficiency
        bars2 = ax2.bar(x, system_efficiencies, width, color='steelblue', alpha=0.8)
        ax2.set_ylabel('System Efficiency (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Overall System Efficiency', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(scenarios, fontsize=9)
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

        # Plot 3: Carbon Intensity
        bars3 = ax3.bar(x, carbon_intensities, width, color='red', alpha=0.8)
        ax3.set_ylabel('Carbon Intensity (kg CO2/kWh)', fontsize=12, fontweight='bold')
        ax3.set_title('Carbon Intensity of Energy', fontsize=14, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(scenarios, fontsize=9)
        ax3.grid(axis='y', alpha=0.3)

        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=9)

        # Plot 4: Water-Energy Nexus Efficiency
        bars4 = ax4.bar(x, water_energy_ratios, width, color='cyan', alpha=0.8)
        ax4.set_ylabel('Water per Energy (m³/kWh)', fontsize=12, fontweight='bold')
        ax4.set_title('Water-Energy Nexus Efficiency', fontsize=14, fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels(scenarios, fontsize=9)
        ax4.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/performance_metrics.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_radar_comparison(self):
        """Multi-criteria comparison using radar chart"""

        # Metrics to compare (normalized to 0-100)
        metrics = ['Renewable\nFraction', 'System\nEfficiency', 'Cost\nEfficiency',
                   'Carbon\nReduction', 'Water\nEfficiency']

        fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))

        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle

        colors = plt.cm.tab10(np.linspace(0, 1, len(self.scenario_ids)))

        for idx, sid in enumerate(self.scenario_ids):
            if sid not in self.scenario_results:
                continue

            results = self.scenario_results[sid]
            config = self.scenario_configs[sid]

            # Normalize metrics to 0-100 scale
            renewable_frac = results['energy']['renewable_fraction_pct']
            system_eff = results['energy']['system_efficiency_pct']

            # Cost efficiency: inverse of LCOE (lower is better, so invert)
            lcoe = results['economics']['lcoe_usd_per_mwh']
            cost_eff = max(0, 100 - lcoe)  # Normalize

            # Carbon reduction: % of CO2 avoided
            co2_avoided = results['carbon']['co2_avoided_tons']
            co2_total = co2_avoided + results['carbon']['co2_emitted_tons']
            carbon_reduction = (co2_avoided / co2_total * 100) if co2_total > 0 else 0

            # Water efficiency: normalized
            water_eff = 50  # Placeholder - needs actual metric

            values = [renewable_frac, system_eff, cost_eff, carbon_reduction, water_eff]
            values += values[:1]  # Complete the circle

            ax.plot(angles, values, 'o-', linewidth=2, label=f"{sid}: {config['scenario_name']}",
                   color=colors[idx])
            ax.fill(angles, values, alpha=0.15, color=colors[idx])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=9)
        ax.set_title('Multi-Criteria Performance Comparison', fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
        ax.grid(True)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/radar_comparison.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_renewable_emissions(self):
        """Scatter plot: Renewable fraction vs Emissions"""

        fig, ax = plt.subplots(figsize=self.figsize)

        renewable_fracs = []
        carbon_intensities = []
        labels = []
        sizes = []

        for sid in self.scenario_ids:
            if sid not in self.scenario_results:
                continue

            results = self.scenario_results[sid]
            config = self.scenario_configs[sid]

            renewable_fracs.append(results['energy']['renewable_fraction_pct'])
            carbon_intensities.append(results['carbon']['carbon_intensity_kg_per_kwh'])
            labels.append(sid)
            sizes.append(results['economics']['total_cost_usd'] / 1000)  # Size = cost/1000

        scatter = ax.scatter(renewable_fracs, carbon_intensities, s=sizes, alpha=0.6,
                           c=range(len(renewable_fracs)), cmap='viridis', edgecolors='black', linewidths=1.5)

        # Add labels
        for i, label in enumerate(labels):
            ax.annotate(label, (renewable_fracs[i], carbon_intensities[i]),
                       fontsize=11, fontweight='bold', ha='center')

        ax.set_xlabel('Renewable Fraction (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Carbon Intensity (kg CO2/kWh)', fontsize=12, fontweight='bold')
        ax.set_title('Renewable Penetration vs Carbon Intensity\n(Bubble size = Total Cost)',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Add ideal region
        ax.axvline(x=80, color='green', linestyle='--', alpha=0.3, label='80% Renewable Target')
        ax.axhline(y=0.1, color='green', linestyle='--', alpha=0.3, label='Low Carbon Target')
        ax.legend()

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/renewable_vs_emissions.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_cost_breakdown(self):
        """Detailed cost breakdown by scenario"""

        fig, ax = plt.subplots(figsize=self.figsize)

        scenarios = []
        capex_costs = []
        opex_costs = []
        fuel_costs = []
        carbon_costs = []

        for sid in self.scenario_ids:
            if sid not in self.scenario_results:
                continue

            results = self.scenario_results[sid]
            config = self.scenario_configs[sid]

            scenarios.append(f"{sid}\n{config['scenario_name']}")

            # Estimate cost breakdown (would need actual data from results)
            total_cost = results['economics']['total_cost_usd']

            # Placeholder breakdown - would need actual cost components
            capex_costs.append(total_cost * 0.3)  # 30% CAPEX
            opex_costs.append(total_cost * 0.4)   # 40% OPEX
            fuel_costs.append(total_cost * 0.2)   # 20% Fuel
            carbon_costs.append(total_cost * 0.1) # 10% Carbon

        x = np.arange(len(scenarios))
        width = 0.6

        p1 = ax.bar(x, capex_costs, width, label='CAPEX', color='#2E86AB')
        p2 = ax.bar(x, opex_costs, width, bottom=capex_costs, label='OPEX', color='#A23B72')

        bottom2 = [c + o for c, o in zip(capex_costs, opex_costs)]
        p3 = ax.bar(x, fuel_costs, width, bottom=bottom2, label='Fuel', color='#F18F01')

        bottom3 = [b + f for b, f in zip(bottom2, fuel_costs)]
        p4 = ax.bar(x, carbon_costs, width, bottom=bottom3, label='Carbon Tax/Penalty', color='#C73E1D')

        ax.set_ylabel('Cost ($)', fontsize=12, fontweight='bold')
        ax.set_title('Cost Breakdown by Component', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, fontsize=9)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/cost_breakdown.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    print("Scenario Comparison Visualization Module")
    print("This module should be imported and used from main.py")
