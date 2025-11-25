#!/usr/bin/env python3
"""
Test script to verify all module imports work correctly
"""

print("Testing imports...")

try:
    # Test main module
    print("\n1. Testing main module import...")
    from saravan_wind_water_nexus import models
    print("   ✓ Main module imported")

    # Test base classes
    print("\n2. Testing base classes...")
    from saravan_wind_water_nexus.models import TechnologyBase, EconomicCalculator
    print("   ✓ Base classes imported")

    # Test wind turbines
    print("\n3. Testing wind turbines...")
    from saravan_wind_water_nexus.models import HAWT, Bladeless
    print("   ✓ Wind turbines imported")

    # Test thermal systems
    print("\n4. Testing thermal systems...")
    from saravan_wind_water_nexus.models import GasMicroturbine, HeatRecovery, GasBoiler
    print("   ✓ Thermal systems imported")

    # Test biogas systems
    print("\n5. Testing biogas systems...")
    from saravan_wind_water_nexus.models import Composting, AnaerobicDigester, Dewatering, CCU
    print("   ✓ Biogas systems imported")

    # Test water systems
    print("\n6. Testing water systems...")
    from saravan_wind_water_nexus.models import GroundwaterWell, WaterTreatment, WastewaterTreatment, ElevatedStorage
    print("   ✓ Water systems imported")

    # Test storage systems
    print("\n7. Testing storage systems...")
    from saravan_wind_water_nexus.models import BatteryESS, ThermalStorage
    print("   ✓ Storage systems imported")

    # Test carbon market
    print("\n8. Testing carbon market...")
    from saravan_wind_water_nexus.models import CarbonMarket, CarbonMarketTier
    print("   ✓ Carbon market imported")

    # Test instantiation of each class
    print("\n9. Testing class instantiation...")

    hawt = HAWT()
    print("   ✓ HAWT instantiated")

    bladeless = Bladeless()
    print("   ✓ Bladeless instantiated")

    gt = GasMicroturbine()
    print("   ✓ GasMicroturbine instantiated")

    hr = HeatRecovery()
    print("   ✓ HeatRecovery instantiated")

    gb = GasBoiler()
    print("   ✓ GasBoiler instantiated")

    comp = Composting()
    print("   ✓ Composting instantiated")

    ad = AnaerobicDigester()
    print("   ✓ AnaerobicDigester instantiated")

    dew = Dewatering()
    print("   ✓ Dewatering instantiated")

    ccu = CCU()
    print("   ✓ CCU instantiated")

    gw = GroundwaterWell()
    print("   ✓ GroundwaterWell instantiated")

    wt = WaterTreatment()
    print("   ✓ WaterTreatment instantiated")

    wwt = WastewaterTreatment()
    print("   ✓ WastewaterTreatment instantiated")

    es = ElevatedStorage()
    print("   ✓ ElevatedStorage instantiated")

    bess = BatteryESS()
    print("   ✓ BatteryESS instantiated")

    ts = ThermalStorage()
    print("   ✓ ThermalStorage instantiated")

    cm = CarbonMarket()
    print("   ✓ CarbonMarket instantiated")

    print("\n" + "="*60)
    print("✅ All imports and instantiations successful!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
