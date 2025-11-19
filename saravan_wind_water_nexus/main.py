"""
Main Entry Point for Saravan Wind-Water-Energy-Carbon Nexus Model

This is the main script that runs the complete analysis workflow
using the refactored PyPSA-standard structure.

Usage:
    python main.py
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from scripts.run_analysis import run_complete_analysis
from config import config


def main():
    """
    Main entry point

    Runs the complete Saravan Wind-Water-Energy-Carbon Nexus analysis
    following the PyPSA-standard workflow structure.
    """

    print("\n" + "="*70)
    print("SARAVAN WIND-WATER-ENERGY-CARBON NEXUS MODEL")
    print("PyPSA-based Multi-Sector Optimization")
    print("="*70)
    print(f"\nModel Configuration:")
    print(f"  Location: Saravan, Iran")
    print(f"  Period: {config.SNAPSHOTS_START} to {config.SNAPSHOTS_END}")
    print(f"  Frequency: {config.SNAPSHOTS_FREQ}")
    print(f"  Solver: {config.SOLVER}")
    print(f"\nComponents:")
    print(f"  Turbines: {config.TURBINE_MIX}")
    print(f"  Battery: {config.BATTERY_CAPACITY_KWH} kWh")
    print(f"  Water Tank: {config.WATER_TANK_CAPACITY_M3} m³")
    print(f"  CHP: {config.CHP_CAPACITY_KW} kW")
    print(f"  Boiler: {config.BOILER_CAPACITY_KW} kW")

    # Run complete analysis
    results = run_complete_analysis()

    # Print final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"\nEnergy:")
    print(f"  Annual generation: {results['carbon']['annual_energy_kwh']:,.0f} kWh")
    print(f"\nEnvironmental Impact:")
    print(f"  CO2 avoided: {results['carbon']['co2_avoided_tons']:,.0f} tons/year")
    print(f"  Carbon market tier: {results['carbon']['optimal_tier']}")
    print(f"\nEconomics:")
    print(f"  Carbon revenue: ${results['carbon']['carbon_revenue_annual']:,.0f}/year")

    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE!")
    print("="*70)
    print(f"\nAll results saved to: {config.OUTPUT_DIR}")
    print(f"  - Summary: {config.OUTPUT_DIR}/summary.json")
    print(f"  - Network: {config.OUTPUT_DIR}/network.nc")
    print(f"  - Plots: {config.OUTPUT_DIR}/plots/")
    print(f"  - Publication figures: {config.OUTPUT_DIR}/publication_figures/")

    return results


if __name__ == "__main__":
    results = main()
