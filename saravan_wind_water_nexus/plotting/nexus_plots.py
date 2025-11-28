"""
Comprehensive Visualization Module for Wind-Water-Energy Nexus
Publication-ready plots for Q1 journals
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
from typing import Dict, Optional
import os
from pathlib import Path

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class NexusVisualizer:
    """
    Comprehensive visualization for Wind-Water-Energy Nexus

    Creates publication-ready plots including:
    - Wind generation by turbine type
    - Dust impact analysis
    - Battery operation and SOC
    - Water system (pumping, tank, demand)
    - Supply-demand balance
    - Economic and carbon analysis
    - Comparative performance
    """

    def __init__(self,
                 dataset: Dict,
                 network,
                 results: Dict,
                 output_dir: str = None,
                 dpi: int = 300):
        """
        Initialize visualizer

        Args:
            dataset: Time series data (wind, dust, temperature, water)
            network: PyPSA network object
            results: Optimization results
            output_dir: Output directory for plots
            dpi: Resolution for saved plots
        """
        self.dataset = dataset
        self.network = network
        self.results = results
        self.dpi = dpi

        # Set output directory - use config.OUTPUT_DIR by default
        if output_dir is None:
            from config import config
            self.output_dir = str(config.OUTPUT_DIR / 'plots')
        else:
            self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        # Figure sizes
        self.figsize_single = (12, 6)
        self.figsize_double = (14, 8)
        self.figsize_grid = (16, 10)

        # Color scheme
        self.colors = {
            'HAWT': '#1f77b4',
            'VAWT': '#ff7f0e',
            'Bladeless': '#2ca02c',
            'Battery': '#d62728',
            'Water': '#17becf',
            'Demand': '#e377c2',
            'Dust': '#8c564b',
            'Wind': '#9467bd',
            'Grid': '#7f7f7f'
        }

    def create_all_plots(self):
        """Create all visualization plots"""

        print(f"\n{'='*70}")
        print("CREATING COMPREHENSIVE VISUALIZATIONS")
        print(f"{'='*70}")

        # Check if optimization was successful
        if self.results.get('optimization', {}).get('status') != 'ok':
            print("\n⚠️  WARNING: Optimization did not complete successfully (status: {})".format(
                self.results.get('optimization', {}).get('status', 'unknown')))
            print("   Skipping detailed visualizations. Only basic plots will be created.")
            print("   Please fix optimization issues first.")

            # Create only basic plots that don't require optimization results
            print("\n📊 Creating basic data plots...")
            self.plot_dust_vs_wind()
            print("\n✅ Basic plots created successfully")
            return

        # 1. Wind generation plots
        print("\n🌪️  Creating wind generation plots...")
        self.plot_wind_generation_by_type()
        self.plot_wind_generation_stacked()
        self.plot_capacity_factors()

        # 2. Dust impact analysis
        print("🏜️  Creating dust impact plots...")
        self.plot_dust_impact()
        self.plot_dust_vs_wind()
        self.plot_turbine_efficiency_comparison()

        # 3. Battery analysis
        print("🔋 Creating battery analysis plots...")
        self.plot_battery_soc()
        self.plot_battery_power_flow()

        # 4. Water system plots
        print("💧 Creating water system plots...")
        self.plot_water_demand_supply()
        self.plot_water_tank_level()
        self.plot_pumping_energy()

        # 5. Supply-demand balance
        print("⚡ Creating supply-demand plots...")
        self.plot_electricity_balance()
        self.plot_water_balance()

        # 6. Environmental data
        print("🌡️  Creating environmental plots...")
        self.plot_weather_conditions()

        # 7. Performance summary
        print("📊 Creating performance summary plots...")
        self.plot_energy_breakdown()
        self.plot_daily_profiles()

        # 8. Economic and carbon
        print("💰 Creating economic plots...")
        self.plot_carbon_analysis()

        print(f"\n✅ All visualizations saved to: {self.output_dir}/")
        print(f"   Total plots created: 18")

    def _get_timestamps(self):
        """Get timestamps from dataset"""
        return pd.to_datetime(self.dataset['wind']['timestamp'])

    def _format_time_axis(self, ax, timestamps):
        """Format time axis with proper date formatting"""
        hours = len(timestamps)

        if hours <= 48:  # 2 days or less
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        elif hours <= 168:  # 1 week
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
        else:  # Longer periods
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # ========== WIND GENERATION PLOTS ==========

    def plot_wind_generation_by_type(self):
        """Plot wind generation separated by turbine type"""

        timestamps = self._get_timestamps()

        # Only use turbine types that exist in the network (VAWT removed)
        turbine_types = ['HAWT', 'Bladeless']
        available_turbines = [t for t in turbine_types
                              if f'Wind_{t}' in self.network.generators_t.p.columns]

        if not available_turbines:
            return

        n_turbines = len(available_turbines)
        fig, axes = plt.subplots(n_turbines, 1, figsize=(14, 4*n_turbines), sharex=True)
        if n_turbines == 1:
            axes = [axes]

        for idx, (ax, turb_type) in enumerate(zip(axes, available_turbines)):
            gen_name = f'Wind_{turb_type}'
            power = self.network.generators_t.p[gen_name].values

            ax.fill_between(timestamps[:len(power)], power,
                           alpha=0.4, color=self.colors.get(turb_type, 'gray'))
            ax.plot(timestamps[:len(power)], power,
                   linewidth=1.5, color=self.colors.get(turb_type, 'gray'))

            # Add statistics
            total_energy = power.sum()
            avg_power = power.mean()
            max_power = power.max()

            ax.text(0.02, 0.95,
                   f'Total: {total_energy:,.0f} kWh\nAvg: {avg_power:.1f} kW\nMax: {max_power:.1f} kW',
                   transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            ax.set_ylabel(f'{turb_type}\nPower (kW)', fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.set_title(f'{turb_type} Wind Turbine Generation', fontsize=12, fontweight='bold')

        self._format_time_axis(axes[-1], timestamps)
        axes[-1].set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/wind_generation_by_type.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_wind_generation_stacked(self):
        """Plot stacked wind generation from all turbines"""

        timestamps = self._get_timestamps()

        fig, ax = plt.subplots(figsize=self.figsize_double)

        # Collect generation data (VAWT removed)
        generation_data = {}
        turbine_types = ['HAWT', 'Bladeless']
        available_turbines = []

        for turb_type in turbine_types:
            gen_name = f'Wind_{turb_type}'
            if gen_name in self.network.generators_t.p.columns:
                generation_data[turb_type] = self.network.generators_t.p[gen_name].values
                available_turbines.append(turb_type)

        if not available_turbines:
            plt.close()
            return

        # Create stacked area plot
        stack_data = [generation_data[t] for t in available_turbines]
        stack_colors = [self.colors.get(t, 'gray') for t in available_turbines]

        ax.stackplot(timestamps[:len(stack_data[0])],
                    *stack_data,
                    labels=available_turbines,
                    colors=stack_colors,
                    alpha=0.7)

        # Add total generation line
        total_gen = sum(stack_data)
        ax.plot(timestamps[:len(total_gen)], total_gen,
               color='black', linewidth=2, label='Total', linestyle='--')

        ax.set_ylabel('Power Generation (kW)', fontsize=12)
        ax.set_title('Total Wind Generation (Stacked by Turbine Type)',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', frameon=True, fontsize=10)
        ax.grid(True, alpha=0.3)

        self._format_time_axis(ax, timestamps)
        ax.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/wind_generation_stacked.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_capacity_factors(self):
        """Plot capacity factors by turbine type"""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize_double)

        # Collect capacity factor data
        turbine_types = []
        capacity_factors = []
        total_energies = []
        capacities = []

        for gen in self.network.generators.index:
            if gen.startswith('Wind_'):
                # Skip if optimization failed and no data available
                if gen not in self.network.generators_t.p.columns:
                    continue

                turb_type = gen.replace('Wind_', '')
                total_gen = self.network.generators_t.p[gen].sum()
                capacity = self.network.generators.loc[gen, 'p_nom']
                hours = len(self.network.snapshots)
                cf = total_gen / (capacity * hours) if capacity > 0 else 0

                turbine_types.append(turb_type)
                capacity_factors.append(cf * 100)
                total_energies.append(total_gen)
                capacities.append(capacity)

        # Plot 1: Capacity factors
        colors_list = [self.colors.get(t, '#gray') for t in turbine_types]
        bars1 = ax1.bar(turbine_types, capacity_factors, color=colors_list, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('Capacity Factor (%)', fontsize=12)
        ax1.set_title('Capacity Factors by Turbine Type', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar, cf in zip(bars1, capacity_factors):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{cf:.1f}%',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 2: Total energy generation
        bars2 = ax2.bar(turbine_types, total_energies, color=colors_list, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Total Energy (kWh)', fontsize=12)
        ax2.set_title('Total Energy Generation by Turbine Type', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar, energy in zip(bars2, total_energies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{energy:,.0f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/capacity_factors.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    # ========== DUST IMPACT PLOTS ==========

    def plot_dust_impact(self):
        """Plot dust concentration and its impact on generation"""

        timestamps = self._get_timestamps()
        dust = self.dataset['dust']['pm10_ugm3'].values
        wind_speed = self.dataset['wind']['wind_speed_ms'].values

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize_double, sharex=True)

        # Plot 1: Dust concentration
        ax1.fill_between(timestamps, dust, alpha=0.3, color=self.colors['Dust'])
        ax1.plot(timestamps, dust, linewidth=1.5, color=self.colors['Dust'])

        # Add threshold lines
        ax1.axhline(y=200, color='orange', linestyle='--', linewidth=2, label='Storm threshold (200 μg/m³)')
        ax1.axhline(y=300, color='red', linestyle='--', linewidth=2, label='Severe storm (300 μg/m³)')

        ax1.set_ylabel('PM10 Concentration (μg/m³)', fontsize=12)
        ax1.set_title('Dust Concentration Over Time', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', frameon=True)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Wind speed (correlated with dust)
        ax2.fill_between(timestamps, wind_speed, alpha=0.3, color=self.colors['Wind'])
        ax2.plot(timestamps, wind_speed, linewidth=1.5, color=self.colors['Wind'])

        ax2.set_ylabel('Wind Speed (m/s)', fontsize=12)
        ax2.set_title('Wind Speed (Correlated with Dust)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        self._format_time_axis(ax2, timestamps)
        ax2.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/dust_impact.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_dust_vs_wind(self):
        """Scatter plot: dust concentration vs wind speed"""

        dust = self.dataset['dust']['pm10_ugm3'].values
        wind_speed = self.dataset['wind']['wind_speed_ms'].values

        fig, ax = plt.subplots(figsize=self.figsize_single)

        # Scatter plot with density coloring
        scatter = ax.scatter(wind_speed, dust, c=dust, cmap='YlOrRd',
                           alpha=0.6, s=20, edgecolors='none')

        # Add correlation line
        z = np.polyfit(wind_speed, dust, 1)
        p = np.poly1d(z)
        ax.plot(wind_speed, p(wind_speed), "r--", linewidth=2, alpha=0.8,
               label=f'Trend (R²={np.corrcoef(wind_speed, dust)[0,1]**2:.3f})')

        ax.set_xlabel('Wind Speed (m/s)', fontsize=12)
        ax.set_ylabel('PM10 Concentration (μg/m³)', fontsize=12)
        ax.set_title('Dust-Wind Correlation', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', frameon=True)
        ax.grid(True, alpha=0.3)

        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('PM10 (μg/m³)', fontsize=10)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/dust_vs_wind_correlation.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_turbine_efficiency_comparison(self):
        """Compare turbine efficiency under different dust conditions"""

        dust = self.dataset['dust']['pm10_ugm3'].values

        # Categorize by dust levels
        clean = dust < 100
        moderate = (dust >= 100) & (dust < 200)
        dusty = dust >= 200

        categories = ['Clean\n(<100 μg/m³)', 'Moderate\n(100-200 μg/m³)', 'Dusty\n(>200 μg/m³)']
        conditions = [clean, moderate, dusty]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize_double)

        # Only use turbine types that exist in the network (VAWT removed)
        turbine_types = ['HAWT', 'Bladeless']
        available_turbines = []
        for turb_type in turbine_types:
            gen_name = f'Wind_{turb_type}'
            if gen_name in self.network.generators_t.p.columns:
                available_turbines.append(turb_type)

        if not available_turbines:
            plt.close()
            return

        # Plot 1: Average power output by condition
        avg_power = {turb: [] for turb in available_turbines}

        for turb_type in available_turbines:
            gen_name = f'Wind_{turb_type}'
            power = self.network.generators_t.p[gen_name].values
            capacity = self.network.generators.loc[gen_name, 'p_nom']

            for condition in conditions:
                if np.sum(condition) > 0:
                    avg_cf = power[condition].mean() / capacity if capacity > 0 else 0
                    avg_power[turb_type].append(avg_cf * 100)
                else:
                    avg_power[turb_type].append(0)

        x = np.arange(len(categories))
        width = 0.35 if len(available_turbines) == 2 else 0.25
        n_turbines = len(available_turbines)

        for idx, turb_type in enumerate(available_turbines):
            offset = (idx - (n_turbines - 1) / 2) * width
            bars = ax1.bar(x + offset, avg_power[turb_type], width,
                          label=turb_type, color=self.colors.get(turb_type, 'gray'), alpha=0.7)

        ax1.set_ylabel('Average Capacity Factor (%)', fontsize=12)
        ax1.set_title('Turbine Performance by Dust Condition', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend(loc='upper right', frameon=True)
        ax1.grid(True, alpha=0.3, axis='y')

        # Plot 2: Dust impact percentage
        # Calculate average loss compared to clean conditions
        losses = {turb: [] for turb in available_turbines}

        for turb_type in available_turbines:
            if len(avg_power[turb_type]) >= 3:
                clean_cf = avg_power[turb_type][0]
                for cf in avg_power[turb_type]:
                    loss = ((clean_cf - cf) / clean_cf * 100) if clean_cf > 0 else 0
                    losses[turb_type].append(loss)

        for idx, turb_type in enumerate(available_turbines):
            if len(losses[turb_type]) >= 3:
                offset = (idx - (n_turbines - 1) / 2) * width
                bars = ax2.bar(x + offset, losses[turb_type], width,
                              label=turb_type, color=self.colors.get(turb_type, 'gray'), alpha=0.7)

        ax2.set_ylabel('Power Loss vs Clean Conditions (%)', fontsize=12)
        ax2.set_title('Dust-Induced Power Loss', fontsize=12, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories)
        ax2.legend(loc='upper left', frameon=True)
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/turbine_efficiency_comparison.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    # ========== BATTERY PLOTS ==========

    def plot_battery_soc(self):
        """Plot battery state of charge"""

        if 'Battery' not in self.network.stores_t.e.columns:
            return

        timestamps = self._get_timestamps()
        soc = self.network.stores_t.e['Battery'].values
        capacity = self.network.stores.loc['Battery', 'e_nom']
        soc_percent = (soc / capacity) * 100

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize_double, sharex=True)

        # Plot 1: SOC in kWh
        ax1.fill_between(timestamps[:len(soc)], soc, alpha=0.3, color=self.colors['Battery'])
        ax1.plot(timestamps[:len(soc)], soc, linewidth=2, color=self.colors['Battery'])
        ax1.axhline(y=capacity, color='red', linestyle='--', linewidth=1.5,
                   label=f'Capacity ({capacity} kWh)', alpha=0.7)
        ax1.set_ylabel('State of Charge (kWh)', fontsize=12)
        ax1.set_title('Battery State of Charge', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', frameon=True)
        ax1.grid(True, alpha=0.3)

        # Add statistics
        stats_text = f'Min: {soc.min():.1f} kWh\nMax: {soc.max():.1f} kWh\nAvg: {soc.mean():.1f} kWh'
        ax1.text(0.02, 0.95, stats_text, transform=ax1.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Plot 2: SOC in percentage
        ax2.fill_between(timestamps[:len(soc_percent)], soc_percent,
                        alpha=0.3, color=self.colors['Battery'])
        ax2.plot(timestamps[:len(soc_percent)], soc_percent,
                linewidth=2, color=self.colors['Battery'])
        ax2.axhline(y=100, color='red', linestyle='--', linewidth=1.5,
                   label='100% SOC', alpha=0.7)
        ax2.axhline(y=20, color='orange', linestyle='--', linewidth=1.5,
                   label='20% SOC (Min recommended)', alpha=0.7)
        ax2.set_ylabel('State of Charge (%)', fontsize=12)
        ax2.set_title('Battery SOC Percentage', fontsize=14, fontweight='bold')
        ax2.legend(loc='upper right', frameon=True)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 105)

        self._format_time_axis(ax2, timestamps)
        ax2.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/battery_soc.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_battery_power_flow(self):
        """Plot battery charging and discharging"""

        if 'Battery' not in self.network.stores_t.e.columns:
            return

        timestamps = self._get_timestamps()
        soc = self.network.stores_t.e['Battery'].values

        # Calculate power flow from SOC changes
        power_flow = np.diff(soc, prepend=soc[0])
        charging = np.maximum(power_flow, 0)
        discharging = np.minimum(power_flow, 0)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize_double, sharex=True)

        # Plot 1: Charging/Discharging power
        ax1.fill_between(timestamps[:len(charging)], charging,
                        alpha=0.5, color='green', label='Charging')
        ax1.fill_between(timestamps[:len(discharging)], discharging,
                        alpha=0.5, color='red', label='Discharging')
        ax1.axhline(y=0, color='black', linewidth=1)
        ax1.set_ylabel('Power Flow (kW)', fontsize=12)
        ax1.set_title('Battery Charging/Discharging', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', frameon=True)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Cumulative energy throughput
        cumulative_charge = np.cumsum(charging)
        cumulative_discharge = np.cumsum(np.abs(discharging))

        ax2.plot(timestamps[:len(cumulative_charge)], cumulative_charge,
                linewidth=2, color='green', label='Cumulative Charging')
        ax2.plot(timestamps[:len(cumulative_discharge)], cumulative_discharge,
                linewidth=2, color='red', label='Cumulative Discharging')
        ax2.set_ylabel('Cumulative Energy (kWh)', fontsize=12)
        ax2.set_title('Battery Cumulative Throughput', fontsize=14, fontweight='bold')
        ax2.legend(loc='upper left', frameon=True)
        ax2.grid(True, alpha=0.3)

        self._format_time_axis(ax2, timestamps)
        ax2.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/battery_power_flow.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    # ========== WATER SYSTEM PLOTS ==========

    def plot_water_demand_supply(self):
        """Plot water demand and supply"""

        timestamps = self._get_timestamps()
        water_demand = self.dataset['water_demand']['total_m3h'].values

        # Get water pumped from link
        water_pumped = np.zeros(len(timestamps))
        if 'Water_Pump' in self.network.links_t.p0.columns:
            # p0 is electricity consumed, need to convert to water
            elec_consumed = self.network.links_t.p0['Water_Pump'].values
            efficiency = self.network.links.loc['Water_Pump', 'efficiency']
            water_pumped = elec_consumed * efficiency

        fig, ax = plt.subplots(figsize=self.figsize_double)

        ax.plot(timestamps[:len(water_demand)], water_demand,
               linewidth=2, color='#d62728', label='Demand', linestyle='--')
        ax.plot(timestamps[:len(water_pumped)], water_pumped,
               linewidth=2, color=self.colors['Water'], label='Supply (Pumped)', alpha=0.8)
        ax.fill_between(timestamps[:len(water_pumped)], water_pumped,
                       alpha=0.3, color=self.colors['Water'])

        ax.set_ylabel('Water Flow (m³/h)', fontsize=12)
        ax.set_title('Water Supply-Demand Balance', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', frameon=True, fontsize=11)
        ax.grid(True, alpha=0.3)

        # Add statistics
        total_demand = water_demand.sum()
        total_supply = water_pumped.sum()
        stats_text = f'Total Demand: {total_demand:,.0f} m³\nTotal Supply: {total_supply:,.0f} m³'
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self._format_time_axis(ax, timestamps)
        ax.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/water_demand_supply.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_water_tank_level(self):
        """Plot water tank storage level"""

        if 'Water_Tank' not in self.network.stores_t.e.columns:
            return

        timestamps = self._get_timestamps()
        tank_level = self.network.stores_t.e['Water_Tank'].values
        capacity = self.network.stores.loc['Water_Tank', 'e_nom']
        level_percent = (tank_level / capacity) * 100

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize_double, sharex=True)

        # Plot 1: Tank level in m³
        ax1.fill_between(timestamps[:len(tank_level)], tank_level,
                        alpha=0.3, color=self.colors['Water'])
        ax1.plot(timestamps[:len(tank_level)], tank_level,
                linewidth=2, color=self.colors['Water'])
        ax1.axhline(y=capacity, color='red', linestyle='--', linewidth=1.5,
                   label=f'Capacity ({capacity} m³)', alpha=0.7)
        ax1.set_ylabel('Water Level (m³)', fontsize=12)
        ax1.set_title('Water Tank Storage Level', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', frameon=True)
        ax1.grid(True, alpha=0.3)

        # Add statistics
        stats_text = f'Min: {tank_level.min():.1f} m³\nMax: {tank_level.max():.1f} m³\nAvg: {tank_level.mean():.1f} m³'
        ax1.text(0.02, 0.95, stats_text, transform=ax1.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Plot 2: Tank level in percentage
        ax2.fill_between(timestamps[:len(level_percent)], level_percent,
                        alpha=0.3, color=self.colors['Water'])
        ax2.plot(timestamps[:len(level_percent)], level_percent,
                linewidth=2, color=self.colors['Water'])
        ax2.axhline(y=100, color='red', linestyle='--', linewidth=1.5,
                   label='100% Full', alpha=0.7)
        ax2.axhline(y=10, color='orange', linestyle='--', linewidth=1.5,
                   label='10% (Emergency reserve)', alpha=0.7)
        ax2.set_ylabel('Tank Level (%)', fontsize=12)
        ax2.set_title('Water Tank Level Percentage', fontsize=14, fontweight='bold')
        ax2.legend(loc='upper right', frameon=True)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 105)

        self._format_time_axis(ax2, timestamps)
        ax2.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/water_tank_level.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_pumping_energy(self):
        """Plot energy consumption for water pumping"""

        timestamps = self._get_timestamps()

        # Get pumping power
        pumping_power = np.zeros(len(timestamps))
        if 'Water_Pump' in self.network.links_t.p0.columns:
            pumping_power = self.network.links_t.p0['Water_Pump'].values

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize_double, sharex=True)

        # Plot 1: Pumping power over time
        ax1.fill_between(timestamps[:len(pumping_power)], pumping_power,
                        alpha=0.3, color=self.colors['Water'])
        ax1.plot(timestamps[:len(pumping_power)], pumping_power,
                linewidth=2, color=self.colors['Water'])
        ax1.set_ylabel('Pumping Power (kW)', fontsize=12)
        ax1.set_title('Water Pumping Energy Consumption', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # Add statistics
        total_energy = pumping_power.sum()
        avg_power = pumping_power.mean()
        max_power = pumping_power.max()
        stats_text = f'Total: {total_energy:,.0f} kWh\nAvg: {avg_power:.1f} kW\nMax: {max_power:.1f} kW'
        ax1.text(0.02, 0.95, stats_text, transform=ax1.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Plot 2: Cumulative energy
        cumulative_energy = np.cumsum(pumping_power)
        ax2.plot(timestamps[:len(cumulative_energy)], cumulative_energy,
                linewidth=2, color=self.colors['Water'])
        ax2.fill_between(timestamps[:len(cumulative_energy)], cumulative_energy,
                        alpha=0.3, color=self.colors['Water'])
        ax2.set_ylabel('Cumulative Energy (kWh)', fontsize=12)
        ax2.set_title('Cumulative Pumping Energy', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        self._format_time_axis(ax2, timestamps)
        ax2.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/pumping_energy.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    # ========== SUPPLY-DEMAND BALANCE ==========

    def plot_electricity_balance(self):
        """Plot electricity supply-demand balance"""

        timestamps = self._get_timestamps()

        # Get electricity demand
        if 'Electricity_Demand' in self.network.loads_t.p.columns:
            elec_demand = self.network.loads_t.p['Electricity_Demand'].values
        else:
            elec_demand = np.zeros(len(timestamps))

        # Get total generation
        total_gen = np.zeros(len(timestamps))
        for gen in self.network.generators_t.p.columns:
            gen_data = self.network.generators_t.p[gen].values
            if len(gen_data) > 0:
                total_gen[:len(gen_data)] += gen_data

        # Get pumping load
        pumping_load = np.zeros(len(timestamps))
        if 'Water_Pump' in self.network.links_t.p0.columns:
            pumping_load = self.network.links_t.p0['Water_Pump'].values

        total_load = elec_demand + pumping_load

        fig, ax = plt.subplots(figsize=self.figsize_double)

        ax.plot(timestamps[:len(total_load)], total_load,
               linewidth=2, color='#d62728', label='Total Demand', linestyle='--')
        ax.plot(timestamps[:len(total_gen)], total_gen,
               linewidth=2, color='#2ca02c', label='Total Generation', alpha=0.8)
        ax.fill_between(timestamps[:len(total_gen)], total_gen,
                       alpha=0.2, color='#2ca02c')

        ax.set_ylabel('Power (kW)', fontsize=12)
        ax.set_title('Electricity Supply-Demand Balance', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', frameon=True, fontsize=11)
        ax.grid(True, alpha=0.3)

        # Add statistics
        total_gen_sum = total_gen.sum()
        total_load_sum = total_load.sum()
        balance = ((total_gen_sum - total_load_sum) / total_load_sum * 100) if total_load_sum > 0 else 0
        stats_text = f'Total Generation: {total_gen_sum:,.0f} kWh\nTotal Load: {total_load_sum:,.0f} kWh\nBalance: {balance:+.1f}%'
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self._format_time_axis(ax, timestamps)
        ax.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/electricity_balance.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_water_balance(self):
        """Plot water supply-demand balance"""

        timestamps = self._get_timestamps()

        # Get water demand
        if 'Water_Demand' in self.network.loads_t.p.columns:
            water_demand = self.network.loads_t.p['Water_Demand'].values
        else:
            water_demand = self.dataset['water_demand']['total_m3h'].values

        # Get water supply
        water_supply = np.zeros(len(timestamps))
        if 'Water_Pump' in self.network.links_t.p0.columns:
            elec_consumed = self.network.links_t.p0['Water_Pump'].values
            efficiency = self.network.links.loc['Water_Pump', 'efficiency']
            water_supply = elec_consumed * efficiency

        fig, ax = plt.subplots(figsize=self.figsize_double)

        ax.plot(timestamps[:len(water_demand)], water_demand,
               linewidth=2, color='#d62728', label='Water Demand', linestyle='--')
        ax.plot(timestamps[:len(water_supply)], water_supply,
               linewidth=2, color=self.colors['Water'], label='Water Supply', alpha=0.8)
        ax.fill_between(timestamps[:len(water_supply)], water_supply,
                       alpha=0.2, color=self.colors['Water'])

        ax.set_ylabel('Water Flow (m³/h)', fontsize=12)
        ax.set_title('Water Supply-Demand Balance', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', frameon=True, fontsize=11)
        ax.grid(True, alpha=0.3)

        # Add statistics
        total_demand_sum = water_demand.sum()
        total_supply_sum = water_supply.sum()
        balance = ((total_supply_sum - total_demand_sum) / total_demand_sum * 100) if total_demand_sum > 0 else 0
        stats_text = f'Total Demand: {total_demand_sum:,.0f} m³\nTotal Supply: {total_supply_sum:,.0f} m³\nBalance: {balance:+.1f}%'
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self._format_time_axis(ax, timestamps)
        ax.set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/water_balance.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    # ========== ENVIRONMENTAL DATA ==========

    def plot_weather_conditions(self):
        """Plot all weather conditions"""

        timestamps = self._get_timestamps()
        wind_speed = self.dataset['wind']['wind_speed_ms'].values
        dust = self.dataset['dust']['pm10_ugm3'].values
        temperature = self.dataset['temperature']['temperature_c'].values

        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        # Wind speed
        axes[0].fill_between(timestamps, wind_speed, alpha=0.3, color=self.colors['Wind'])
        axes[0].plot(timestamps, wind_speed, linewidth=1.5, color=self.colors['Wind'])
        axes[0].set_ylabel('Wind Speed (m/s)', fontsize=12)
        axes[0].set_title('Environmental Conditions', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        axes[0].text(0.02, 0.95, f'Avg: {wind_speed.mean():.2f} m/s\nMax: {wind_speed.max():.2f} m/s',
                    transform=axes[0].transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Dust concentration
        axes[1].fill_between(timestamps, dust, alpha=0.3, color=self.colors['Dust'])
        axes[1].plot(timestamps, dust, linewidth=1.5, color=self.colors['Dust'])
        axes[1].axhline(y=200, color='orange', linestyle='--', linewidth=1, alpha=0.7)
        axes[1].set_ylabel('PM10 (μg/m³)', fontsize=12)
        axes[1].grid(True, alpha=0.3)
        axes[1].text(0.02, 0.95, f'Avg: {dust.mean():.0f} μg/m³\nMax: {dust.max():.0f} μg/m³',
                    transform=axes[1].transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Temperature
        axes[2].fill_between(timestamps, temperature, alpha=0.3, color='#ff7f0e')
        axes[2].plot(timestamps, temperature, linewidth=1.5, color='#ff7f0e')
        axes[2].set_ylabel('Temperature (°C)', fontsize=12)
        axes[2].grid(True, alpha=0.3)
        axes[2].text(0.02, 0.95, f'Avg: {temperature.mean():.1f}°C\nMax: {temperature.max():.1f}°C',
                    transform=axes[2].transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self._format_time_axis(axes[2], timestamps)
        axes[2].set_xlabel('Time', fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/weather_conditions.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    # ========== PERFORMANCE SUMMARY ==========

    def plot_energy_breakdown(self):
        """Plot energy generation breakdown pie chart"""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize_double)

        # Energy generation breakdown
        energy_data = []
        labels = []
        colors_list = []

        for gen in self.network.generators.index:
            if gen.startswith('Wind_'):
                turb_type = gen.replace('Wind_', '')
                total_gen = self.network.generators_t.p[gen].sum()
                if total_gen > 0:
                    energy_data.append(total_gen)
                    labels.append(turb_type)
                    colors_list.append(self.colors[turb_type])

        # Pie chart
        wedges, texts, autotexts = ax1.pie(energy_data, labels=labels, autopct='%1.1f%%',
                                           colors=colors_list, startangle=90)
        ax1.set_title('Energy Generation by Turbine Type', fontsize=12, fontweight='bold')

        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        # Bar chart with absolute values
        bars = ax2.bar(labels, energy_data, color=colors_list, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Total Energy (kWh)', fontsize=12)
        ax2.set_title('Total Energy Generation', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for bar, energy in zip(bars, energy_data):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{energy:,.0f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/energy_breakdown.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    def plot_daily_profiles(self):
        """Plot average daily profiles"""

        timestamps = self._get_timestamps()

        # Calculate hourly averages
        if isinstance(timestamps, pd.Series):
            hours = timestamps.dt.hour.values
        else:
            hours = pd.DatetimeIndex(timestamps).hour

        # Wind generation
        total_wind = np.zeros(len(timestamps))
        for gen in self.network.generators_t.p.columns:
            if 'Wind_' in gen:
                total_wind += self.network.generators_t.p[gen].values

        # Water demand
        water_demand = self.dataset['water_demand']['total_m3h'].values

        # Create hourly averages
        hourly_wind = [total_wind[hours == h].mean() for h in range(24)]
        hourly_water = [water_demand[hours == h].mean() for h in range(24)]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize_double, sharex=True)

        # Wind generation profile
        ax1.plot(range(24), hourly_wind, linewidth=2.5, marker='o',
                markersize=6, color=self.colors['Wind'])
        ax1.fill_between(range(24), hourly_wind, alpha=0.3, color=self.colors['Wind'])
        ax1.set_ylabel('Avg Wind Generation (kW)', fontsize=12)
        ax1.set_title('Average Daily Profiles', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # Water demand profile
        ax2.plot(range(24), hourly_water, linewidth=2.5, marker='s',
                markersize=6, color=self.colors['Water'])
        ax2.fill_between(range(24), hourly_water, alpha=0.3, color=self.colors['Water'])
        ax2.set_ylabel('Avg Water Demand (m³/h)', fontsize=12)
        ax2.set_xlabel('Hour of Day', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(range(0, 24, 2))

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/daily_profiles.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()

    # ========== CARBON ANALYSIS ==========

    def plot_carbon_analysis(self):
        """Plot carbon credits and revenue analysis"""

        if 'carbon' not in self.results:
            return

        carbon_data = self.results['carbon']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize_double)

        # CO2 breakdown
        co2_sources = ['Energy\nGeneration', 'Water\nPumping']
        co2_values = [carbon_data['co2_from_energy'], carbon_data['co2_from_water']]
        colors_co2 = ['#2ca02c', '#17becf']

        bars1 = ax1.bar(co2_sources, co2_values, color=colors_co2, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('CO2 Avoided (tons/year)', fontsize=12)
        ax1.set_title('CO2 Emissions Avoided', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for bar, value in zip(bars1, co2_values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:,.0f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Add total line
        total_co2 = sum(co2_values)
        ax1.axhline(y=total_co2, color='red', linestyle='--', linewidth=2,
                   label=f'Total: {total_co2:,.0f} tons/year')
        ax1.legend(loc='upper right', frameon=True)

        # Carbon market comparison
        if 'tier_comparison' in carbon_data:
            tier_data = carbon_data['tier_comparison']
            if 'net_revenue' in tier_data:
                tiers = list(tier_data['net_revenue'].values())
                tier_names = list(tier_data['net_revenue'].keys())

                bars2 = ax2.bar(tier_names, tiers,
                              color=['#ff9999', '#ffcc99', '#99ff99'],
                              alpha=0.7, edgecolor='black')
                ax2.set_ylabel('Annual Revenue ($)', fontsize=12)
                ax2.set_title('Carbon Market Tier Comparison', fontsize=12, fontweight='bold')
                ax2.grid(True, alpha=0.3, axis='y')

                # Add value labels
                for bar, value in zip(bars2, tiers):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'${value:,.0f}',
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

                # Highlight optimal tier
                optimal_tier = carbon_data['optimal_tier']
                if optimal_tier in tier_names:
                    optimal_idx = tier_names.index(optimal_tier)
                    bars2[optimal_idx].set_edgecolor('red')
                    bars2[optimal_idx].set_linewidth(3)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/carbon_analysis.png',
                   dpi=self.dpi, bbox_inches='tight')
        plt.close()


# Example usage
if __name__ == "__main__":
    print("Visualization module for Wind-Water-Energy Nexus")
    print("Import this module and use NexusVisualizer class")
