"""
Level 1 Results Visualization
Capacity Planning and Investment Analysis (30-year)
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict
import json

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class Level1Visualizer:
    """
    تجسم نتایج Level 1: برنامه‌ریزی ظرفیت

    نمایش:
    - ظرفیت بهینه هر تکنولوژی
    - تجزیه بودجه (CAPEX breakdown)
    - اقتصاد 30 ساله (NPV, LCOE, ROI)
    - بازگشت سرمایه
    """

    def __init__(self, results: Dict, output_dir: Path):
        """
        Initialize Level 1 visualizer

        Args:
            results: دیکشنری نتایج از BiLevelOptimizer
            output_dir: پوشه خروجی برای ذخیره پلات‌ها
        """
        self.results = results
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.figsize = (14, 10)
        self.dpi = 300

    def create_all_plots(self):
        """ایجاد همه پلات‌های Level 1"""

        print(f"\n{'='*70}")
        print("CREATING LEVEL 1 (CAPACITY PLANNING) VISUALIZATIONS")
        print(f"{'='*70}\n")

        print("📊 1. Optimal capacity breakdown...")
        self.plot_capacity_breakdown()

        print("💰 2. Investment breakdown (CAPEX)...")
        self.plot_capex_breakdown()

        print("📈 3. Economics summary (30-year)...")
        self.plot_economics_summary()

        print("💵 4. Cash flow analysis...")
        self.plot_cashflow_analysis()

        print(f"\n✅ Level 1 plots saved to: {self.output_dir}/")

    def plot_capacity_breakdown(self):
        """نمودار ظرفیت بهینه هر تکنولوژی"""

        caps = self.results['optimal_capacities']

        # Prepare data
        tech_names = []
        tech_values = []
        tech_units = []
        tech_colors = []

        if 'wind_total_kw' in caps and caps['wind_total_kw'] > 0:
            tech_names.append('Wind\nTurbines')
            tech_values.append(caps['wind_total_kw'])
            tech_units.append('kW')
            tech_colors.append('#2E86AB')

        if 'battery_kwh' in caps and caps['battery_kwh'] > 0:
            tech_names.append('Battery\nStorage')
            tech_values.append(caps['battery_kwh'])
            tech_units.append('kWh')
            tech_colors.append('#C73E1D')

        if 'gas_turbine_kw' in caps and caps['gas_turbine_kw'] > 0:
            tech_names.append('Gas\nTurbine')
            tech_values.append(caps['gas_turbine_kw'])
            tech_units.append('kW')
            tech_colors.append('#A23B72')

        if 'gas_boiler_kw' in caps and caps['gas_boiler_kw'] > 0:
            tech_names.append('Gas\nBoiler')
            tech_values.append(caps['gas_boiler_kw'])
            tech_units.append('kW')
            tech_colors.append('#F18F01')

        if 'biogas_generator_kw' in caps and caps['biogas_generator_kw'] > 0:
            tech_names.append('Biogas\nGenerator')
            tech_values.append(caps['biogas_generator_kw'])
            tech_units.append('kW')
            tech_colors.append('#6A994E')

        if 'water_tank_m3' in caps and caps['water_tank_m3'] > 0:
            tech_names.append('Water\nTank')
            tech_values.append(caps['water_tank_m3'])
            tech_units.append('m³')
            tech_colors.append('#17becf')

        if not tech_names:
            print("  ⚠ No capacity data available")
            return

        # Create plot
        fig, ax = plt.subplots(figsize=self.figsize)

        bars = ax.bar(range(len(tech_names)), tech_values, color=tech_colors, alpha=0.8, width=0.6)

        ax.set_xlabel('Technology', fontsize=13, fontweight='bold')
        ax.set_ylabel('Optimal Capacity', fontsize=13, fontweight='bold')
        ax.set_title(f'Optimal Capacity for Each Technology\n{self.results["scenario"]["name"]}',
                     fontsize=15, fontweight='bold')
        ax.set_xticks(range(len(tech_names)))
        ax.set_xticklabels(tech_names, fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')

        # Add values and units on bars
        for i, (bar, val, unit) in enumerate(zip(bars, tech_values, tech_units)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + max(tech_values)*0.02,
                    f'{val:.1f} {unit}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/capacity_breakdown.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_capex_breakdown(self):
        """تجزیه CAPEX به تفکیک تکنولوژی"""

        # این نیاز به محاسبه CAPEX هر تکنولوژی دارد
        # از bi_level_config استفاده می‌کنیم

        from bi_level_config import BI_LEVEL_CONFIG
        cfg = BI_LEVEL_CONFIG

        caps = self.results['optimal_capacities']

        tech_names = []
        capex_values = []
        tech_colors = []

        if 'wind_total_kw' in caps and caps['wind_total_kw'] > 0:
            tech_names.append('Wind')
            capex_values.append(caps['wind_total_kw'] * cfg.hawt_capex_usd_per_kw / 1e6)
            tech_colors.append('#2E86AB')

        if 'battery_kwh' in caps and caps['battery_kwh'] > 0:
            tech_names.append('Battery')
            capex_values.append(caps['battery_kwh'] * cfg.battery_capex_usd_per_kwh / 1e6)
            tech_colors.append('#C73E1D')

        if 'gas_turbine_kw' in caps and caps['gas_turbine_kw'] > 0:
            tech_names.append('Gas Turbine')
            capex_values.append(caps['gas_turbine_kw'] * cfg.gas_turbine_capex_usd_per_kw / 1e6)
            tech_colors.append('#A23B72')

        if 'gas_boiler_kw' in caps and caps['gas_boiler_kw'] > 0:
            tech_names.append('Gas Boiler')
            capex_values.append(caps['gas_boiler_kw'] * cfg.gas_boiler_capex_usd_per_kw / 1e6)
            tech_colors.append('#F18F01')

        if 'biogas_generator_kw' in caps and caps['biogas_generator_kw'] > 0:
            tech_names.append('Biogas')
            capex_values.append(caps['biogas_generator_kw'] * cfg.biogas_generator_capex_usd_per_kw / 1e6)
            tech_colors.append('#6A994E')

        if 'water_tank_m3' in caps and caps['water_tank_m3'] > 0:
            tech_names.append('Water Tank')
            capex_values.append(caps['water_tank_m3'] * cfg.water_tank_capex_usd_per_m3 / 1e6)
            tech_colors.append('#17becf')

        if not tech_names:
            print("  ⚠ No CAPEX data available")
            return

        # Create pie chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

        # Pie chart
        wedges, texts, autotexts = ax1.pie(capex_values, labels=tech_names, autopct='%1.1f%%',
                                            colors=tech_colors, startangle=90,
                                            textprops={'fontsize': 11})
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax1.set_title('CAPEX Breakdown by Technology', fontsize=14, fontweight='bold')

        # Bar chart
        bars = ax2.barh(range(len(tech_names)), capex_values, color=tech_colors, alpha=0.8)
        ax2.set_yticks(range(len(tech_names)))
        ax2.set_yticklabels(tech_names, fontsize=11)
        ax2.set_xlabel('Investment (Million $)', fontsize=12, fontweight='bold')
        ax2.set_title('CAPEX by Technology', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')

        # Add values
        for i, (bar, val) in enumerate(zip(bars, capex_values)):
            ax2.text(val + max(capex_values)*0.02, bar.get_y() + bar.get_height()/2,
                    f'${val:.2f}M',
                    ha='left', va='center', fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/capex_breakdown.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_economics_summary(self):
        """خلاصه اقتصادی 30 ساله"""

        econ = self.results['economics']

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Total costs
        total_capex = econ['total_capex_usd'] / 1e6
        npv_opex_30y = econ['npv_opex_30_years_usd'] / 1e6
        total_npv = econ['total_npv_30_years_usd'] / 1e6

        categories = ['CAPEX\n(Initial)', 'OPEX\n(30-year NPV)', 'Total NPV\n(30-year)']
        values = [total_capex, npv_opex_30y, total_npv]
        colors = ['#F18F01', '#A23B72', '#C73E1D']

        bars1 = ax1.bar(range(len(categories)), values, color=colors, alpha=0.8, width=0.6)
        ax1.set_ylabel('Cost (Million $)', fontsize=12, fontweight='bold')
        ax1.set_title('Cost Breakdown (30-year)', fontsize=14, fontweight='bold')
        ax1.set_xticks(range(len(categories)))
        ax1.set_xticklabels(categories, fontsize=11)
        ax1.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars1, values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                    f'${val:.2f}M',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 2. LCOE
        lcoe = econ['lcoe_usd_per_mwh']

        ax2.bar([0], [lcoe], color='#2E86AB', alpha=0.8, width=0.5)
        ax2.set_ylabel('LCOE ($/MWh)', fontsize=12, fontweight='bold')
        ax2.set_title('Levelized Cost of Energy', fontsize=14, fontweight='bold')
        ax2.set_xticks([0])
        ax2.set_xticklabels(['LCOE'], fontsize=11)
        ax2.set_ylim([0, lcoe * 1.3])
        ax2.grid(True, alpha=0.3, axis='y')

        ax2.text(0, lcoe + lcoe*0.05, f'${lcoe:.2f}/MWh',
                ha='center', va='bottom', fontsize=13, fontweight='bold')

        # 3. Annual OPEX
        annual_opex = econ['annual_opex_usd'] / 1e3  # thousands

        ax3.bar([0], [annual_opex], color='#6A994E', alpha=0.8, width=0.5)
        ax3.set_ylabel('Annual OPEX (Thousand $)', fontsize=12, fontweight='bold')
        ax3.set_title('Annual Operating Expenditure', fontsize=14, fontweight='bold')
        ax3.set_xticks([0])
        ax3.set_xticklabels(['Annual OPEX'], fontsize=11)
        ax3.set_ylim([0, annual_opex * 1.3])
        ax3.grid(True, alpha=0.3, axis='y')

        ax3.text(0, annual_opex + annual_opex*0.05, f'${annual_opex:.0f}K/year',
                ha='center', va='bottom', fontsize=13, fontweight='bold')

        # 4. Investment summary text
        ax4.axis('off')

        summary_text = f"""
    📊 INVESTMENT SUMMARY

    Scenario: {self.results['scenario']['name']}

    💰 CAPITAL INVESTMENT (CAPEX):
       ${total_capex:.2f} Million

    📈 30-YEAR NET PRESENT VALUE:
       ${total_npv:.2f} Million

    ⚡ LEVELIZED COST OF ENERGY:
       ${lcoe:.2f} per MWh

    🔄 ANNUAL OPERATING COST:
       ${annual_opex:.0f} Thousand per year

    🌍 RENEWABLE FRACTION:
       {self.results['operations']['renewable_fraction_pct']:.1f}%

    ♻️ ANNUAL CO₂ EMISSIONS:
       {self.results['emissions']['total_co2_tons']:.0f} tons
        """

        ax4.text(0.1, 0.5, summary_text, transform=ax4.transAxes,
                fontsize=12, verticalalignment='center',
                fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/economics_summary.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_cashflow_analysis(self):
        """تحلیل جریان نقدی 30 ساله"""

        econ = self.results['economics']

        # Calculate yearly cash flows
        years = np.arange(0, 31)  # 0 to 30
        discount_rate = 0.08

        # Year 0: CAPEX
        cashflow = np.zeros(31)
        cashflow[0] = -econ['total_capex_usd'] / 1e6  # Negative (outflow)

        # Years 1-30: OPEX
        annual_opex = econ['annual_opex_usd'] / 1e6
        for year in range(1, 31):
            cashflow[year] = -annual_opex  # Negative (outflow)

        # Cumulative NPV
        cumulative_npv = np.zeros(31)
        cumulative_npv[0] = cashflow[0]

        for year in range(1, 31):
            discounted_cashflow = cashflow[year] / ((1 + discount_rate) ** year)
            cumulative_npv[year] = cumulative_npv[year-1] + discounted_cashflow

        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # 1. Annual cash flow
        colors = ['red' if cf < 0 else 'green' for cf in cashflow]
        bars = ax1.bar(years, cashflow, color=colors, alpha=0.6, width=0.8)

        ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('Cash Flow (Million $)', fontsize=12)
        ax1.set_title('Annual Cash Flow (30 years)', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.set_xlim([-1, 31])

        # 2. Cumulative NPV
        ax2.plot(years, cumulative_npv, marker='o', linewidth=2, color='#2E86AB', markersize=4)
        ax2.fill_between(years, cumulative_npv, 0, alpha=0.2, color='#2E86AB')
        ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

        ax2.set_xlabel('Year', fontsize=12)
        ax2.set_ylabel('Cumulative NPV (Million $)', fontsize=12)
        ax2.set_title('Cumulative Net Present Value (8% discount rate)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim([-1, 31])

        # Mark final NPV
        final_npv = cumulative_npv[-1]
        ax2.text(30, final_npv, f'  Final NPV:\n  ${final_npv:.2f}M',
                ha='left', va='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/cashflow_analysis.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    print("Level 1 Visualizer - Capacity Planning Results")
