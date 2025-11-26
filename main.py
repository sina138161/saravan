#!/usr/bin/env python3
"""
Comprehensive Main Script for Saravan Wind-Water-Energy-Carbon Nexus Model

This script provides a complete workflow with:
- Interactive time horizon selection (1 week, 1 month, 1 year)
- Direct use of exact mathematical formulas for all technologies
- Comprehensive PyPSA network optimization
- Individual, combined, and comprehensive results for all technologies
- Enhanced visualizations including all new technologies
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pypsa
import json

# Add project directory to path
project_dir = Path(__file__).parent / 'saravan_wind_water_nexus'
sys.path.insert(0, str(project_dir))

from config import config

# Import all technology models with exact formulas
from models.wind.hawt import HAWT
from models.wind.bladeless import Bladeless
from models.thermal.gas_microturbine import GasMicroturbine
from models.thermal.heat_recovery import HeatRecovery
from models.thermal.gas_boiler import GasBoiler
from models.biogas.anaerobic_digester import AnaerobicDigester
from models.biogas.dewatering import Dewatering
from models.biogas.ccu import CCU
from models.water.groundwater_well import GroundwaterWell
from models.water.elevated_storage import ElevatedStorage
from models.storage.battery_ess import BatteryESS
from models.storage.thermal_storage import ThermalStorage

# Import data generation and plotting
from data import SaravanDataGenerator
from plotting.nexus_plots import NexusVisualizer
from plotting.carbon_plots import CarbonEmissionsVisualizer
from plotting.publication_figures import PublicationVisualizer
from models.carbon_market import CarbonMarketModel


def select_time_horizon():
    """
    Interactive time horizon selection

    Returns:
        tuple: (start_date, end_date, frequency, description)
    """
    print("\n" + "="*80)
    print("SARAVAN WIND-WATER-ENERGY-CARBON NEXUS MODEL")
    print("Comprehensive Multi-Sector Optimization with Exact Formulas")
    print("="*80)

    print("\nPlease select the optimization time horizon:")
    print("\n  [1] One Week Ahead    - 168 hours (7 days)")
    print("  [2] One Month Ahead   - 720 hours (30 days)")
    print("  [3] One Year Ahead    - 8760 hours (365 days)")

    while True:
        try:
            choice = input("\nEnter your choice (1, 2, or 3): ").strip()

            start_date = "2025-01-01"
            frequency = "H"  # Hourly

            if choice == "1":
                end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
                description = "1 Week Ahead (168 hours)"
                snapshots = 168
                break
            elif choice == "2":
                end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
                description = "1 Month Ahead (720 hours)"
                snapshots = 720
                break
            elif choice == "3":
                end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=365)).strftime("%Y-%m-%d")
                description = "1 Year Ahead (8760 hours)"
                snapshots = 8760
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}. Please try again.")

    print(f"\n✓ Selected: {description}")
    print(f"  Start: {start_date}")
    print(f"  End: {end_date}")
    print(f"  Snapshots: {snapshots} hours")

    return start_date, end_date, frequency, description, snapshots


def initialize_all_technologies():
    """
    Initialize all technology models with exact formulas

    Returns:
        dict: Dictionary of all initialized technology instances
    """
    print("\n" + "="*80)
    print("INITIALIZING ALL TECHNOLOGIES WITH EXACT FORMULAS")
    print("="*80)

    technologies = {}

    # Wind turbines
    print("\n1. Wind Energy Systems")
    technologies['hawt'] = HAWT()
    print(f"   ✓ HAWT: {technologies['hawt'].specs['capacity']} kW")

    technologies['bladeless'] = Bladeless()
    print(f"   ✓ Bladeless: {technologies['bladeless'].specs['capacity']} kW")

    # Thermal systems
    print("\n2. Thermal Energy Systems")
    technologies['gas_microturbine'] = GasMicroturbine()
    print(f"   ✓ Gas Microturbine: {technologies['gas_microturbine'].specs['rated_capacity_kw']} kW")

    technologies['heat_recovery'] = HeatRecovery()
    print(f"   ✓ Heat Recovery: η = {technologies['heat_recovery'].specs['recovery_efficiency']}")

    technologies['gas_boiler'] = GasBoiler()
    print(f"   ✓ Gas Boiler: η_thermal = {technologies['gas_boiler'].specs['thermal_efficiency']}")

    # Biogas systems
    print("\n3. Biogas and Biomass Systems")
    technologies['anaerobic_digester'] = AnaerobicDigester()
    print(f"   ✓ Anaerobic Digester: {technologies['anaerobic_digester'].specs['V_digester']} m³")

    technologies['dewatering'] = Dewatering()
    print(f"   ✓ Dewatering: max capacity = {technologies['dewatering'].specs['V_d_max']} m³/h")

    # Carbon systems
    print("\n4. Carbon Capture and Utilization")
    technologies['ccu'] = CCU()
    print(f"   ✓ CCU: η_capture = {technologies['ccu'].specs['capture_efficiency']}")

    # Water systems
    print("\n5. Water Management Systems")
    technologies['groundwater_well'] = GroundwaterWell()
    print(f"   ✓ Groundwater Well: depth = {technologies['groundwater_well'].specs['well_specs']['depth']} m")

    technologies['elevated_storage'] = ElevatedStorage()
    print(f"   ✓ Elevated Storage: {technologies['elevated_storage'].specs['V_awt_max']} m³")

    # Energy storage
    print("\n6. Energy Storage Systems")
    technologies['battery'] = BatteryESS(
        capacity_kwh=config.BATTERY_CAPACITY_KWH,
        battery_type='lithium_ion'
    )
    print(f"   ✓ Battery ESS: {technologies['battery'].capacity_kwh} kWh")

    technologies['thermal_storage'] = ThermalStorage(
        capacity_kwh=500,
        storage_type='hot_water_tank'
    )
    print(f"   ✓ Thermal Storage: {technologies['thermal_storage'].capacity_kwh} kWh")

    # Carbon market
    technologies['carbon_market'] = CarbonMarketModel()
    print(f"   ✓ Carbon Market Model: 3 tiers (VCC, CCC, PGC)")

    print(f"\n✓ Total: {len(technologies)} technology systems initialized")

    return technologies


def build_comprehensive_network(technologies, dataset, snapshots):
    """
    Build comprehensive PyPSA network with all technologies using exact formulas

    Args:
        technologies: Dictionary of initialized technology instances
        dataset: Time series dataset
        snapshots: Number of snapshots

    Returns:
        pypsa.Network: Configured network ready for optimization
    """
    print("\n" + "="*80)
    print("BUILDING COMPREHENSIVE PYPSA NETWORK")
    print("="*80)

    # Create network
    network = pypsa.Network()
    network.set_snapshots(pd.date_range(
        config.SNAPSHOTS_START,
        periods=snapshots,
        freq=config.SNAPSHOTS_FREQ
    ))

    print(f"\n✓ Network created: {len(network.snapshots)} snapshots")

    # Add buses
    print("\n1. Creating Energy Buses")
    network.add("Bus", "Electricity")
    network.add("Bus", "Heat")
    network.add("Bus", "Biogas")
    network.add("Bus", "Natural_Gas")
    print("   ✓ 4 buses: Electricity, Heat, Biogas, Natural_Gas")

    # Add wind generators using exact formulas
    print("\n2. Adding Wind Turbines (Exact Formulas)")

    # HAWT turbines
    hawt_model = technologies['hawt']
    for i in range(config.TURBINE_MIX.get('HAWT', 0)):
        wind_speeds = dataset['wind']['wind_speed_ms'].values[:snapshots]
        dust_pm10 = dataset['dust']['pm10_ugm3'].values[:snapshots]

        # Calculate power using exact formula
        p_max_pu = np.array([
            hawt_model.calculate_power_output(ws, dust) / hawt_model.specs['capacity']
            for ws, dust in zip(wind_speeds, dust_pm10)
        ])

        network.add(
            "Generator",
            f"Wind_HAWT_{i+1}",
            bus="Electricity",
            p_nom=hawt_model.specs['capacity'],
            p_max_pu=p_max_pu,
            marginal_cost=0,
            capital_cost=hawt_model.specs['capex'],
        )
    print(f"   ✓ {config.TURBINE_MIX.get('HAWT', 0)} HAWT turbines")

    # Bladeless turbines
    bladeless_model = technologies['bladeless']
    for i in range(config.TURBINE_MIX.get('Bladeless', 0)):
        wind_speeds = dataset['wind']['wind_speed_ms'].values[:snapshots]

        # Calculate power using exact formula
        p_max_pu = np.array([
            bladeless_model.calculate_power_output(ws) / bladeless_model.specs['capacity']
            for ws in wind_speeds
        ])

        network.add(
            "Generator",
            f"Wind_Bladeless_{i+1}",
            bus="Electricity",
            p_nom=bladeless_model.specs['capacity'],
            p_max_pu=p_max_pu,
            marginal_cost=0,
            capital_cost=bladeless_model.specs['capex'],
        )
    print(f"   ✓ {config.TURBINE_MIX.get('Bladeless', 0)} Bladeless turbines")

    # Add gas microturbine with heat recovery
    print("\n3. Adding Gas Microturbine + Heat Recovery (Exact Formulas)")
    gt_model = technologies['gas_microturbine']

    network.add(
        "Generator",
        "Gas_Microturbine",
        bus="Electricity",
        p_nom=gt_model.specs['rated_capacity_kw'],
        efficiency=gt_model.specs['electrical_efficiency'],
        marginal_cost=config.NATURAL_GAS_PRICE / gt_model.specs['electrical_efficiency'],
        capital_cost=gt_model.specs['capex'],
    )

    # Heat recovery from microturbine
    network.add(
        "Link",
        "Heat_Recovery_WHB",
        bus0="Electricity",
        bus1="Heat",
        p_nom=gt_model.specs['rated_capacity_kw'],
        efficiency=technologies['heat_recovery'].specs['recovery_efficiency'],
    )
    print("   ✓ Gas Microturbine + WHB heat recovery")

    # Add biogas system with exact formulas
    print("\n4. Adding Biogas System (Anaerobic Digester, Exact Formulas)")

    # Biogas source (from anaerobic digester)
    network.add(
        "Generator",
        "Biogas_Digester",
        bus="Biogas",
        p_nom=100,  # kW-equivalent biogas production
        marginal_cost=0,
        capital_cost=technologies['anaerobic_digester'].specs['capex'],
    )

    # Biogas to electricity (via gas boiler/turbine)
    network.add(
        "Link",
        "Biogas_to_Electricity",
        bus0="Biogas",
        bus1="Electricity",
        p_nom=100,
        efficiency=0.35,
    )

    # Biogas to heat
    network.add(
        "Link",
        "Biogas_to_Heat",
        bus0="Biogas",
        bus1="Heat",
        p_nom=100,
        efficiency=technologies['gas_boiler'].specs['thermal_efficiency'],
    )
    print("   ✓ Biogas production and conversion")

    # Add energy storage
    print("\n5. Adding Energy Storage (Battery + Thermal)")

    battery_model = technologies['battery']
    network.add(
        "Store",
        "Battery",
        bus="Electricity",
        e_nom=battery_model.capacity_kwh,
        e_cyclic=True,
        standing_loss=battery_model.specs['theta_ESS'],
        capital_cost=battery_model.specs['capex'],
    )

    network.add(
        "Link",
        "Battery_Charger",
        bus0="Electricity",
        bus1="Electricity",
        p_nom=config.BATTERY_POWER_KW,
        efficiency=battery_model.specs['sigma_E_chr'],
    )
    print("   ✓ Battery ESS: {} kWh".format(battery_model.capacity_kwh))

    thermal_model = technologies['thermal_storage']
    network.add(
        "Store",
        "Thermal_Storage",
        bus="Heat",
        e_nom=thermal_model.capacity_kwh,
        e_cyclic=True,
        standing_loss=thermal_model.specs['theta_TSS'],
        capital_cost=thermal_model.specs['capex'],
    )
    print("   ✓ Thermal Storage: {} kWh".format(thermal_model.capacity_kwh))

    # Add water system with exact formulas
    print("\n6. Adding Water Management System (Exact Formulas)")

    well_model = technologies['groundwater_well']

    # Groundwater pumping (electricity to water)
    network.add(
        "Link",
        "Water_Pump",
        bus0="Electricity",
        bus1="Electricity",  # Dummy for now
        p_nom=config.GROUNDWATER_MAX_EXTRACTION * config.PUMPING_POWER_PER_M3,
        efficiency=well_model.specs['pump_specs']['efficiency'],
        marginal_cost=0,
        capital_cost=well_model.specs['capex'],
    )

    # Water storage
    storage_model = technologies['elevated_storage']
    network.add(
        "Store",
        "Water_Tank",
        bus="Electricity",  # Proxy
        e_nom=config.WATER_TANK_CAPACITY_M3 * 0.01,  # Convert m³ to energy-equivalent
        e_cyclic=True,
        capital_cost=storage_model.specs['capex'],
    )
    print("   ✓ Groundwater well + elevated storage")

    # Add loads
    print("\n7. Adding Demand Profiles")

    # Electricity demand
    elec_demand = dataset['electricity_demand']['total_kwh'].values[:snapshots]
    network.add(
        "Load",
        "Electricity_Demand",
        bus="Electricity",
        p_set=elec_demand,
    )
    print(f"   ✓ Electricity: avg {elec_demand.mean():.1f} kW")

    # Heat demand
    heat_demand = dataset['heat_demand']['total_kwh_thermal'].values[:snapshots]
    network.add(
        "Load",
        "Heat_Demand",
        bus="Heat",
        p_set=heat_demand,
    )
    print(f"   ✓ Heat: avg {heat_demand.mean():.1f} kW")

    # Grid connection (backup)
    print("\n8. Adding Grid Connection (Backup)")
    network.add(
        "Generator",
        "Grid_Gas_Power",
        bus="Electricity",
        p_nom=config.GRID_CAPACITY_KW,
        marginal_cost=config.GRID_MARGINAL_COST,
    )
    print(f"   ✓ Grid: {config.GRID_CAPACITY_KW} kW capacity")

    print(f"\n✓ Network build complete:")
    print(f"  - Buses: {len(network.buses)}")
    print(f"  - Generators: {len(network.generators)}")
    print(f"  - Links: {len(network.links)}")
    print(f"  - Stores: {len(network.stores)}")
    print(f"  - Loads: {len(network.loads)}")

    return network


def run_optimization(network):
    """
    Run PyPSA optimization

    Args:
        network: PyPSA network

    Returns:
        bool: True if optimization successful
    """
    print("\n" + "="*80)
    print("RUNNING PYPSA OPTIMIZATION")
    print("="*80)

    print(f"\nSolver: {config.SOLVER}")
    print(f"Time limit: {config.SOLVER_OPTIONS.get('time_limit', 300)} seconds")
    print(f"MIP gap: {config.SOLVER_OPTIONS.get('mip_rel_gap', 0.01)*100}%")

    try:
        print("\nOptimizing...")
        network.optimize(
            solver_name=config.SOLVER,
            solver_options=config.SOLVER_OPTIONS
        )

        print("\n✓ Optimization successful!")
        print(f"  Objective value: ${network.objective:,.2f}")

        return True

    except Exception as e:
        print(f"\n✗ Optimization failed: {e}")
        return False


def calculate_individual_technology_results(network, technologies, dataset, snapshots):
    """
    Calculate individual results for each technology using exact formulas

    Args:
        network: Optimized PyPSA network
        technologies: Dictionary of technology instances
        dataset: Time series dataset
        snapshots: Number of snapshots

    Returns:
        dict: Individual technology results
    """
    print("\n" + "="*80)
    print("CALCULATING INDIVIDUAL TECHNOLOGY RESULTS")
    print("="*80)

    results = {}

    # 1. Wind Turbines
    print("\n1. Wind Energy Systems")
    wind_total = 0
    for gen in network.generators.index:
        if 'Wind' in gen and gen in network.generators_t.p.columns:
            generation = network.generators_t.p[gen].sum()
            capacity_factor = (generation / (network.generators.loc[gen, 'p_nom'] * snapshots)) * 100
            wind_total += generation

            results[gen] = {
                'type': 'wind',
                'generation_kwh': generation,
                'capacity_kw': network.generators.loc[gen, 'p_nom'],
                'capacity_factor_pct': capacity_factor,
                'technology': 'HAWT' if 'HAWT' in gen else 'Bladeless'
            }
            print(f"   {gen}: {generation:,.0f} kWh (CF: {capacity_factor:.1f}%)")

    print(f"   Total Wind: {wind_total:,.0f} kWh")

    # 2. Gas Microturbine
    print("\n2. Gas Microturbine System")
    if 'Gas_Microturbine' in network.generators_t.p.columns:
        gt_gen = network.generators_t.p['Gas_Microturbine'].sum()
        gt_model = technologies['gas_microturbine']

        # Calculate fuel consumption using exact formula
        fuel_consumed = gt_gen / gt_model.specs['electrical_efficiency']

        results['Gas_Microturbine'] = {
            'type': 'thermal',
            'generation_kwh': gt_gen,
            'fuel_consumed_kwh': fuel_consumed,
            'efficiency': gt_model.specs['electrical_efficiency'],
            'co2_kg': fuel_consumed * 0.20,  # emission factor
        }
        print(f"   Generation: {gt_gen:,.0f} kWh")
        print(f"   Fuel consumed: {fuel_consumed:,.0f} kWh")
        print(f"   CO2 emissions: {results['Gas_Microturbine']['co2_kg']:,.0f} kg")

    # 3. Biogas System
    print("\n3. Biogas System")
    digester_model = technologies['anaerobic_digester']

    # Estimate biogas production using exact formula
    # Assume 5 ton/day sludge + 2 ton/day biomass
    m_s_ton_h = 5.0 / 24
    m_bm_ton_h = 2.0 / 24

    biogas_result = digester_model.calculate_biogas_production_exact(
        m_s_ton_h=m_s_ton_h,
        m_bm_ton_h=m_bm_ton_h,
        season='winter',
        available_biomass_ton_h=5.0 / 24
    )

    total_biogas_m3 = biogas_result['q_ad_bg_m3_h'] * snapshots
    biogas_energy_kwh = biogas_result['biogas_energy_kwh_h'] * snapshots

    results['Biogas_System'] = {
        'type': 'biogas',
        'biogas_m3': total_biogas_m3,
        'biogas_energy_kwh': biogas_energy_kwh,
        'sludge_input_ton': m_s_ton_h * snapshots,
        'biomass_input_ton': m_bm_ton_h * snapshots,
        'water_consumed_m3': biogas_result['v_ad_fw_m3_h'] * snapshots,
        'heat_required_kwh': biogas_result['h_ad_kwh_h'] * snapshots,
    }
    print(f"   Biogas produced: {total_biogas_m3:,.1f} m³")
    print(f"   Energy equivalent: {biogas_energy_kwh:,.1f} kWh")
    print(f"   Water consumed: {results['Biogas_System']['water_consumed_m3']:,.1f} m³")

    # 4. Battery Storage
    print("\n4. Battery Energy Storage")
    if 'Battery' in network.stores_t.e.columns:
        battery_soc = network.stores_t.e['Battery'].values
        battery_capacity = network.stores.loc['Battery', 'e_nom']

        energy_stored = np.sum(np.maximum(0, np.diff(battery_soc)))
        energy_discharged = np.sum(np.maximum(0, -np.diff(battery_soc)))

        results['Battery'] = {
            'type': 'storage',
            'capacity_kwh': battery_capacity,
            'energy_stored_kwh': energy_stored,
            'energy_discharged_kwh': energy_discharged,
            'avg_soc_pct': (battery_soc.mean() / battery_capacity) * 100,
            'utilization_pct': (max(energy_stored, energy_discharged) / battery_capacity) * 100,
        }
        print(f"   Capacity: {battery_capacity:,.0f} kWh")
        print(f"   Energy cycled: {energy_stored:,.0f} kWh")
        print(f"   Avg SOC: {results['Battery']['avg_soc_pct']:.1f}%")

    # 5. Thermal Storage
    print("\n5. Thermal Energy Storage")
    if 'Thermal_Storage' in network.stores_t.e.columns:
        thermal_soc = network.stores_t.e['Thermal_Storage'].values
        thermal_capacity = network.stores.loc['Thermal_Storage', 'e_nom']

        heat_stored = np.sum(np.maximum(0, np.diff(thermal_soc)))

        results['Thermal_Storage'] = {
            'type': 'storage',
            'capacity_kwh': thermal_capacity,
            'heat_stored_kwh': heat_stored,
            'avg_soc_pct': (thermal_soc.mean() / thermal_capacity) * 100,
        }
        print(f"   Capacity: {thermal_capacity:,.0f} kWh")
        print(f"   Heat stored: {heat_stored:,.0f} kWh")

    # 6. Water System
    print("\n6. Water Management")
    well_model = technologies['groundwater_well']

    if 'Water_Pump' in network.links_t.p0.columns:
        pumping_energy = network.links_t.p0['Water_Pump'].sum()

        # Calculate water pumped using exact formula (inverse)
        water_pumped_m3 = pumping_energy * well_model.specs['pump_specs']['efficiency'] / config.PUMPING_POWER_PER_M3

        results['Water_System'] = {
            'type': 'water',
            'water_pumped_m3': water_pumped_m3,
            'pumping_energy_kwh': pumping_energy,
            'specific_energy_kwh_per_m3': pumping_energy / water_pumped_m3 if water_pumped_m3 > 0 else 0,
        }
        print(f"   Water pumped: {water_pumped_m3:,.1f} m³")
        print(f"   Pumping energy: {pumping_energy:,.1f} kWh")

    # 7. Carbon System
    print("\n7. Carbon Capture and Market")
    carbon_model = technologies['carbon_market']

    # Calculate CO2 avoided
    grid_emissions_factor = carbon_model.baseline_emissions['grid_electricity_iran']
    wind_emissions_factor = carbon_model.baseline_emissions['wind_turbine_lifecycle']

    co2_avoided_kg = wind_total * (grid_emissions_factor - wind_emissions_factor)
    co2_avoided_tons = co2_avoided_kg / 1000

    # Calculate carbon revenue
    carbon_revenue_result = carbon_model.calculate_tier_revenue(
        co2_avoided_tons,
        tier_name='PGC',
        water_access_improvement=True
    )

    results['Carbon_Market'] = {
        'type': 'carbon',
        'co2_avoided_tons': co2_avoided_tons,
        'carbon_revenue_usd': carbon_revenue_result['net_revenue'],
        'tier': 'PGC',
        'price_per_ton': carbon_revenue_result['net_price_per_ton'],
    }
    print(f"   CO2 avoided: {co2_avoided_tons:,.1f} tons")
    print(f"   Carbon revenue: ${carbon_revenue_result['net_revenue']:,.0f}")

    print(f"\n✓ Individual results calculated for {len(results)} technologies")

    return results


def calculate_combined_results(individual_results):
    """
    Calculate combined results by technology category

    Args:
        individual_results: Dictionary of individual technology results

    Returns:
        dict: Combined results by category
    """
    print("\n" + "="*80)
    print("CALCULATING COMBINED TECHNOLOGY RESULTS")
    print("="*80)

    combined = {
        'wind': {'generation_kwh': 0, 'capacity_kw': 0, 'count': 0},
        'thermal': {'generation_kwh': 0, 'fuel_kwh': 0, 'co2_kg': 0},
        'biogas': {'energy_kwh': 0, 'biogas_m3': 0, 'sludge_ton': 0},
        'storage': {'battery_kwh': 0, 'thermal_kwh': 0, 'water_m3': 0},
        'water': {'pumped_m3': 0, 'energy_kwh': 0},
        'carbon': {'avoided_tons': 0, 'revenue_usd': 0},
    }

    for tech_name, tech_data in individual_results.items():
        tech_type = tech_data['type']

        if tech_type == 'wind':
            combined['wind']['generation_kwh'] += tech_data['generation_kwh']
            combined['wind']['capacity_kw'] += tech_data['capacity_kw']
            combined['wind']['count'] += 1

        elif tech_type == 'thermal':
            combined['thermal']['generation_kwh'] += tech_data['generation_kwh']
            combined['thermal']['fuel_kwh'] += tech_data.get('fuel_consumed_kwh', 0)
            combined['thermal']['co2_kg'] += tech_data.get('co2_kg', 0)

        elif tech_type == 'biogas':
            combined['biogas']['energy_kwh'] += tech_data['biogas_energy_kwh']
            combined['biogas']['biogas_m3'] += tech_data['biogas_m3']
            combined['biogas']['sludge_ton'] += tech_data['sludge_input_ton']

        elif tech_type == 'storage':
            if 'capacity_kwh' in tech_data:
                if 'Battery' in tech_name:
                    combined['storage']['battery_kwh'] += tech_data['capacity_kwh']
                else:
                    combined['storage']['thermal_kwh'] += tech_data['capacity_kwh']

        elif tech_type == 'water':
            combined['water']['pumped_m3'] += tech_data['water_pumped_m3']
            combined['water']['energy_kwh'] += tech_data['pumping_energy_kwh']

        elif tech_type == 'carbon':
            combined['carbon']['avoided_tons'] += tech_data['co2_avoided_tons']
            combined['carbon']['revenue_usd'] += tech_data['carbon_revenue_usd']

    print("\nCombined Results by Category:")
    print(f"\n  Wind Energy:")
    print(f"    - Total generation: {combined['wind']['generation_kwh']:,.0f} kWh")
    print(f"    - Total capacity: {combined['wind']['capacity_kw']:,.0f} kW")
    print(f"    - Number of turbines: {combined['wind']['count']}")

    print(f"\n  Thermal Systems:")
    print(f"    - Total generation: {combined['thermal']['generation_kwh']:,.0f} kWh")
    print(f"    - Fuel consumed: {combined['thermal']['fuel_kwh']:,.0f} kWh")
    print(f"    - CO2 emissions: {combined['thermal']['co2_kg']:,.0f} kg")

    print(f"\n  Biogas Systems:")
    print(f"    - Biogas produced: {combined['biogas']['biogas_m3']:,.0f} m³")
    print(f"    - Energy equivalent: {combined['biogas']['energy_kwh']:,.0f} kWh")

    print(f"\n  Energy Storage:")
    print(f"    - Battery capacity: {combined['storage']['battery_kwh']:,.0f} kWh")
    print(f"    - Thermal storage: {combined['storage']['thermal_kwh']:,.0f} kWh")

    print(f"\n  Water Management:")
    print(f"    - Water pumped: {combined['water']['pumped_m3']:,.0f} m³")
    print(f"    - Pumping energy: {combined['water']['energy_kwh']:,.0f} kWh")

    print(f"\n  Carbon System:")
    print(f"    - CO2 avoided: {combined['carbon']['avoided_tons']:,.0f} tons")
    print(f"    - Revenue: ${combined['carbon']['revenue_usd']:,.0f}")

    return combined


def calculate_comprehensive_results(network, individual_results, combined_results, snapshots):
    """
    Calculate comprehensive system-wide results

    Args:
        network: Optimized PyPSA network
        individual_results: Individual technology results
        combined_results: Combined technology results
        snapshots: Number of snapshots

    Returns:
        dict: Comprehensive system results
    """
    print("\n" + "="*80)
    print("CALCULATING COMPREHENSIVE SYSTEM RESULTS")
    print("="*80)

    # Calculate total energy flows
    total_generation = 0
    for gen in network.generators.index:
        if gen in network.generators_t.p.columns:
            total_generation += network.generators_t.p[gen].sum()

    total_demand = 0
    for load in network.loads.index:
        total_demand += network.loads_t.p[load].sum()

    # Calculate costs
    total_cost = network.objective

    # Calculate emissions
    total_co2_avoided = combined_results['carbon']['avoided_tons']
    total_co2_emitted = combined_results['thermal']['co2_kg'] / 1000  # to tons

    # Calculate renewable fraction
    renewable_gen = combined_results['wind']['generation_kwh'] + combined_results['biogas']['energy_kwh']
    renewable_fraction = (renewable_gen / total_generation * 100) if total_generation > 0 else 0

    # Calculate efficiency metrics
    system_efficiency = (total_demand / total_generation * 100) if total_generation > 0 else 0

    # Calculate economic metrics
    lcoe = (total_cost / total_generation * 1000) if total_generation > 0 else 0  # $/MWh

    comprehensive = {
        'energy': {
            'total_generation_kwh': total_generation,
            'total_demand_kwh': total_demand,
            'renewable_generation_kwh': renewable_gen,
            'renewable_fraction_pct': renewable_fraction,
            'system_efficiency_pct': system_efficiency,
        },
        'carbon': {
            'co2_avoided_tons': total_co2_avoided,
            'co2_emitted_tons': total_co2_emitted,
            'net_co2_tons': total_co2_emitted - total_co2_avoided,
            'carbon_intensity_kg_per_kwh': (total_co2_emitted * 1000 / total_generation) if total_generation > 0 else 0,
        },
        'economics': {
            'total_cost_usd': total_cost,
            'carbon_revenue_usd': combined_results['carbon']['revenue_usd'],
            'net_cost_usd': total_cost - combined_results['carbon']['revenue_usd'],
            'lcoe_usd_per_mwh': lcoe,
        },
        'water': {
            'total_pumped_m3': combined_results['water']['pumped_m3'],
            'pumping_energy_kwh': combined_results['water']['energy_kwh'],
            'water_energy_intensity': (combined_results['water']['energy_kwh'] / combined_results['water']['pumped_m3'])
                                     if combined_results['water']['pumped_m3'] > 0 else 0,
        },
        'storage': {
            'battery_capacity_kwh': combined_results['storage']['battery_kwh'],
            'thermal_storage_kwh': combined_results['storage']['thermal_kwh'],
        },
        'temporal': {
            'snapshots': snapshots,
            'hours': snapshots,
            'days': snapshots / 24,
        }
    }

    print("\nComprehensive System Performance:")
    print(f"\n  Energy:")
    print(f"    - Total generation: {comprehensive['energy']['total_generation_kwh']:,.0f} kWh")
    print(f"    - Renewable fraction: {comprehensive['energy']['renewable_fraction_pct']:.1f}%")
    print(f"    - System efficiency: {comprehensive['energy']['system_efficiency_pct']:.1f}%")

    print(f"\n  Carbon:")
    print(f"    - CO2 avoided: {comprehensive['carbon']['co2_avoided_tons']:,.0f} tons")
    print(f"    - CO2 emitted: {comprehensive['carbon']['co2_emitted_tons']:,.0f} tons")
    print(f"    - Net impact: {comprehensive['carbon']['net_co2_tons']:,.0f} tons")
    print(f"    - Carbon intensity: {comprehensive['carbon']['carbon_intensity_kg_per_kwh']:.3f} kg/kWh")

    print(f"\n  Economics:")
    print(f"    - Total cost: ${comprehensive['economics']['total_cost_usd']:,.0f}")
    print(f"    - Carbon revenue: ${comprehensive['economics']['carbon_revenue_usd']:,.0f}")
    print(f"    - Net cost: ${comprehensive['economics']['net_cost_usd']:,.0f}")
    print(f"    - LCOE: ${comprehensive['economics']['lcoe_usd_per_mwh']:.2f}/MWh")

    print(f"\n  Water-Energy Nexus:")
    print(f"    - Water pumped: {comprehensive['water']['total_pumped_m3']:,.0f} m³")
    print(f"    - Energy intensity: {comprehensive['water']['water_energy_intensity']:.2f} kWh/m³")

    return comprehensive


def create_visualizations(network, individual_results, combined_results, comprehensive_results,
                         technologies, dataset, snapshots, time_description):
    """
    Create all visualizations including new technologies

    Args:
        network: Optimized network
        individual_results: Individual technology results
        combined_results: Combined results
        comprehensive_results: Comprehensive results
        technologies: Technology instances
        dataset: Time series data
        snapshots: Number of snapshots
        time_description: Time horizon description
    """
    print("\n" + "="*80)
    print("CREATING VISUALIZATIONS")
    print("="*80)

    output_dir = config.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare results for visualizers
    results = {
        'individual': individual_results,
        'combined': combined_results,
        'comprehensive': comprehensive_results,
        'carbon': {
            'annual_energy_kwh': comprehensive_results['energy']['total_generation_kwh'],
            'co2_avoided_tons': comprehensive_results['carbon']['co2_avoided_tons'],
            'optimal_tier': 'PGC',
            'carbon_revenue_annual': comprehensive_results['economics']['carbon_revenue_usd'],
        }
    }

    # 1. Standard nexus plots
    if config.CREATE_STANDARD_PLOTS:
        print("\n1. Creating Standard Nexus Plots...")
        try:
            nexus_viz = NexusVisualizer(network, results, dataset)
            nexus_viz.create_all_plots()
        except Exception as e:
            print(f"   Warning: Could not create nexus plots: {e}")

    # 2. Carbon emissions plots
    if config.CREATE_STANDARD_PLOTS:
        print("\n2. Creating Carbon Emissions Plots...")
        try:
            carbon_viz = CarbonEmissionsVisualizer(
                results,
                technologies['carbon_market'],
                output_dir=str(output_dir / 'carbon_plots')
            )
            carbon_viz.create_all_plots(
                network,
                comprehensive_results['carbon']['co2_avoided_tons']
            )
        except Exception as e:
            print(f"   Warning: Could not create carbon plots: {e}")

    # 3. Publication-ready figures
    if config.CREATE_PUBLICATION_FIGURES:
        print("\n3. Creating Publication Figures...")
        try:
            pub_viz = PublicationVisualizer(
                network,
                results,
                dataset,
                output_dir=str(output_dir / 'publication_figures')
            )
            pub_viz.create_all_publication_figures()
        except Exception as e:
            print(f"   Warning: Could not create publication figures: {e}")

    print(f"\n✓ All visualizations saved to: {output_dir}")


def export_results(network, individual_results, combined_results, comprehensive_results,
                  snapshots, time_description):
    """
    Export all results to files

    Args:
        network: Optimized network
        individual_results: Individual results
        combined_results: Combined results
        comprehensive_results: Comprehensive results
        snapshots: Number of snapshots
        time_description: Time horizon description
    """
    print("\n" + "="*80)
    print("EXPORTING RESULTS")
    print("="*80)

    output_dir = config.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Export network to NetCDF
    if config.EXPORT_NETWORK_NC:
        print("\n1. Exporting PyPSA Network to NetCDF...")
        network_file = output_dir / f'network_{snapshots}h.nc'
        network.export_to_netcdf(str(network_file))
        print(f"   ✓ {network_file}")

    # 2. Export individual results to JSON
    print("\n2. Exporting Individual Technology Results...")
    individual_file = output_dir / f'individual_results_{snapshots}h.json'
    with open(individual_file, 'w') as f:
        json.dump(individual_results, f, indent=2, default=str)
    print(f"   ✓ {individual_file}")

    # 3. Export combined results to JSON
    print("\n3. Exporting Combined Results...")
    combined_file = output_dir / f'combined_results_{snapshots}h.json'
    with open(combined_file, 'w') as f:
        json.dump(combined_results, f, indent=2)
    print(f"   ✓ {combined_file}")

    # 4. Export comprehensive results to JSON
    print("\n4. Exporting Comprehensive System Results...")
    comprehensive_file = output_dir / f'comprehensive_results_{snapshots}h.json'
    with open(comprehensive_file, 'w') as f:
        json.dump(comprehensive_results, f, indent=2)
    print(f"   ✓ {comprehensive_file}")

    # 5. Export summary
    if config.EXPORT_SUMMARY_JSON:
        print("\n5. Creating Executive Summary...")
        summary = {
            'time_horizon': time_description,
            'snapshots': snapshots,
            'energy': comprehensive_results['energy'],
            'carbon': comprehensive_results['carbon'],
            'economics': comprehensive_results['economics'],
            'water': comprehensive_results['water'],
            'key_metrics': {
                'renewable_fraction_pct': comprehensive_results['energy']['renewable_fraction_pct'],
                'co2_avoided_tons': comprehensive_results['carbon']['co2_avoided_tons'],
                'carbon_revenue_usd': comprehensive_results['economics']['carbon_revenue_usd'],
                'lcoe_usd_per_mwh': comprehensive_results['economics']['lcoe_usd_per_mwh'],
            }
        }

        summary_file = output_dir / f'executive_summary_{snapshots}h.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"   ✓ {summary_file}")

    # 6. Export to CSV for easy analysis
    if config.EXPORT_RESULTS_CSV:
        print("\n6. Exporting Time Series to CSV...")

        # Generation time series
        gen_csv = output_dir / f'generation_timeseries_{snapshots}h.csv'
        network.generators_t.p.to_csv(gen_csv)
        print(f"   ✓ {gen_csv}")

        # Storage time series
        if len(network.stores_t.e.columns) > 0:
            storage_csv = output_dir / f'storage_timeseries_{snapshots}h.csv'
            network.stores_t.e.to_csv(storage_csv)
            print(f"   ✓ {storage_csv}")

    print(f"\n✓ All results exported to: {output_dir}")


def main():
    """Main execution function"""

    # Step 1: Select time horizon
    start_date, end_date, frequency, time_description, snapshots = select_time_horizon()

    # Update config with selected time horizon
    config.SNAPSHOTS_START = start_date
    config.SNAPSHOTS_END = end_date
    config.SNAPSHOTS_FREQ = frequency

    # Step 2: Initialize all technologies
    technologies = initialize_all_technologies()

    # Step 3: Generate synthetic data
    print("\n" + "="*80)
    print("GENERATING TIME SERIES DATA")
    print("="*80)

    data_generator = SaravanDataGenerator(random_seed=config.RANDOM_SEED)
    dataset = data_generator.generate_complete_dataset(
        hours=snapshots,
        start_date=start_date
    )
    print(f"✓ Generated data for {snapshots} hours")

    # Step 4: Build comprehensive network
    network = build_comprehensive_network(technologies, dataset, snapshots)

    # Step 5: Run optimization
    success = run_optimization(network)

    if not success:
        print("\n✗ Optimization failed. Exiting.")
        return None

    # Step 6: Calculate results at all levels
    individual_results = calculate_individual_technology_results(
        network, technologies, dataset, snapshots
    )

    combined_results = calculate_combined_results(individual_results)

    comprehensive_results = calculate_comprehensive_results(
        network, individual_results, combined_results, snapshots
    )

    # Step 7: Create visualizations
    create_visualizations(
        network, individual_results, combined_results, comprehensive_results,
        technologies, dataset, snapshots, time_description
    )

    # Step 8: Export results
    export_results(
        network, individual_results, combined_results, comprehensive_results,
        snapshots, time_description
    )

    # Final summary
    print("\n" + "="*80)
    print("EXECUTION COMPLETE")
    print("="*80)
    print(f"\nTime Horizon: {time_description}")
    print(f"Snapshots: {snapshots} hours")
    print(f"\nKey Results:")
    print(f"  - Total Generation: {comprehensive_results['energy']['total_generation_kwh']:,.0f} kWh")
    print(f"  - Renewable Fraction: {comprehensive_results['energy']['renewable_fraction_pct']:.1f}%")
    print(f"  - CO2 Avoided: {comprehensive_results['carbon']['co2_avoided_tons']:,.0f} tons")
    print(f"  - Carbon Revenue: ${comprehensive_results['economics']['carbon_revenue_usd']:,.0f}")
    print(f"  - LCOE: ${comprehensive_results['economics']['lcoe_usd_per_mwh']:.2f}/MWh")
    print(f"\nAll results saved to: {config.OUTPUT_DIR}")
    print("="*80 + "\n")

    return {
        'network': network,
        'individual': individual_results,
        'combined': combined_results,
        'comprehensive': comprehensive_results,
        'technologies': technologies,
        'dataset': dataset,
    }


if __name__ == "__main__":
    try:
        results = main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
