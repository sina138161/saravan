#!/usr/bin/env python3
"""
Test script to verify compatibility wrapper imports
"""

print("Testing compatibility wrapper imports...")

try:
    # Test wind_turbines wrapper
    print("\n1. Testing wind_turbines wrapper...")
    from saravan_wind_water_nexus.models.wind_turbines import WindTurbineModels
    turbines = WindTurbineModels()
    power = turbines.calculate_power_output('HAWT', 12, 50, 25)
    specs = turbines.get_turbine_specs('HAWT')
    print(f"   ✓ WindTurbineModels works (power: {power:.2f} kW, capacity: {specs['capacity']} kW)")

    # Test water_treatment wrapper
    print("\n2. Testing water_treatment wrapper...")
    from saravan_wind_water_nexus.models.water_treatment import WaterSystemModel
    water = WaterSystemModel()
    well_capacity = water.quality_system['groundwater_well']['extraction_limit_m3_per_hour']
    print(f"   ✓ WaterSystemModel works (well capacity: {well_capacity} m³/h)")

    # Test carbon_market wrapper
    print("\n3. Testing carbon_market wrapper...")
    from saravan_wind_water_nexus.models.carbon_market import CarbonMarketModel
    carbon = CarbonMarketModel()
    print(f"   ✓ CarbonMarketModel works")

    # Test thermal_systems wrapper
    print("\n4. Testing thermal_systems wrapper...")
    from saravan_wind_water_nexus.models.thermal_systems import CHPModel, GasBoilerModel
    chp = CHPModel()
    boiler = GasBoilerModel()
    chp_specs = chp.get_specs()
    boiler_specs = boiler.get_specs()
    print(f"   ✓ CHPModel works (efficiency: {chp_specs['electrical_efficiency']:.0%})")
    print(f"   ✓ GasBoilerModel works (efficiency: {boiler_specs['thermal_efficiency']:.0%})")

    # Test sludge_biogas wrapper
    print("\n5. Testing sludge_biogas wrapper...")
    from saravan_wind_water_nexus.models.sludge_biogas import SludgeManagementSystem, CCUSystem, MarketModel
    sludge = SludgeManagementSystem()
    ccu = CCUSystem()
    market = MarketModel()
    compost_specs = sludge.get_composting_specs()
    digester_specs = sludge.get_digester_specs()
    ccu_specs = ccu.get_specs()
    prices = market.get_prices()
    print(f"   ✓ SludgeManagementSystem works (biogas yield: {digester_specs['biogas_yield_m3_per_kg']} m³/kg)")
    print(f"   ✓ CCUSystem works (capture efficiency: {ccu_specs['capture_efficiency']:.0%})")
    print(f"   ✓ MarketModel works (electricity price: ${prices['electricity_per_kwh']}/kWh)")

    print("\n" + "="*60)
    print("✅ All compatibility wrapper imports successful!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
