"""
Network Building Script

Constructs the PyPSA network for the Saravan Wind-Water-Energy-Carbon Nexus
including all components: turbines, battery, water system, thermal systems,
biogas, and carbon capture.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from network_builder_simple import WindWaterNetworkBuilder
from config import config


def build_network(dataset, turbine_mix=None, battery_kwh=None,
                  water_tank_m3=None, water_tank_elevation_m=None):
    """
    Build PyPSA network with all components

    Args:
        dataset: Data generated from prepare_data.py
        turbine_mix: Dict of turbine counts (default from config)
        battery_kwh: Battery capacity (default from config)
        water_tank_m3: Water tank size (default from config)
        water_tank_elevation_m: Tank elevation (default from config)

    Returns:
        PyPSA network object
    """

    # Use config defaults if not specified
    if turbine_mix is None:
        turbine_mix = config.TURBINE_MIX

    if battery_kwh is None:
        battery_kwh = config.BATTERY_CAPACITY_KWH

    if water_tank_m3 is None:
        water_tank_m3 = config.WATER_TANK_CAPACITY_M3

    if water_tank_elevation_m is None:
        water_tank_elevation_m = config.WATER_TANK_ELEVATION_M

    print("="*70)
    print("NETWORK CONSTRUCTION")
    print("="*70)
    print(f"Turbine mix: {turbine_mix}")
    print(f"Battery: {battery_kwh} kWh")
    print(f"Water tank: {water_tank_m3} m³ at {water_tank_elevation_m}m")

    # Build network
    network_builder = WindWaterNetworkBuilder(dataset)
    network = network_builder.build_network(
        turbine_mix=turbine_mix,
        battery_size_kwh=battery_kwh,
        water_tank_capacity_m3=water_tank_m3,
        water_tank_elevation_m=water_tank_elevation_m
    )

    # Print network summary
    print("\nNetwork Summary:")
    print(f"  Buses: {len(network.buses)}")
    print(f"  Generators: {len(network.generators)}")
    print(f"  Loads: {len(network.loads)}")
    print(f"  Links: {len(network.links)}")
    print(f"  Stores: {len(network.stores)}")
    print(f"  Storage Units: {len(network.storage_units)}")

    return network, network_builder


if __name__ == "__main__":
    from prepare_data import prepare_data

    # Prepare data first
    dataset = prepare_data()

    # Build network
    network, builder = build_network(dataset)

    print("\n✅ Network construction complete!")
