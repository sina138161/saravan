"""
BI-LEVEL Optimization Comparison Plots

مقایسه ظرفیت‌های بهینه و اقتصاد بین سناریوهای مختلف
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict
import json

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class BiLevelComparison:
    """
    مقایسه نتایج BI-LEVEL بین سناریوهای مختلف

    این کلاس پلات‌های مقایسه‌ای برای:
    - ظرفیت‌های بهینه هر تکنولوژی
    - اقتصاد 30 ساله (NPV, LCOE, CAPEX, OPEX)
    - عملکرد (renewable fraction, emissions)
    """

    def __init__(self, results_base_dir: Path, scenario_ids: List[str]):
        """
        Initialize comparison

        Args:
            results_base_dir: پوشه اصلی نتایج
            scenario_ids: لیست scenario IDs برای مقایسه
        """
        self.results_base_dir = Path(results_base_dir)
        self.scenario_ids = scenario_ids
        self.output_dir = self.results_base_dir / 'scenario_comparison'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load all results
        self.scenario_data = {}
        self._load_all_results()

    def _load_all_results(self):
        """بارگذاری نتایج همه سناریوها"""
        print("\n📊 Loading BI-LEVEL results...")

        for sid in self.scenario_ids:
            bilevel_dir = self.results_base_dir / f'bilevel_{sid}'
            level1_file = bilevel_dir / 'level1_results' / 'capacity_results.json'

            if not level1_file.exists():
                print(f"  ⚠ No BI-LEVEL results for {sid}")
                continue

            with open(level1_file, 'r') as f:
                data = json.load(f)

            self.scenario_data[sid] = data
            print(f"  ✓ Loaded {sid}: {data['scenario']['name']}")

        print(f"\n  Total scenarios loaded: {len(self.scenario_data)}")

    def create_all_comparison_plots(self):
        """ایجاد همه پلات‌های مقایسه"""
        if len(self.scenario_data) < 2:
            print("\n⚠ Need at least 2 scenarios for comparison")
            return

        print("\n" + "="*70)
        print("CREATING BI-LEVEL COMPARISON PLOTS")
        print("="*70 + "\n")

        print("📊 1. Optimal capacities comparison...")
        self.plot_optimal_capacities()

        print("💰 2. Economics comparison (30-year)...")
        self.plot_economics_comparison()

        print("⚡ 3. Technology mix comparison...")
        self.plot_technology_mix()

        print("🌍 4. Environmental performance...")
        self.plot_environmental_comparison()

        print("📈 5. Multi-criteria radar...")
        self.plot_radar_comparison()

        print("💵 6. Investment breakdown...")
        self.plot_investment_breakdown()

        print(f"\n✅ All BI-LEVEL comparison plots saved to: {self.output_dir}/")
        print("="*70 + "\n")

    def plot_optimal_capacities(self):
        """مقایسه ظرفیت‌های بهینه"""

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        scenarios = list(self.scenario_data.keys())
        scenario_names = [self.scenario_data[s]['scenario']['name'] for s in scenarios]

        # 1. Wind capacity
        wind_caps = [self.scenario_data[s]['optimal_capacities'].get('wind_total_kw', 0)
                     for s in scenarios]

        ax1 = axes[0, 0]
        bars1 = ax1.bar(range(len(scenarios)), wind_caps, color='#2E86AB', alpha=0.7)
        ax1.set_xlabel('Scenario', fontsize=12)
        ax1.set_ylabel('Capacity (kW)', fontsize=12)
        ax1.set_title('Optimal Wind Capacity', fontsize=14, fontweight='bold')
        ax1.set_xticks(range(len(scenarios)))
        ax1.set_xticklabels(scenarios, rotation=0)
        ax1.grid(True, alpha=0.3, axis='y')

        # Add values on bars
        for i, (bar, val) in enumerate(zip(bars1, wind_caps)):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=10)

        # 2. Battery capacity
        battery_caps = [self.scenario_data[s]['optimal_capacities'].get('battery_kwh', 0)
                        for s in scenarios]

        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(scenarios)), battery_caps, color='#C73E1D', alpha=0.7)
        ax2.set_xlabel('Scenario', fontsize=12)
        ax2.set_ylabel('Capacity (kWh)', fontsize=12)
        ax2.set_title('Optimal Battery Capacity', fontsize=14, fontweight='bold')
        ax2.set_xticks(range(len(scenarios)))
        ax2.set_xticklabels(scenarios, rotation=0)
        ax2.grid(True, alpha=0.3, axis='y')

        for i, (bar, val) in enumerate(zip(bars2, battery_caps)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=10)

        # 3. Gas turbine capacity
        gas_caps = [self.scenario_data[s]['optimal_capacities'].get('gas_turbine_kw', 0)
                    for s in scenarios]

        ax3 = axes[1, 0]
        bars3 = ax3.bar(range(len(scenarios)), gas_caps, color='#A23B72', alpha=0.7)
        ax3.set_xlabel('Scenario', fontsize=12)
        ax3.set_ylabel('Capacity (kW)', fontsize=12)
        ax3.set_title('Optimal Gas Turbine Capacity', fontsize=14, fontweight='bold')
        ax3.set_xticks(range(len(scenarios)))
        ax3.set_xticklabels(scenarios, rotation=0)
        ax3.grid(True, alpha=0.3, axis='y')

        for i, (bar, val) in enumerate(zip(bars3, gas_caps)):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=10)

        # 4. Water tank capacity
        water_caps = [self.scenario_data[s]['optimal_capacities'].get('water_tank_m3', 0)
                      for s in scenarios]

        ax4 = axes[1, 1]
        bars4 = ax4.bar(range(len(scenarios)), water_caps, color='#17becf', alpha=0.7)
        ax4.set_xlabel('Scenario', fontsize=12)
        ax4.set_ylabel('Capacity (m³)', fontsize=12)
        ax4.set_title('Optimal Water Tank Capacity', fontsize=14, fontweight='bold')
        ax4.set_xticks(range(len(scenarios)))
        ax4.set_xticklabels(scenarios, rotation=0)
        ax4.grid(True, alpha=0.3, axis='y')

        for i, (bar, val) in enumerate(zip(bars4, water_caps)):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/bilevel_optimal_capacities.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_economics_comparison(self):
        """مقایسه اقتصادی 30 ساله"""

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        scenarios = list(self.scenario_data.keys())
        x_pos = np.arange(len(scenarios))

        # 1. Total CAPEX
        capex_values = [self.scenario_data[s]['economics']['total_capex_usd'] / 1e6
                        for s in scenarios]

        bars1 = ax1.bar(x_pos, capex_values, color='#F18F01', alpha=0.7)
        ax1.set_xlabel('Scenario', fontsize=12)
        ax1.set_ylabel('CAPEX (Million $)', fontsize=12)
        ax1.set_title('Total Capital Investment', fontsize=14, fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(scenarios)
        ax1.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars1, capex_values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'${val:.2f}M', ha='center', va='bottom', fontsize=9)

        # 2. 30-Year NPV
        npv_values = [self.scenario_data[s]['economics']['total_npv_30_years_usd'] / 1e6
                      for s in scenarios]

        bars2 = ax2.bar(x_pos, npv_values, color='#6A994E', alpha=0.7)
        ax2.set_xlabel('Scenario', fontsize=12)
        ax2.set_ylabel('NPV (Million $)', fontsize=12)
        ax2.set_title('30-Year Net Present Value', fontsize=14, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(scenarios)
        ax2.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars2, npv_values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'${val:.2f}M', ha='center', va='bottom', fontsize=9)

        # 3. LCOE
        lcoe_values = [self.scenario_data[s]['economics']['lcoe_usd_per_mwh']
                       for s in scenarios]

        bars3 = ax3.bar(x_pos, lcoe_values, color='#2E86AB', alpha=0.7)
        ax3.set_xlabel('Scenario', fontsize=12)
        ax3.set_ylabel('LCOE ($/MWh)', fontsize=12)
        ax3.set_title('Levelized Cost of Energy', fontsize=14, fontweight='bold')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(scenarios)
        ax3.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars3, lcoe_values):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                    f'${val:.1f}', ha='center', va='bottom', fontsize=9)

        # 4. Annual OPEX
        opex_values = [self.scenario_data[s]['economics']['annual_opex_usd'] / 1e3
                       for s in scenarios]

        bars4 = ax4.bar(x_pos, opex_values, color='#A23B72', alpha=0.7)
        ax4.set_xlabel('Scenario', fontsize=12)
        ax4.set_ylabel('Annual OPEX (Thousand $)', fontsize=12)
        ax4.set_title('Annual Operating Expenditure', fontsize=14, fontweight='bold')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(scenarios)
        ax4.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars4, opex_values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                    f'${val:.0f}K', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/bilevel_economics_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_technology_mix(self):
        """مقایسه ترکیب تکنولوژی‌ها"""

        scenarios = list(self.scenario_data.keys())

        # Collect data
        wind_caps = []
        battery_caps = []
        gas_caps = []
        biogas_caps = []

        for s in scenarios:
            caps = self.scenario_data[s]['optimal_capacities']
            wind_caps.append(caps.get('wind_total_kw', 0))
            battery_caps.append(caps.get('battery_kwh', 0) / 10)  # Scale for visibility
            gas_caps.append(caps.get('gas_turbine_kw', 0))
            biogas_caps.append(caps.get('biogas_generator_kw', 0))

        # Create stacked bar
        fig, ax = plt.subplots(figsize=(14, 8))

        x_pos = np.arange(len(scenarios))
        width = 0.6

        # Note: Battery scaled by /10 for visualization
        p1 = ax.bar(x_pos, wind_caps, width, label='Wind', color='#2E86AB', alpha=0.8)
        p2 = ax.bar(x_pos, battery_caps, width, bottom=wind_caps,
                    label='Battery (×0.1)', color='#C73E1D', alpha=0.8)
        p3 = ax.bar(x_pos, gas_caps, width,
                    bottom=np.array(wind_caps) + np.array(battery_caps),
                    label='Gas Turbine', color='#A23B72', alpha=0.8)
        p4 = ax.bar(x_pos, biogas_caps, width,
                    bottom=np.array(wind_caps) + np.array(battery_caps) + np.array(gas_caps),
                    label='Biogas', color='#6A994E', alpha=0.8)

        ax.set_xlabel('Scenario', fontsize=12)
        ax.set_ylabel('Capacity (kW or kWh×0.1)', fontsize=12)
        ax.set_title('Optimal Technology Mix Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(scenarios)
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/bilevel_technology_mix.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_environmental_comparison(self):
        """مقایسه عملکرد زیست‌محیطی"""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        scenarios = list(self.scenario_data.keys())
        x_pos = np.arange(len(scenarios))

        # 1. Renewable fraction
        renewable_pcts = [self.scenario_data[s]['operations']['renewable_fraction_pct']
                          for s in scenarios]

        bars1 = ax1.bar(x_pos, renewable_pcts, color='#6A994E', alpha=0.7)
        ax1.set_xlabel('Scenario', fontsize=12)
        ax1.set_ylabel('Renewable Fraction (%)', fontsize=12)
        ax1.set_title('Renewable Energy Fraction', fontsize=14, fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(scenarios)
        ax1.set_ylim([0, 100])
        ax1.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars1, renewable_pcts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=10)

        # 2. CO2 emissions
        co2_emissions = [self.scenario_data[s]['emissions']['total_co2_tons']
                         for s in scenarios]

        bars2 = ax2.bar(x_pos, co2_emissions, color='#C73E1D', alpha=0.7)
        ax2.set_xlabel('Scenario', fontsize=12)
        ax2.set_ylabel('CO₂ Emissions (tons/year)', fontsize=12)
        ax2.set_title('Annual CO₂ Emissions', fontsize=14, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(scenarios)
        ax2.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars2, co2_emissions):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/bilevel_environmental_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_radar_comparison(self):
        """نمودار رادار چند معیاره"""

        scenarios = list(self.scenario_data.keys())

        # Normalize metrics to 0-100 scale
        metrics = {
            'Renewable\nFraction': [],
            'Low\nLCOE': [],
            'Low\nCAPEX': [],
            'Low\nEmissions': [],
            'High\nWind': []
        }

        # Collect raw values
        renewable_vals = [self.scenario_data[s]['operations']['renewable_fraction_pct']
                          for s in scenarios]
        lcoe_vals = [self.scenario_data[s]['economics']['lcoe_usd_per_mwh']
                     for s in scenarios]
        capex_vals = [self.scenario_data[s]['economics']['total_capex_usd']
                      for s in scenarios]
        co2_vals = [self.scenario_data[s]['emissions']['total_co2_tons']
                    for s in scenarios]
        wind_vals = [self.scenario_data[s]['optimal_capacities'].get('wind_total_kw', 0)
                     for s in scenarios]

        # Normalize (higher is better)
        for s_idx in range(len(scenarios)):
            metrics['Renewable\nFraction'].append(renewable_vals[s_idx])

            # Invert LCOE (lower is better → higher score)
            metrics['Low\nLCOE'].append(100 * (1 - (lcoe_vals[s_idx] - min(lcoe_vals)) /
                                               (max(lcoe_vals) - min(lcoe_vals) + 0.01)))

            # Invert CAPEX
            metrics['Low\nCAPEX'].append(100 * (1 - (capex_vals[s_idx] - min(capex_vals)) /
                                                (max(capex_vals) - min(capex_vals) + 0.01)))

            # Invert CO2
            metrics['Low\nEmissions'].append(100 * (1 - (co2_vals[s_idx] - min(co2_vals)) /
                                                    (max(co2_vals) - min(co2_vals) + 0.01)))

            # Wind capacity (normalized)
            metrics['High\nWind'].append(100 * (wind_vals[s_idx] - min(wind_vals)) /
                                         (max(wind_vals) - min(wind_vals) + 0.01))

        # Plot radar
        labels = list(metrics.keys())
        num_vars = len(labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        colors = plt.cm.tab10(np.linspace(0, 1, len(scenarios)))

        for s_idx, s in enumerate(scenarios):
            values = [metrics[label][s_idx] for label in labels]
            values += values[:1]  # Complete the circle

            ax.plot(angles, values, 'o-', linewidth=2, label=s, color=colors[s_idx])
            ax.fill(angles, values, alpha=0.15, color=colors[s_idx])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], size=9)
        ax.set_title('Multi-Criteria Comparison\n(BI-LEVEL Optimization)',
                     size=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        ax.grid(True)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/bilevel_radar_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_investment_breakdown(self):
        """تجزیه سرمایه‌گذاری به تفکیک تکنولوژی"""

        scenarios = list(self.scenario_data.keys())

        # این نیاز به CAPEX تفکیک شده دارد - فعلاً placeholder
        # در آینده می‌توان از bi_level_config استفاده کرد

        fig, ax = plt.subplots(figsize=(14, 8))

        # فعلاً فقط total CAPEX را نشان می‌دهیم
        total_capex = [self.scenario_data[s]['economics']['total_capex_usd'] / 1e6
                       for s in scenarios]

        x_pos = np.arange(len(scenarios))
        bars = ax.bar(x_pos, total_capex, color='#F18F01', alpha=0.7, width=0.6)

        ax.set_xlabel('Scenario', fontsize=12)
        ax.set_ylabel('Total Investment (Million $)', fontsize=12)
        ax.set_title('Total Capital Investment Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(scenarios)
        ax.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars, total_capex):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'${val:.2f}M', ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/bilevel_investment_breakdown.png', dpi=300, bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    print("BI-LEVEL Comparison Plots Module")
    print("Use BiLevelComparison class to compare scenarios")
