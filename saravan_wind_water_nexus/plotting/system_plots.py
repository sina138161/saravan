"""
System-Level Visualization Module
Simple, practical plots showing total generation by technology category
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from typing import Dict
import os
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class SystemVisualizer:
    """
    Create system-level visualizations showing aggregated results

    Focus on:
    - Total generation by technology type (not individual units)
    - Supply vs demand comparisons
    - Storage operation
    - Water production and usage
    """

    def __init__(self, network, dataset: Dict, results: Dict, output_dir: str = None):
        """
        Initialize system visualizer

        Args:
            network: PyPSA network object
            dataset: Time series data
            results: Optimization results
            output_dir: Output directory for plots
        """
        self.network = network
        self.dataset = dataset
        self.results = results

        # Set output directory
        if output_dir is None:
            from config import config
            self.output_dir = str(config.OUTPUT_DIR / 'system_plots')
        else:
            self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        self.figsize = (14, 8)
        self.dpi = 300

    def create_all_plots(self):
        """Create all system-level plots"""

        print(f"\n{'='*70}")
        print("CREATING SYSTEM-LEVEL VISUALIZATIONS")
        print(f"{'='*70}\n")

        print("📊 1. Electricity generation by technology...")
        self.plot_electricity_generation_by_technology()

        print("⚡ 2. Electricity supply vs demand...")
        self.plot_electricity_supply_demand()

        print("🔋 3. Battery operation...")
        self.plot_battery_operation()

        print("🔥 4. Heat generation by technology...")
        self.plot_heat_generation_by_technology()

        print("💧 5. Water production and usage...")
        self.plot_water_production_usage()

        print("🌾 6. Biogas system operation...")
        self.plot_biogas_operation()

        print("📈 7. Daily average profiles...")
        self.plot_daily_average_profiles()

        print("🎯 8. Technology contribution pie charts...")
        self.plot_technology_contribution()

        print(f"\n✅ All system plots saved to: {self.output_dir}/")
        print(f"   Total plots created: 8\n")

    def _get_timestamps(self):
        """Get timestamps from dataset"""
        return pd.to_datetime(self.dataset['wind']['timestamp'])

    def _format_time_axis(self, ax, timestamps, max_points=168):
        """Format time axis - show subset if too many points"""
        hours = len(timestamps)

        if hours <= 48:  # 2 days
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        elif hours <= 168:  # 1 week
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
        elif hours <= 720:  # 1 month
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=7))
        else:  # 1 year - show monthly
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def plot_electricity_generation_by_technology(self):
        """Plot total electricity generation by technology type (not individual units)"""

        timestamps = self._get_timestamps()
        hours = len(timestamps)

        fig, ax = plt.subplots(figsize=self.figsize)

        # Aggregate wind turbines (all HAWT + all Bladeless)
        wind_cols = [c for c in self.network.generators_t.p.columns if 'Wind_' in c]
        wind_total = self.network.generators_t.p[wind_cols].sum(axis=1).values if wind_cols else np.zeros(hours)

        # Gas microturbine
        gt_cols = [c for c in self.network.generators_t.p.columns if 'Gas_Microturbine' in c]
        gas_total = self.network.generators_t.p[gt_cols].sum(axis=1).values if gt_cols else np.zeros(hours)

        # Biogas generators
        biogas_cols = [c for c in self.network.generators_t.p.columns if 'Biogas' in c]
        biogas_total = self.network.generators_t.p[biogas_cols].sum(axis=1).values if biogas_cols else np.zeros(hours)

        # Grid (if used)
        grid_cols = [c for c in self.network.generators_t.p.columns if 'Grid' in c]
        grid_total = self.network.generators_t.p[grid_cols].sum(axis=1).values if grid_cols else np.zeros(hours)

        # Battery discharge (negative charging = discharge)
        battery_cols = [c for c in self.network.links_t.p0.columns if 'Battery' in c]
        if battery_cols:
            battery_discharge = -np.minimum(0, self.network.links_t.p0[battery_cols].sum(axis=1).values)
        else:
            battery_discharge = np.zeros(hours)

        # Create stacked area plot
        ax.fill_between(timestamps, 0, wind_total, label='Wind (HAWT + Bladeless)', alpha=0.7, color='#2E86AB')
        ax.fill_between(timestamps, wind_total, wind_total + gas_total,
                        label='Gas Microturbine', alpha=0.7, color='#A23B72')
        ax.fill_between(timestamps, wind_total + gas_total,
                        wind_total + gas_total + biogas_total,
                        label='Biogas', alpha=0.7, color='#F18F01')
        ax.fill_between(timestamps, wind_total + gas_total + biogas_total,
                        wind_total + gas_total + biogas_total + battery_discharge,
                        label='Battery Discharge', alpha=0.7, color='#C73E1D')
        ax.fill_between(timestamps, wind_total + gas_total + biogas_total + battery_discharge,
                        wind_total + gas_total + biogas_total + battery_discharge + grid_total,
                        label='Grid', alpha=0.7, color='#6A6A6A')

        # Add demand line
        demand = self.dataset['electricity_demand']['total_kwh'].values
        ax.plot(timestamps, demand, 'k--', linewidth=2, label='Demand', alpha=0.8)

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Power (kW)', fontsize=12)
        ax.set_title('Electricity Generation by Technology Type', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        self._format_time_axis(ax, timestamps)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/electricity_by_technology.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_electricity_supply_demand(self):
        """Plot total electricity supply vs demand"""

        timestamps = self._get_timestamps()
        hours = len(timestamps)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, sharex=True)

        # Total supply
        all_gen_cols = self.network.generators_t.p.columns
        total_supply = self.network.generators_t.p.sum(axis=1).values
        demand = self.dataset['electricity_demand']['total_kwh'].values

        # Plot 1: Supply vs Demand
        ax1.plot(timestamps, total_supply, label='Total Supply', color='#2E86AB', linewidth=2)
        ax1.plot(timestamps, demand, label='Demand', color='#C73E1D', linewidth=2, linestyle='--')
        ax1.fill_between(timestamps, total_supply, demand, where=(total_supply >= demand),
                         alpha=0.3, color='green', label='Surplus')
        ax1.fill_between(timestamps, total_supply, demand, where=(total_supply < demand),
                         alpha=0.3, color='red', label='Deficit')
        ax1.set_ylabel('Power (kW)', fontsize=12)
        ax1.set_title('Electricity Supply vs Demand', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Mismatch (supply - demand)
        mismatch = total_supply - demand
        colors = ['green' if x >= 0 else 'red' for x in mismatch]
        ax2.bar(timestamps, mismatch, color=colors, alpha=0.6, width=1/24)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Surplus/Deficit (kW)', fontsize=12)
        ax2.set_title('Supply-Demand Mismatch', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        self._format_time_axis(ax2, timestamps)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/electricity_supply_demand.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_battery_operation(self):
        """Plot battery state of charge and power flow"""

        timestamps = self._get_timestamps()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, sharex=True)

        # Get battery data
        if 'Battery' in self.network.stores.index:
            soc = self.network.stores_t.e['Battery'].values
            capacity = self.network.stores.loc['Battery', 'e_nom']
            soc_percent = (soc / capacity) * 100

            # Get charge/discharge power from battery charger link
            battery_link_cols = [c for c in self.network.links_t.p0.columns if 'Battery' in c]
            if battery_link_cols:
                power = self.network.links_t.p0[battery_link_cols[0]].values
            else:
                power = np.zeros(len(timestamps))
        else:
            soc_percent = np.zeros(len(timestamps))
            power = np.zeros(len(timestamps))
            capacity = 0

        # Plot 1: State of Charge
        ax1.plot(timestamps, soc_percent, color='#2E86AB', linewidth=2)
        ax1.fill_between(timestamps, 0, soc_percent, alpha=0.3, color='#2E86AB')
        ax1.set_ylabel('State of Charge (%)', fontsize=12)
        ax1.set_title(f'Battery Operation (Capacity: {capacity:.0f} kWh)', fontsize=14, fontweight='bold')
        ax1.set_ylim([0, 100])
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='Low SOC (20%)')
        ax1.axhline(y=80, color='orange', linestyle='--', alpha=0.5, label='High SOC (80%)')
        ax1.legend(loc='upper right', fontsize=9)

        # Plot 2: Charge/Discharge Power
        charge = np.maximum(0, power)
        discharge = np.minimum(0, power)

        ax2.fill_between(timestamps, 0, charge, alpha=0.6, color='green', label='Charging')
        ax2.fill_between(timestamps, 0, discharge, alpha=0.6, color='red', label='Discharging')
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Power (kW)', fontsize=12)
        ax2.set_title('Battery Charge/Discharge Power', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)

        self._format_time_axis(ax2, timestamps)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/battery_operation.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_heat_generation_by_technology(self):
        """Plot heat generation by technology"""

        timestamps = self._get_timestamps()
        hours = len(timestamps)

        fig, ax = plt.subplots(figsize=self.figsize)

        # Heat recovery from gas turbine
        hr_cols = [c for c in self.network.links_t.p1.columns if 'Heat_Recovery' in c]
        heat_recovery = self.network.links_t.p1[hr_cols].sum(axis=1).values if hr_cols else np.zeros(hours)

        # Gas boiler
        boiler_cols = [c for c in self.network.generators_t.p.columns if 'Boiler' in c]
        boiler = self.network.generators_t.p[boiler_cols].sum(axis=1).values if boiler_cols else np.zeros(hours)

        # Biogas heat
        biogas_heat_cols = [c for c in self.network.links_t.p1.columns if 'Biogas_to_Heat' in c]
        biogas_heat = self.network.links_t.p1[biogas_heat_cols].sum(axis=1).values if biogas_heat_cols else np.zeros(hours)

        # Thermal storage discharge
        thermal_discharge = np.zeros(hours)  # Placeholder

        # Stacked area plot
        ax.fill_between(timestamps, 0, heat_recovery, label='Heat Recovery (WHB)', alpha=0.7, color='#F18F01')
        ax.fill_between(timestamps, heat_recovery, heat_recovery + boiler,
                        label='Gas Boiler', alpha=0.7, color='#A23B72')
        ax.fill_between(timestamps, heat_recovery + boiler,
                        heat_recovery + boiler + biogas_heat,
                        label='Biogas Heat', alpha=0.7, color='#6A994E')

        # Add demand line
        demand = self.dataset['heat_demand']['total_kwh_thermal'].values
        ax.plot(timestamps, demand, 'k--', linewidth=2, label='Heat Demand', alpha=0.8)

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Heat Power (kW-thermal)', fontsize=12)
        ax.set_title('Heat Generation by Technology Type', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        self._format_time_axis(ax, timestamps)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/heat_by_technology.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_water_production_usage(self):
        """Plot water production and usage"""

        timestamps = self._get_timestamps()
        hours = len(timestamps)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, sharex=True)

        # Get water tank data if exists
        if 'Water_Tank' in self.network.stores.index:
            tank_volume = self.network.stores_t.e['Water_Tank'].values
            tank_capacity = self.network.stores.loc['Water_Tank', 'e_nom']
        else:
            tank_volume = np.zeros(hours)
            tank_capacity = 0

        # Water demand
        demand = self.dataset['water_demand']['total_m3'].values

        # Plot 1: Tank level
        ax1.plot(timestamps, tank_volume, color='#17becf', linewidth=2)
        ax1.fill_between(timestamps, 0, tank_volume, alpha=0.3, color='#17becf')
        ax1.axhline(y=tank_capacity, color='red', linestyle='--', alpha=0.5, label=f'Capacity ({tank_capacity:.0f} m³)')
        ax1.set_ylabel('Tank Volume (m³)', fontsize=12)
        ax1.set_title(f'Water Tank Level', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Demand
        ax2.plot(timestamps, demand, color='#C73E1D', linewidth=2, label='Water Demand')
        ax2.fill_between(timestamps, 0, demand, alpha=0.3, color='#C73E1D')
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Demand (m³/h)', fontsize=12)
        ax2.set_title('Water Demand', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)

        self._format_time_axis(ax2, timestamps)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/water_production_usage.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_biogas_operation(self):
        """Plot biogas production and usage"""

        timestamps = self._get_timestamps()
        hours = len(timestamps)

        fig, ax = plt.subplots(figsize=self.figsize)

        # Biogas storage if exists
        if 'Biogas_Storage' in self.network.stores.index:
            biogas_stored = self.network.stores_t.e['Biogas_Storage'].values
            capacity = self.network.stores.loc['Biogas_Storage', 'e_nom']
        else:
            biogas_stored = np.zeros(hours)
            capacity = 0

        # Biomass availability
        if 'biomass_availability' in self.dataset:
            biomass_available = self.dataset['biomass_availability']['biomass_ton_h'].values
        else:
            biomass_available = np.zeros(hours)

        ax.plot(timestamps, biogas_stored, color='#6A994E', linewidth=2, label='Biogas Stored')
        ax.fill_between(timestamps, 0, biogas_stored, alpha=0.3, color='#6A994E')

        # Add biomass availability on secondary axis
        ax2 = ax.twinx()
        ax2.plot(timestamps, biomass_available, color='#8B4513', linewidth=1.5,
                linestyle='--', alpha=0.7, label='Biomass Available')

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Biogas Stored (kWh)', fontsize=12, color='#6A994E')
        ax2.set_ylabel('Biomass Available (ton/h)', fontsize=12, color='#8B4513')
        ax.set_title('Biogas System Operation', fontsize=14, fontweight='bold')

        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

        ax.grid(True, alpha=0.3)
        self._format_time_axis(ax, timestamps)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/biogas_operation.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_daily_average_profiles(self):
        """Plot average daily profiles for key variables"""

        timestamps = self._get_timestamps()
        df = pd.DataFrame({'timestamp': timestamps})
        df['hour'] = df['timestamp'].dt.hour

        # Get data
        wind_cols = [c for c in self.network.generators_t.p.columns if 'Wind_' in c]
        df['wind'] = self.network.generators_t.p[wind_cols].sum(axis=1).values if wind_cols else 0
        df['demand'] = self.dataset['electricity_demand']['total_kwh'].values

        if 'Battery' in self.network.stores.index:
            battery_link_cols = [c for c in self.network.links_t.p0.columns if 'Battery' in c]
            df['battery'] = self.network.links_t.p0[battery_link_cols[0]].values if battery_link_cols else 0
        else:
            df['battery'] = 0

        # Group by hour and calculate mean
        hourly_avg = df.groupby('hour').mean()

        fig, ax = plt.subplots(figsize=self.figsize)

        hours = range(24)
        ax.plot(hours, hourly_avg['wind'], marker='o', linewidth=2, label='Wind Generation', color='#2E86AB')
        ax.plot(hours, hourly_avg['demand'], marker='s', linewidth=2, label='Electricity Demand', color='#C73E1D')
        ax.plot(hours, hourly_avg['battery'], marker='^', linewidth=2, label='Battery Power', color='#6A994E')

        ax.set_xlabel('Hour of Day', fontsize=12)
        ax.set_ylabel('Average Power (kW)', fontsize=12)
        ax.set_title('Average Daily Profiles', fontsize=14, fontweight='bold')
        ax.set_xticks(range(0, 24, 2))
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/daily_average_profiles.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_technology_contribution(self):
        """Plot pie charts showing technology contribution"""

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 12))

        # 1. Electricity generation contribution
        wind_cols = [c for c in self.network.generators_t.p.columns if 'Wind_' in c]
        wind_total = self.network.generators_t.p[wind_cols].sum().sum() if wind_cols else 0

        gt_cols = [c for c in self.network.generators_t.p.columns if 'Gas_Microturbine' in c]
        gas_total = self.network.generators_t.p[gt_cols].sum().sum() if gt_cols else 0

        biogas_cols = [c for c in self.network.generators_t.p.columns if 'Biogas' in c]
        biogas_total = self.network.generators_t.p[biogas_cols].sum().sum() if biogas_cols else 0

        grid_cols = [c for c in self.network.generators_t.p.columns if 'Grid' in c]
        grid_total = self.network.generators_t.p[grid_cols].sum().sum() if grid_cols else 0

        elec_data = [wind_total, gas_total, biogas_total, grid_total]
        elec_labels = ['Wind', 'Gas Turbine', 'Biogas', 'Grid']
        elec_data = [x for x in elec_data if x > 0]
        elec_labels = [elec_labels[i] for i, x in enumerate([wind_total, gas_total, biogas_total, grid_total]) if x > 0]

        if sum(elec_data) > 0:
            ax1.pie(elec_data, labels=elec_labels, autopct='%1.1f%%', startangle=90,
                   colors=['#2E86AB', '#A23B72', '#F18F01', '#6A6A6A'])
            ax1.set_title('Electricity Generation\nby Technology', fontsize=12, fontweight='bold')

        # 2. Wind turbine types
        hawt_cols = [c for c in self.network.generators_t.p.columns if 'HAWT' in c]
        bladeless_cols = [c for c in self.network.generators_t.p.columns if 'Bladeless' in c]

        hawt_total = self.network.generators_t.p[hawt_cols].sum().sum() if hawt_cols else 0
        bladeless_total = self.network.generators_t.p[bladeless_cols].sum().sum() if bladeless_cols else 0

        wind_data = [hawt_total, bladeless_total]
        wind_labels = ['HAWT', 'Bladeless']
        wind_data = [x for x in wind_data if x > 0]
        wind_labels = [wind_labels[i] for i, x in enumerate([hawt_total, bladeless_total]) if x > 0]

        if sum(wind_data) > 0:
            ax2.pie(wind_data, labels=wind_labels, autopct='%1.1f%%', startangle=90,
                   colors=['#1f77b4', '#2ca02c'])
            ax2.set_title('Wind Generation\nby Turbine Type', fontsize=12, fontweight='bold')

        # 3. Energy vs cost (placeholder - would need cost data)
        ax3.text(0.5, 0.5, 'Cost Analysis\n(Requires Cost Data)',
                ha='center', va='center', fontsize=12, transform=ax3.transAxes)
        ax3.set_title('Economic Analysis', fontsize=12, fontweight='bold')
        ax3.axis('off')

        # 4. Renewable vs non-renewable
        renewable = wind_total + biogas_total
        non_renewable = gas_total + grid_total

        if renewable + non_renewable > 0:
            ax4.pie([renewable, non_renewable], labels=['Renewable', 'Non-Renewable'],
                   autopct='%1.1f%%', startangle=90, colors=['#6A994E', '#C73E1D'])
            ax4.set_title('Renewable Energy\nFraction', fontsize=12, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/technology_contribution.png', dpi=self.dpi, bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    print("System-level visualization module")
    print("Import and use SystemVisualizer class")
