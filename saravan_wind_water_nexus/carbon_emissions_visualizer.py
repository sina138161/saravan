"""
Carbon Emissions and Market Visualizer
Comprehensive visualization for CO2 emissions, carbon market revenue, and environmental impact
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import os


class CarbonEmissionsVisualizer:
    """
    Create visualizations for carbon emissions and carbon market analysis

    Visualizations include:
    - Hourly emissions comparison (grid vs renewable)
    - Carbon market revenue analysis
    - Cumulative emissions avoided
    - Carbon credit pricing tiers
    """

    def __init__(self, results: Dict, carbon_model, output_dir: str = None):
        """
        Initialize visualizer

        Args:
            results: Optimization results
            carbon_model: CarbonMarketModel instance
            output_dir: Output directory for plots
        """
        self.results = results
        self.carbon_model = carbon_model

        if output_dir is None:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            self.output_dir = os.path.join(desktop, 'saravan_carbon_plots')
        else:
            self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10

    def plot_hourly_emissions_comparison(self, grid_generation: np.ndarray,
                                        renewable_generation: np.ndarray,
                                        hours: int = 168):
        """
        Plot hourly emissions comparison between grid and renewable sources

        Args:
            grid_generation: Hourly grid power generation (kWh)
            renewable_generation: Hourly renewable generation (kWh)
            hours: Number of hours to display
        """

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))

        # Limit to display hours
        grid_gen = grid_generation[:hours]
        renew_gen = renewable_generation[:hours]

        # Calculate emissions (kgCO2)
        grid_emissions_factor = self.carbon_model.baseline_emissions['grid_electricity_iran']  # kgCO2/kWh
        renew_emissions_factor = self.carbon_model.baseline_emissions['wind_turbine_lifecycle']

        grid_emissions = grid_gen * grid_emissions_factor
        renew_emissions = renew_gen * renew_emissions_factor
        emissions_avoided = grid_emissions - renew_emissions

        time_hours = np.arange(hours)

        # Plot 1: Generation comparison
        ax1.fill_between(time_hours, 0, grid_gen, alpha=0.5, label='Grid Generation', color='red')
        ax1.fill_between(time_hours, 0, renew_gen, alpha=0.5, label='Renewable Generation', color='green')
        ax1.set_ylabel('Generation (kWh)')
        ax1.set_title('Hourly Power Generation: Grid vs Renewable', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Emissions comparison
        ax2.fill_between(time_hours, 0, grid_emissions, alpha=0.5, label='Grid Emissions', color='darkred')
        ax2.fill_between(time_hours, 0, renew_emissions, alpha=0.5, label='Renewable Emissions', color='lightgreen')
        ax2.set_ylabel('Emissions (kgCO₂)')
        ax2.set_title('Hourly CO₂ Emissions Comparison', fontsize=14, fontweight='bold')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)

        # Plot 3: Emissions avoided
        ax3.fill_between(time_hours, 0, emissions_avoided, alpha=0.6, color='blue')
        ax3.axhline(y=emissions_avoided.mean(), color='navy', linestyle='--',
                   label=f'Average: {emissions_avoided.mean():.1f} kgCO₂/h')
        ax3.set_xlabel('Hour')
        ax3.set_ylabel('Emissions Avoided (kgCO₂)')
        ax3.set_title('Hourly CO₂ Emissions Avoided by Renewable Energy', fontsize=14, fontweight='bold')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/hourly_emissions_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"   ✓ Saved hourly_emissions_comparison.png")

    def plot_carbon_market_revenue(self, annual_co2_avoided: float):
        """
        Plot carbon market revenue comparison across different tiers

        Args:
            annual_co2_avoided: Annual CO2 avoided (tons)
        """

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Calculate revenue for each tier
        tiers = ['VCC', 'CCC', 'PGC']
        revenues = []
        net_prices = []

        for tier in tiers:
            result = self.carbon_model.calculate_tier_revenue(
                annual_co2_avoided,
                tier,
                water_access_improvement=True
            )
            revenues.append(result['net_revenue'])
            net_prices.append(result['net_price_per_ton'])

        # Plot 1: Annual revenue by tier
        colors = ['skyblue', 'orange', 'green']
        bars1 = ax1.bar(tiers, revenues, color=colors, alpha=0.7, edgecolor='black')

        # Add value labels on bars
        for i, (bar, rev) in enumerate(zip(bars1, revenues)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'${rev:,.0f}',
                    ha='center', va='bottom', fontweight='bold')

        ax1.set_ylabel('Annual Net Revenue ($)', fontsize=12)
        ax1.set_title('Carbon Market Revenue by Tier', fontsize=14, fontweight='bold')
        ax1.grid(True, axis='y', alpha=0.3)

        # Plot 2: Effective price per ton
        bars2 = ax2.bar(tiers, net_prices, color=colors, alpha=0.7, edgecolor='black')

        # Add value labels
        for bar, price in zip(bars2, net_prices):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'${price:.2f}/ton',
                    ha='center', va='bottom', fontweight='bold')

        ax2.set_ylabel('Effective Price ($/tonCO₂)', fontsize=12)
        ax2.set_title('Net Carbon Price After Costs', fontsize=14, fontweight='bold')
        ax2.grid(True, axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/carbon_market_revenue.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"   ✓ Saved carbon_market_revenue.png")

    def plot_cumulative_emissions_avoided(self, hourly_renewable_gen: np.ndarray,
                                          hourly_grid_gen: np.ndarray):
        """
        Plot cumulative emissions avoided over time

        Args:
            hourly_renewable_gen: Hourly renewable generation (kWh)
            hourly_grid_gen: Hourly grid generation (kWh)
        """

        # Calculate hourly emissions
        grid_factor = self.carbon_model.baseline_emissions['grid_electricity_iran']
        renew_factor = self.carbon_model.baseline_emissions['wind_turbine_lifecycle']

        grid_emissions = hourly_grid_gen * grid_factor  # kgCO2
        renew_emissions = hourly_renewable_gen * renew_factor
        hourly_avoided = grid_emissions - renew_emissions

        # Cumulative
        cumulative_avoided = np.cumsum(hourly_avoided) / 1000  # Convert to tons

        hours = len(cumulative_avoided)
        time_hours = np.arange(hours)

        fig, ax = plt.subplots(figsize=(14, 6))

        ax.plot(time_hours, cumulative_avoided, linewidth=2, color='darkgreen')
        ax.fill_between(time_hours, 0, cumulative_avoided, alpha=0.3, color='green')

        # Add milestone markers
        milestones = [hours//4, hours//2, 3*hours//4, hours-1]
        for milestone in milestones:
            if milestone < len(cumulative_avoided):
                ax.plot(milestone, cumulative_avoided[milestone], 'ro', markersize=8)
                ax.text(milestone, cumulative_avoided[milestone],
                       f'{cumulative_avoided[milestone]:.1f} tons',
                       ha='center', va='bottom', fontsize=9)

        ax.set_xlabel('Hour', fontsize=12)
        ax.set_ylabel('Cumulative CO₂ Avoided (tons)', fontsize=12)
        ax.set_title('Cumulative CO₂ Emissions Avoided Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/cumulative_emissions_avoided.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"   ✓ Saved cumulative_emissions_avoided.png")

    def plot_20year_carbon_revenue_projection(self, annual_co2_avoided: float,
                                              optimal_tier: str = 'PGC'):
        """
        Plot 20-year carbon revenue projection

        Args:
            annual_co2_avoided: Annual CO2 avoided (tons)
            optimal_tier: Optimal carbon market tier
        """

        projection = self.carbon_model.calculate_20year_carbon_revenue(
            annual_co2_avoided,
            optimal_tier,
            water_benefit=True,
            price_escalation=0.03
        )

        df = projection['annual_revenues_df']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Plot 1: Annual revenue over 20 years
        ax1.bar(df['year'], df['net_revenue']/1000, color='green', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('Annual Revenue ($1000s)', fontsize=12)
        ax1.set_title(f'20-Year Carbon Revenue Projection ({optimal_tier})',
                     fontsize=14, fontweight='bold')
        ax1.grid(True, axis='y', alpha=0.3)

        # Plot 2: Carbon price escalation
        ax2.plot(df['year'], df['price_per_ton'], linewidth=2, color='blue', marker='o')
        ax2.set_xlabel('Year', fontsize=12)
        ax2.set_ylabel('Carbon Price ($/tonCO₂)', fontsize=12)
        ax2.set_title('Carbon Price Escalation (3% annual)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # Add summary text
        fig.text(0.5, 0.02,
                f"Total 20-year revenue: \\${projection['total_nominal']:,.0f} | " +
                f"NPV @ 8%%: \\${projection['npv_at_8pct']:,.0f}",
                ha='center', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout(rect=[0, 0.05, 1, 1])
        plt.savefig(f"{self.output_dir}/carbon_revenue_projection_20year.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"   ✓ Saved carbon_revenue_projection_20year.png")

    def create_all_plots(self, network, annual_co2_avoided: float):
        """
        Create all carbon-related visualizations

        Args:
            network: PyPSA network with optimization results
            annual_co2_avoided: Annual CO2 avoided (tons)
        """

        print(f"\n{'='*70}")
        print("CREATING CARBON EMISSIONS VISUALIZATIONS")
        print(f"{'='*70}")

        # Extract generation data
        if 'Grid_Gas_Power' in network.generators_t.p.columns:
            grid_gen = network.generators_t.p['Grid_Gas_Power'].values
        else:
            grid_gen = np.zeros(len(network.snapshots))

        # Sum all renewable generation
        renew_gen = np.zeros(len(network.snapshots))
        for gen in network.generators.index:
            if 'Wind' in gen:
                # Skip if optimization failed and no data available
                if gen not in network.generators_t.p.columns:
                    continue
                renew_gen += network.generators_t.p[gen].values

        # Create plots
        self.plot_hourly_emissions_comparison(grid_gen, renew_gen)
        self.plot_carbon_market_revenue(annual_co2_avoided)
        self.plot_cumulative_emissions_avoided(renew_gen, grid_gen)
        self.plot_20year_carbon_revenue_projection(annual_co2_avoided)

        print(f"\n✅ All carbon visualizations saved to: {self.output_dir}")


# Example usage
if __name__ == "__main__":
    from carbon_market_model import CarbonMarketModel

    carbon_model = CarbonMarketModel()

    # Mock results for testing
    results = {
        'carbon': {
            'annual_energy_kwh': 5000000,
            'co2_avoided_tons': 3000
        }
    }

    visualizer = CarbonEmissionsVisualizer(results, carbon_model)

    # Create sample data
    hours = 168
    grid_gen = np.random.uniform(20, 100, hours)
    renew_gen = np.random.uniform(50, 150, hours)

    print("Creating carbon emissions visualizations...")
    visualizer.plot_hourly_emissions_comparison(grid_gen, renew_gen)
    visualizer.plot_carbon_market_revenue(3000)
    visualizer.plot_cumulative_emissions_avoided(renew_gen, grid_gen)
    visualizer.plot_20year_carbon_revenue_projection(3000)

    print("\n✅ Test visualizations complete!")
