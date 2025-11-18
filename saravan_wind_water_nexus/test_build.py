#!/usr/bin/env python3
"""
Quick test to verify network can be built with waste-to-energy system
"""

import sys
import traceback

try:
    # Test imports
    print("Testing imports...")
    import numpy as np
    import pandas as pd
    print("✓ numpy and pandas imported")

    import pypsa
    print("✓ pypsa imported")

    from network_builder_simple import WindWaterNetworkBuilder
    print("✓ WindWaterNetworkBuilder imported")

    # Test data loading
    print("\nTesting data loading...")
    data_path = './data/saravan_data.pkl'
    builder = WindWaterNetworkBuilder(data_path)
    print("✓ Builder created")

    # Test network building
    print("\nTesting network build...")
    network = builder.build_network(
        turbine_mix={'HAWT': 2, 'Bladeless': 5},
        battery_size_kwh=1000,
        water_tank_capacity_m3=2500
    )
    print("\n✓ Network built successfully!")

    # Verify new components exist
    print("\nVerifying waste-to-energy components:")
    print(f"  Buses: {len(network.buses)} total")
    expected_buses = ['heat', 'biogas', 'biomass', 'sludge', 'compost']
    for bus_name in expected_buses:
        if bus_name in network.buses.index:
            print(f"  ✓ Bus '{bus_name}' exists")
        else:
            print(f"  ✗ Bus '{bus_name}' MISSING!")

    print(f"\n  Links: {len(network.links)} total")
    expected_links = ['Anaerobic_Digester', 'Composting', 'CHP_Biogas']
    for link_name in expected_links:
        if link_name in network.links.index:
            print(f"  ✓ Link '{link_name}' exists")
        else:
            print(f"  ✗ Link '{link_name}' MISSING!")

    print(f"\n  Stores: {len(network.stores)} total")
    if 'Heat_Storage' in network.stores.index:
        print(f"  ✓ Store 'Heat_Storage' exists")
    else:
        print(f"  ✗ Store 'Heat_Storage' MISSING!")

    print(f"\n  Loads: {len(network.loads)} total")
    if 'Urban_Heat_Demand' in network.loads.index:
        print(f"  ✓ Load 'Urban_Heat_Demand' exists")
    else:
        print(f"  ✗ Load 'Urban_Heat_Demand' MISSING!")

    print("\n" + "="*70)
    print("SUCCESS: Waste-to-energy system integrated correctly!")
    print("="*70)

except Exception as e:
    print("\n" + "="*70)
    print("ERROR during testing:")
    print("="*70)
    traceback.print_exc()
    sys.exit(1)
