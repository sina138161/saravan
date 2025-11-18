"""
Simplified PyPSA Network Builder for Wind-Water Nexus
Focuses on wind turbines, battery storage, and water pumping
"""

import pypsa
import numpy as np
import pandas as pd
from typing import Dict, Optional
from wind_turbine_models import WindTurbineModels
from water_system_model import WaterSystemModel
from carbon_market_model import CarbonMarketModel


class WindWaterNetworkBuilder:
    """
    Build PyPSA network for wind-water-energy optimization

    Simplified version focusing on:
    - Wind turbines (HAWT, VAWT, Bladeless)
    - Battery storage
    - Water pumping and storage
    - Carbon revenue integration
    """

    def __init__(self, time_series_data: Dict):
        """
        Initialize network builder

        Args:
            time_series_data: Dictionary with wind, dust, temperature, water_demand
        """
        self.data = time_series_data
        self.turbines = WindTurbineModels()
        self.water = WaterSystemModel()
        self.carbon = CarbonMarketModel()

        # Network will be created later
        self.network = None

    def build_network(self, turbine_mix: Dict = None,
                     battery_size_kwh: float = 1000,
                     water_tank_capacity_m3: float = 2500,
                     water_tank_elevation_m: float = 25) -> pypsa.Network:
        """
        Build complete PyPSA network

        Args:
            turbine_mix: Dict with number of each turbine type
                        e.g., {'HAWT': 5, 'VAWT': 3, 'Bladeless': 15}
            battery_size_kwh: Battery capacity in kWh
            water_tank_capacity_m3: Water tank size in m³
            water_tank_elevation_m: Tank elevation in meters

        Returns:
            PyPSA Network object
        """

        # Default turbine mix
        if turbine_mix is None:
            turbine_mix = {
                'HAWT': 5,
                'VAWT': 3,
                'Bladeless': 15
            }

        print(f"\n{'='*70}")
        print("BUILDING PYPSA NETWORK")
        print(f"{'='*70}")

        # Get time series
        hours = len(self.data['wind'])
        timestamps = pd.date_range(start='2025-01-01', periods=hours, freq='H')

        # Create network
        self.network = pypsa.Network()
        self.network.set_snapshots(timestamps)

        print(f"\nSnapshots: {len(self.network.snapshots)}")

        # Add carriers
        self._add_carriers()

        # Add buses
        self._add_buses()

        # Add wind turbines
        self._add_wind_turbines(turbine_mix)

        # Add battery storage
        self._add_battery_storage(battery_size_kwh)

        # Add water system
        self._add_water_system(water_tank_capacity_m3, water_tank_elevation_m)

        # Add loads (electricity and water demand)
        self._add_loads()

        print(f"\n✅ Network built successfully!")
        print(f"   Buses: {len(self.network.buses)}")
        print(f"   Generators: {len(self.network.generators)}")
        print(f"   Stores: {len(self.network.stores)}")
        print(f"   Links: {len(self.network.links)}")
        print(f"   Loads: {len(self.network.loads)}")

        return self.network

    def _add_carriers(self):
        """Add carriers to network"""
        carriers = [
            ('electricity', 'Electricity'),
            ('wind', 'Wind energy'),
            ('natural_gas', 'Natural gas'),
            ('water', 'Water'),
        ]

        for carrier_name, nice_name in carriers:
            self.network.add("Carrier", carrier_name, nice_name=nice_name)

        print(f"\n⚡ Added {len(carriers)} carriers")

    def _add_buses(self):
        """Add buses to network"""
        buses = [
            'electricity',
            'water_raw',  # Raw groundwater
            'water_agricultural',  # Primary treated water
            'water_potable',  # Secondary treated water (potable)
            'wastewater_municipal',  # Urban wastewater
            'wastewater_discharge',  # Discharge sink for excess wastewater
        ]

        for bus in buses:
            self.network.add("Bus", bus)

        print(f"\n📍 Added {len(buses)} buses: {buses}")

    def _add_wind_turbines(self, turbine_mix: Dict):
        """Add wind turbines with dust impact"""

        print(f"\n🌪️  Adding wind turbines...")

        wind_speeds = self.data['wind']['wind_speed_ms'].values
        dust_pm10 = self.data['dust']['pm10_ugm3'].values
        temperatures = self.data['temperature']['temperature_c'].values

        total_capacity = 0

        for turbine_type, n_turbines in turbine_mix.items():
            if n_turbines == 0:
                continue

            # Calculate power output for each hour
            hourly_power = np.array([
                self.turbines.calculate_power_output(
                    turbine_type, v, d, t
                )
                for v, d, t in zip(wind_speeds, dust_pm10, temperatures)
            ])

            # Turbine specs
            spec = self.turbines.get_turbine_specs(turbine_type)
            capacity_per_unit = spec['capacity']

            # Scale to number of turbines
            total_power = hourly_power * n_turbines
            total_cap = capacity_per_unit * n_turbines

            # Capacity factor time series (p_max_pu)
            p_max_pu = total_power / total_cap if total_cap > 0 else np.zeros_like(total_power)

            # Add to network
            self.network.add(
                "Generator",
                f"Wind_{turbine_type}",
                bus="electricity",
                p_nom=total_cap,
                p_max_pu=p_max_pu,
                p_min_pu=0,
                marginal_cost=0,  # No fuel cost for wind
                capital_cost=spec['capex'] * total_cap,  # $/kW * kW
                carrier='wind'
            )

            total_capacity += total_cap

            # Calculate expected annual energy
            annual_energy = total_power.sum()
            cf = annual_energy / (total_cap * len(wind_speeds)) if total_cap > 0 else 0

            print(f"   {turbine_type}: {n_turbines} × {capacity_per_unit}kW = {total_cap}kW")
            print(f"      Annual energy: {annual_energy:,.0f} kWh, CF: {cf*100:.1f}%")
            print(f"      CAPEX: ${spec['capex'] * total_cap:,.0f}")

        print(f"\n   TOTAL wind capacity: {total_capacity:.0f} kW")

    def _add_battery_storage(self, capacity_kwh: float):
        """Add battery storage"""

        print(f"\n🔋 Adding battery storage...")

        # LiFePO4 specs
        efficiency = 0.92
        capex_per_kwh = 300

        self.network.add(
            "Store",
            "Battery",
            bus="electricity",
            e_nom=capacity_kwh,
            e_cyclic=True,  # State of charge at end = start
            e_initial=capacity_kwh * 0.5,  # Start at 50%
            standing_losses=0.01,  # 1% per hour self-discharge
            capital_cost=capex_per_kwh * capacity_kwh
        )

        print(f"   Capacity: {capacity_kwh} kWh")
        print(f"   Standing losses: 1%/hour")
        print(f"   CAPEX: ${capex_per_kwh * capacity_kwh:,.0f}")

    def _add_water_system(self, tank_capacity_m3: float, elevation_m: float):
        """Add comprehensive water system with treatment and recycling"""

        print(f"\n💧 Adding comprehensive water system...")

        # Get water demand data
        water_df = self.data['water_demand']
        agri_demand = water_df['agricultural_m3h'].values[:len(self.network.snapshots)]
        urban_demand = water_df['urban_m3h'].values[:len(self.network.snapshots)]

        max_agri = agri_demand.max()
        max_urban = urban_demand.max()

        # 1. Groundwater Well Pumping (electricity → raw water)
        max_well_extraction = self.water.quality_system['groundwater_well']['extraction_limit_m3_per_hour']
        pumping_power_per_m3 = 1.2  # kWh per m³ for deep well
        water_energy_equiv = 1.0  # Treat 1 m³/h as 1 kW for unit consistency

        # IMPORTANT: In PyPSA, efficiency must be <= 1.0
        # So we make water the reference (bus0) and electricity consumed (bus1)
        self.network.add(
            "Link",
            "Groundwater_Well",
            bus0="electricity",
            bus1="water_raw",
            p_nom=max_well_extraction * pumping_power_per_m3,  # Max power (kW electricity)
            efficiency=water_energy_equiv / pumping_power_per_m3,  # 1.0/1.2 = 0.833 water per elec
            marginal_cost=0.5,  # Small cost to prefer recycling
            capital_cost=50000
        )

        # 2. Primary Treatment (raw → agricultural quality)
        # CRITICAL FIX: efficiency must be <= 1.0 in PyPSA
        # Make water_raw the reference (bus0), not electricity
        primary_energy = self.water.quality_system['primary_treatment']['energy_kwh_per_m3']

        self.network.add(
            "Link",
            "Primary_Treatment",
            bus0="water_raw",  # Input water (reference)
            bus1="electricity",  # Electricity consumed
            bus2="water_agricultural",  # Output water
            p_nom=max_agri * water_energy_equiv,  # Max flow in kW-equiv water
            efficiency=primary_energy / water_energy_equiv,  # 0.15/1.0 = 0.15 kW elec per kW water
            efficiency2=1.0,  # 1 kW water out per 1 kW water in
            marginal_cost=0,
            capital_cost=80000
        )

        # 3. Secondary Treatment (agricultural → potable)
        # Same fix: water as reference
        secondary_energy = self.water.quality_system['secondary_treatment']['energy_kwh_per_m3']

        self.network.add(
            "Link",
            "Secondary_Treatment",
            bus0="water_agricultural",  # Input water (reference)
            bus1="electricity",  # Electricity consumed
            bus2="water_potable",  # Output water
            p_nom=max_urban * water_energy_equiv,  # Max flow in kW-equiv water
            efficiency=secondary_energy / water_energy_equiv,  # 0.50/1.0 = 0.50
            efficiency2=1.0,  # 1 kW water out per 1 kW water in
            marginal_cost=0,
            capital_cost=150000
        )

        # 4. Wastewater Generation (urban water use → wastewater)
        # 80% of urban water becomes wastewater
        wastewater_factor = 0.80

        self.network.add(
            "Link",
            "Wastewater_Generation",
            bus0="water_potable",
            bus1="wastewater_municipal",
            p_nom=max_urban,
            efficiency=wastewater_factor,  # 80% becomes wastewater
            marginal_cost=0,
            capital_cost=0  # No cost for generation
        )

        # 5. Wastewater Primary Treatment (wastewater → agricultural reuse)
        # Same fix: wastewater as reference
        ww_primary_energy = self.water.quality_system['wastewater_primary_treatment']['energy_kwh_per_m3']
        ww_primary_recovery = self.water.quality_system['wastewater_primary_treatment']['recovery_rate']

        self.network.add(
            "Link",
            "Wastewater_Primary_Treatment",
            bus0="wastewater_municipal",  # Input wastewater (reference)
            bus1="electricity",  # Electricity consumed
            bus2="water_agricultural",  # Output water
            p_nom=max_urban * wastewater_factor * water_energy_equiv,  # Max flow kW-equiv
            efficiency=ww_primary_energy / water_energy_equiv,  # 0.25/1.0 = 0.25
            efficiency2=ww_primary_recovery,  # 0.85 output per input
            marginal_cost=0,
            capital_cost=100000
        )

        # 6. Wastewater Secondary Treatment (wastewater → potable reuse)
        # Same fix: wastewater as reference
        ww_secondary_energy = self.water.quality_system['wastewater_secondary_treatment']['energy_kwh_per_m3']
        ww_secondary_recovery = self.water.quality_system['wastewater_secondary_treatment']['recovery_rate']

        self.network.add(
            "Link",
            "Wastewater_Secondary_Treatment",
            bus0="wastewater_municipal",  # Input wastewater (reference)
            bus1="electricity",  # Electricity consumed
            bus2="water_potable",  # Output water
            p_nom=max_urban * wastewater_factor * water_energy_equiv,  # Max flow kW-equiv
            efficiency=ww_secondary_energy / water_energy_equiv,  # 0.60/1.0 = 0.60
            efficiency2=ww_secondary_recovery,  # 0.75 output per input
            marginal_cost=0,
            capital_cost=200000
        )

        # 7. Wastewater Discharge (for excess wastewater that cannot be recycled)
        # This acts as a slack variable to prevent infeasibility
        self.network.add(
            "Link",
            "Wastewater_Discharge",
            bus0="wastewater_municipal",
            bus1="wastewater_discharge",  # Discharge sink
            p_nom=max_urban * wastewater_factor,
            efficiency=1.0,  # Full discharge (no conversion)
            marginal_cost=5  # Small cost to prefer recycling over discharge
        )

        # Add a Store on discharge bus to absorb excess wastewater
        self.network.add(
            "Store",
            "Wastewater_Discharge_Sink",
            bus="wastewater_discharge",
            e_nom=1e6,  # Very large capacity (unlimited sink)
            e_cyclic=False,
            e_initial=0
        )

        # 8. Water Storage Tank
        # Only agricultural sector needs storage (for irrigation scheduling)
        # Urban and industrial sectors have direct supply
        self.network.add(
            "Store",
            "Agricultural_Water_Tank",
            bus="water_agricultural",
            e_nom=tank_capacity_m3 * water_energy_equiv,  # Full tank for agricultural (kWh-eq)
            e_cyclic=False,
            e_initial=tank_capacity_m3 * 0.5 * water_energy_equiv,  # Start at 50%
            capital_cost=60000
        )

        print(f"\n   Groundwater well:")
        print(f"      Max extraction: {max_well_extraction} m³/h")
        print(f"      Pumping energy: {pumping_power_per_m3} kWh/m³")
        print(f"\n   Water treatment:")
        print(f"      Primary (→ agricultural): {primary_energy} kWh/m³")
        print(f"      Secondary (→ potable): {secondary_energy} kWh/m³")
        print(f"\n   Wastewater treatment & recycling:")
        print(f"      Primary (→ agricultural): {ww_primary_energy} kWh/m³, {ww_primary_recovery*100}% recovery")
        print(f"      Secondary (→ potable): {ww_secondary_energy} kWh/m³, {ww_secondary_recovery*100}% recovery")
        print(f"      Discharge sink: Available as fallback (${5}/m³ penalty)")
        print(f"\n   Storage:")
        print(f"      Agricultural tank: {tank_capacity_m3:.0f} m³ (100% for irrigation scheduling)")
        print(f"      Urban: Direct supply (no storage)")
        print(f"      Discharge sink: Unlimited capacity")

    def _add_loads(self):
        """Add electricity and water demand loads"""

        print(f"\n📊 Adding demand loads...")

        # Electricity demand from various sectors
        if 'electricity_demand' in self.data:
            elec_df = self.data['electricity_demand']

            # Urban electricity demand (only sector in Saravan)
            urban_demand = elec_df['urban_kwh'].values[:len(self.network.snapshots)]
            self.network.add(
                "Load",
                "Urban_Electricity",
                bus="electricity",
                p_set=urban_demand
            )

            # NOTE: No industrial sector in Saravan
            # NOTE: Treatment electricity is NOT added as a separate load because
            # the treatment Links (Primary_Treatment, Secondary_Treatment, etc.)
            # already consume electricity when they operate. Adding it as a load
            # would double-count the treatment energy consumption!

            total_elec = urban_demand
            print(f"\n   Electricity demand (direct loads only):")
            print(f"      Urban: {urban_demand.mean():.1f} kW (avg), {urban_demand.sum():,.0f} kWh (total)")
            print(f"      NOTE: No industrial sector in Saravan")
            print(f"      NOTE: Pumping & treatment energy handled by Links, not loads")
        else:
            # Fallback to simple baseload
            baseload_kw = 100
            elec_load = np.ones(len(self.network.snapshots)) * baseload_kw
            self.network.add(
                "Load",
                "Electricity_Demand",
                bus="electricity",
                p_set=elec_load
            )
            print(f"   Electricity baseload: {baseload_kw} kW")

        # Add grid connection with natural gas consumption
        # Grid power is generated from natural gas (efficiency ~45%)
        self.network.add(
            "Generator",
            "Grid_Gas_Power",
            bus="electricity",
            p_nom=5000,  # 5 MW capacity
            marginal_cost=120,  # $/MWh (natural gas price + grid markup)
            capital_cost=0,  # Grid already exists
            efficiency=0.45,  # 45% gas-to-electricity efficiency
            carrier="natural_gas"
        )

        # Add expensive backup for emergency only
        self.network.add(
            "Generator",
            "Emergency_Backup",
            bus="electricity",
            p_nom=2000,
            marginal_cost=2000,  # Very expensive ($2/kWh)
            capital_cost=0,
            carrier='electricity'
        )

        # Water demand - separate by sector
        # IMPORTANT: Convert m³/h to kW-equivalent for PyPSA
        water_energy_equiv = 1.0  # 1 m³/h = 1 kW-equivalent
        water_df = self.data['water_demand']

        # Agricultural water demand
        agri_demand_m3h = water_df['agricultural_m3h'].values[:len(self.network.snapshots)]
        agri_demand_kw = agri_demand_m3h * water_energy_equiv
        self.network.add(
            "Load",
            "Agricultural_Water",
            bus="water_agricultural",
            p_set=agri_demand_kw  # In kW-equivalent
        )

        # Urban water demand
        urban_water_demand_m3h = water_df['urban_m3h'].values[:len(self.network.snapshots)]
        urban_water_demand_kw = urban_water_demand_m3h * water_energy_equiv
        self.network.add(
            "Load",
            "Urban_Water",
            bus="water_potable",
            p_set=urban_water_demand_kw  # In kW-equivalent
        )

        print(f"\n   Water demand:")
        print(f"      Agricultural: {agri_demand_m3h.mean():.1f} m³/h (avg), {agri_demand_m3h.sum():.0f} m³ (total)")
        print(f"      Urban: {urban_water_demand_m3h.mean():.1f} m³/h (avg), {urban_water_demand_m3h.sum():.0f} m³ (total)")
        print(f"\n   Grid connection:")
        print(f"      Gas-fired power: 5 MW capacity, $0.12/kWh, 45% efficiency")
        print(f"      Emergency backup: 2 MW capacity, $2/kWh")

    def optimize(self, solver: str = 'highs') -> Dict:
        """
        Run optimization

        Args:
            solver: Solver name

        Returns:
            Results dictionary
        """

        if self.network is None:
            raise ValueError("Network not built. Call build_network() first.")

        print(f"\n{'='*70}")
        print("RUNNING OPTIMIZATION")
        print(f"{'='*70}")
        print(f"Solver: {solver}")

        # Check network consistency before optimization
        print(f"\n🔍 Checking network consistency...")
        self.network.consistency_check()

        import time
        start_time = time.time()

        # Run optimization
        status = self.network.optimize(solver_name=solver)

        elapsed = time.time() - start_time

        # Extract status and objective
        if isinstance(status, tuple):
            status_str = status[0]
        else:
            status_str = str(status)

        # Get objective if available
        objective = None
        try:
            if hasattr(self.network, 'objective'):
                objective = float(self.network.objective)
            elif hasattr(self.network, 'objective_constant'):
                # Some PyPSA versions store it differently
                objective = float(self.network.objective_constant)
        except (AttributeError, TypeError, ValueError):
            # If optimization failed or objective not available
            objective = None

        print(f"\n{'='*70}")
        if status_str == 'ok' and objective is not None:
            print(f"✅ Optimization successful!")
            print(f"   Time: {elapsed:.2f} seconds")
            print(f"   Objective: ${objective:,.2f}")
        else:
            print(f"❌ Optimization failed!")
            print(f"   Status: {status_str}")
            if objective is None:
                print(f"   Problem is infeasible - cannot satisfy all constraints")
                print(f"\n   Likely causes:")
                print(f"   - Water demand exceeds pumping capacity")
                print(f"   - Insufficient wind generation for loads")
                print(f"   - Check system sizing and demand profiles")
            else:
                print(f"   Objective: ${objective:,.2f}")

        # Calculate results
        results = self._extract_results(status_str, objective, elapsed)

        return results

    def _extract_results(self, status_str: str, objective: float, elapsed: float) -> Dict:
        """Extract optimization results"""

        results = {
            'objective': objective if objective is not None else 0,
            'execution_time': elapsed,
            'network': self.network,
            'status': status_str
        }

        # If failed or infeasible, return minimal results without extracting details
        if status_str != 'ok' or objective is None or objective == 0:
            print(f"\n⚠️  Optimization did not complete successfully - skipping detailed results extraction")
            return results

        # Extract generator outputs
        print(f"\n{'='*70}")
        print("RESULTS SUMMARY")
        print(f"{'='*70}")

        print(f"\nWind Generation:")
        for gen in self.network.generators.index:
            if gen not in self.network.generators_t.p.columns:
                continue  # Skip if no data
            total_gen = self.network.generators_t.p[gen].sum()
            capacity = self.network.generators.loc[gen, 'p_nom']
            cf = total_gen / (capacity * len(self.network.snapshots)) if capacity > 0 else 0
            print(f"   {gen}: {total_gen:,.0f} kWh, CF: {cf*100:.1f}%")

        # Battery statistics
        if 'Battery' in self.network.stores.index:
            soc = self.network.stores_t.e['Battery']
            capacity = self.network.stores.loc['Battery', 'e_nom']
            cycles = soc.diff().clip(lower=0).sum() / capacity if capacity > 0 else 0

            print(f"\nBattery:")
            print(f"   Capacity: {capacity:.0f} kWh")
            print(f"   Cycles: {cycles:.2f}")
            print(f"   Min SOC: {soc.min():.1f} kWh ({soc.min()/capacity*100:.1f}%)")
            print(f"   Max SOC: {soc.max():.1f} kWh ({soc.max()/capacity*100:.1f}%)")

        # Water system
        if 'Water_Tank' in self.network.stores.index:
            tank_level = self.network.stores_t.e['Water_Tank']
            capacity = self.network.stores.loc['Water_Tank', 'e_nom']

            print(f"\nWater Tank:")
            print(f"   Capacity: {capacity:.0f} m³")
            print(f"   Min level: {tank_level.min():.1f} m³ ({tank_level.min()/capacity*100:.1f}%)")
            print(f"   Max level: {tank_level.max():.1f} m³ ({tank_level.max()/capacity*100:.1f}%)")
            print(f"   Avg level: {tank_level.mean():.1f} m³ ({tank_level.mean()/capacity*100:.1f}%)")

        # Water pumped
        if 'Water_Pump' in self.network.links_t.p0.columns:
            total_pumped = self.network.links_t.p0['Water_Pump'].sum()
            print(f"\nWater Pumped:")
            print(f"   Total: {total_pumped:,.0f} m³")

        return results


# Example usage
if __name__ == "__main__":
    from data_generator import SaravanDataGenerator

    # Generate data
    print("Generating Saravan data...")
    generator = SaravanDataGenerator(random_seed=42)
    dataset = generator.generate_complete_dataset(hours=168)  # 1 week

    # Build network
    builder = WindWaterNetworkBuilder(dataset)

    turbine_mix = {
        'HAWT': 2,
        'VAWT': 1,
        'Bladeless': 5
    }

    network = builder.build_network(
        turbine_mix=turbine_mix,
        battery_size_kwh=500,
        water_tank_capacity_m3=1000,
        water_tank_elevation_m=25
    )

    # Optimize
    results = builder.optimize(solver='highs')

    print(f"\n{'='*70}")
    print("✅ COMPLETE!")
    print(f"{'='*70}")
