"""
Quick test to debug optimization issues
"""

from data_generator import SaravanDataGenerator
from network_builder_simple import WindWaterNetworkBuilder

# Generate minimal dataset
print("Generating test data...")
generator = SaravanDataGenerator(random_seed=42)
dataset = generator.generate_complete_dataset(hours=24)  # Just 1 day

# Build network
print("\nBuilding network...")
builder = WindWaterNetworkBuilder(dataset)

network = builder.build_network(
    turbine_mix={'HAWT': 1, 'VAWT': 0, 'Bladeless': 0},  # Just 1 turbine
    battery_size_kwh=100,
    water_tank_capacity_m3=500,
    water_tank_elevation_m=25
)

# Print network summary
print("\n" + "="*70)
print("NETWORK SUMMARY")
print("="*70)
print(f"Buses: {len(network.buses)}")
print(f"  {list(network.buses.index)}")
print(f"\nGenerators: {len(network.generators)}")
for gen in network.generators.index:
    print(f"  {gen}: p_nom={network.generators.loc[gen, 'p_nom']:.1f} kW")
print(f"\nLoads: {len(network.loads)}")
for load in network.loads.index:
    p_set = network.loads_t.p_set[load]
    print(f"  {load}: avg={p_set.mean():.1f} kW, max={p_set.max():.1f} kW")
print(f"\nLinks: {len(network.links)}")
for link in network.links.index:
    print(f"  {link}: p_nom={network.links.loc[link, 'p_nom']:.1f} kW")
print(f"\nStores: {len(network.stores)}")
for store in network.stores.index:
    print(f"  {store}: e_nom={network.stores.loc[store, 'e_nom']:.1f}")

# Try optimization
print("\n" + "="*70)
print("TESTING OPTIMIZATION")
print("="*70)

try:
    results = builder.optimize(solver='highs')
    print(f"\nStatus: {results['status']}")
    print(f"Objective: ${results['objective']:,.2f}")
except Exception as e:
    print(f"\n❌ Error during optimization: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
