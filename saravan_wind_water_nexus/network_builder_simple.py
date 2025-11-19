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
from thermal_carbon_systems import CHPModel, GasBoilerModel, SludgeManagementSystem, CCUSystem, MarketModel


class WindWaterNetworkBuilder:
    """
    Build PyPSA network for wind-water-energy optimization

    Simplified version focusing on:
    - Wind turbines (HAWT, Bladeless)
    - Battery storage
    - Water pumping and storage
    - Power grid connection (gas-based electricity)
    - Carbon revenue integration
    """

    def __init__(self, time_series_data: Dict):
        """
        Initialize network builder

        Args:
            time_series_data: Dictionary with wind, dust, temperature, water_demand, heat_demand, biomass
        """
        self.data = time_series_data
        self.turbines = WindTurbineModels()
        self.water = WaterSystemModel()
        self.carbon = CarbonMarketModel()
        self.chp = CHPModel()
        self.boiler = GasBoilerModel()
        self.sludge_system = SludgeManagementSystem()
        self.ccu = CCUSystem()
        self.market = MarketModel()

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

        # Default turbine mix (VAWT removed as per requirement)
        if turbine_mix is None:
            turbine_mix = {
                'HAWT': 5,
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

        # Add thermal and carbon systems (CHP, boiler, sludge, CCU, market)
        self._add_thermal_carbon_systems()

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
            ('heat', 'Heat (thermal energy)'),
            ('biogas', 'Biogas (from digester)'),
            ('biomass', 'Biomass (organic matter)'),
            ('sludge', 'Sludge (from wastewater)'),
            ('compost', 'Compost (fertilizer)'),
            ('digestate', 'Digestate (fertilizer)'),
            ('co2', 'Carbon dioxide'),
            ('captured_co2', 'Captured CO2 (pure)'),
        ]

        for carrier_name, nice_name in carriers:
            self.network.add("Carrier", carrier_name, nice_name=nice_name)

        print(f"\n⚡ Added {len(carriers)} carriers")

    def _add_buses(self):
        """Add buses to network"""
        buses = [
            # Energy buses
            'electricity',
            'natural_gas',
            'heat',
            'biogas',

            # Water buses
            'water_raw',  # Raw groundwater
            'water_agricultural',  # Primary treated water
            'water_potable',  # Secondary treated water (potable)
            'wastewater_municipal',  # Urban wastewater
            'wastewater_discharge',  # Discharge sink for excess wastewater

            # Organic matter buses
            'biomass',
            'sludge',

            # Products buses
            'compost',
            'digestate',

            # Carbon buses
            'co2_emissions',  # CO2 from combustion
            'co2_captured',  # Captured and purified CO2

            # Market buses
            'market_compost',
            'market_digestate',
            'market_co2',
            'market_electricity',
            'market_heat',
        ]

        for bus in buses:
            self.network.add("Bus", bus)

        print(f"\n📍 Added {len(buses)} buses")

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

        # 5. Wastewater Primary Treatment (wastewater → agricultural reuse + sludge)
        # Same fix: wastewater as reference
        ww_primary_energy = self.water.quality_system['wastewater_primary_treatment']['energy_kwh_per_m3']
        ww_primary_recovery = self.water.quality_system['wastewater_primary_treatment']['recovery_rate']

        # Sludge production: ~75 g/m³ of wastewater treated
        sludge_production_kg_per_m3 = 0.075

        self.network.add(
            "Link",
            "Wastewater_Primary_Treatment",
            bus0="wastewater_municipal",  # Input wastewater (reference)
            bus1="electricity",  # Electricity consumed
            bus2="water_agricultural",  # Output water
            bus3="sludge",  # Output sludge
            p_nom=max_urban * wastewater_factor * water_energy_equiv,  # Max flow kW-equiv
            efficiency=ww_primary_energy / water_energy_equiv,  # 0.25/1.0 = 0.25
            efficiency2=ww_primary_recovery,  # 0.85 output per input
            efficiency3=sludge_production_kg_per_m3,  # Sludge production
            marginal_cost=0,
            capital_cost=100000
        )

        # 6. Wastewater Secondary Treatment (wastewater → potable reuse + sludge)
        # Same fix: wastewater as reference
        ww_secondary_energy = self.water.quality_system['wastewater_secondary_treatment']['energy_kwh_per_m3']
        ww_secondary_recovery = self.water.quality_system['wastewater_secondary_treatment']['recovery_rate']

        self.network.add(
            "Link",
            "Wastewater_Secondary_Treatment",
            bus0="wastewater_municipal",  # Input wastewater (reference)
            bus1="electricity",  # Electricity consumed
            bus2="water_potable",  # Output water
            bus3="sludge",  # Output sludge
            p_nom=max_urban * wastewater_factor * water_energy_equiv,  # Max flow kW-equiv
            efficiency=ww_secondary_energy / water_energy_equiv,  # 0.60/1.0 = 0.60
            efficiency2=ww_secondary_recovery,  # 0.75 output per input
            efficiency3=sludge_production_kg_per_m3 * 1.2,  # More sludge from secondary (20% more)
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

        # Add grid connection - natural gas to electricity (power network)
        # This represents the national grid's gas-fired power plants
        # Important: Iran has natural gas imbalance, so grid electricity depends on gas availability
        self.network.add(
            "Link",
            "Power_Network_NG_to_Elec",
            bus0="natural_gas",  # Input: natural gas
            bus1="electricity",  # Output: electricity
            p_nom=5000,  # 5 MW capacity
            efficiency=0.45,  # 45% gas-to-electricity efficiency (typical for CCGT)
            marginal_cost=80,  # Grid markup ($/MWh-electricity)
            capital_cost=0,  # Grid already exists
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

    def _add_thermal_carbon_systems(self):
        """Add all thermal and carbon systems: biomass, CHP, boiler, sludge, CCU, market"""

        print(f"\n🔥 Adding thermal and carbon systems...")

        # ====================================================================================
        # 1. BIOMASS SOURCE
        # ====================================================================================
        print(f"\n   1. Biomass source...")

        if 'biomass' in self.data:
            biomass_df = self.data['biomass']
            biomass_available = biomass_df['biomass_available_kg_h'].values[:len(self.network.snapshots)]

            # Biomass is available as a generator (source)
            # Convert kg/h to kW-equivalent for PyPSA (using energy content)
            energy_per_kg = 4.2  # kWh/kg
            biomass_power = biomass_available * energy_per_kg  # kW-equivalent

            # Add biomass as a limited generator
            self.network.add(
                "Generator",
                "Biomass_Source",
                bus="biomass",
                p_nom=biomass_power.max(),  # Peak availability
                p_max_pu=biomass_power / biomass_power.max() if biomass_power.max() > 0 else np.zeros_like(biomass_power),
                marginal_cost=5,  # Collection cost ($/MWh equivalent)
                capital_cost=0,
                carrier='biomass'
            )

            print(f"      Biomass availability: {biomass_available.sum():,.0f} kg (total)")
            print(f"      Energy content: {biomass_power.sum():,.0f} kWh-thermal (total)")
        else:
            print(f"      WARNING: No biomass data available!")

        # ====================================================================================
        # 2. NATURAL GAS SOURCE
        # ====================================================================================
        print(f"\n   2. Natural gas source...")

        # Natural gas is unlimited but expensive
        self.network.add(
            "Generator",
            "Natural_Gas_Source",
            bus="natural_gas",
            p_nom=10000,  # 10 MW thermal equivalent
            marginal_cost=40,  # $/MWh-thermal (gas price)
            capital_cost=0,
            carrier='natural_gas'
        )

        print(f"      Natural gas: Unlimited, $0.04/kWh-thermal")

        # ====================================================================================
        # 3. HEAT DEMAND
        # ====================================================================================
        print(f"\n   3. Heat demand...")

        if 'heat_demand' in self.data:
            heat_df = self.data['heat_demand']
            heat_demand_kwh = heat_df['urban_kwh_thermal'].values[:len(self.network.snapshots)]

            self.network.add(
                "Load",
                "Urban_Heat",
                bus="heat",
                p_set=heat_demand_kwh
            )

            print(f"      Urban heat demand: {heat_demand_kwh.mean():.1f} kWh/h (avg), {heat_demand_kwh.sum():,.0f} kWh (total)")
        else:
            print(f"      WARNING: No heat demand data available!")

        # ====================================================================================
        # 4. CHP (Combined Heat & Power)
        # ====================================================================================
        print(f"\n   4. CHP (Combined Heat & Power)...")

        chp_specs = self.chp.get_specs()

        # CHP from natural gas
        self.network.add(
            "Link",
            "CHP_NaturalGas",
            bus0="natural_gas",  # Input: natural gas
            bus1="electricity",  # Output 1: electricity
            bus2="heat",  # Output 2: heat
            bus3="co2_emissions",  # Output 3: CO2
            p_nom=1000,  # 1 MW thermal input capacity
            efficiency=chp_specs['electrical_efficiency'],  # 35% electrical
            efficiency2=chp_specs['thermal_efficiency'],  # 45% thermal
            efficiency3=chp_specs['emissions_natural_gas'],  # CO2 emissions
            marginal_cost=20,  # O&M cost
            capital_cost=chp_specs['capex'] * chp_specs['electrical_efficiency'] * 1000  # Based on electrical output
        )

        # CHP from biogas
        self.network.add(
            "Link",
            "CHP_Biogas",
            bus0="biogas",  # Input: biogas
            bus1="electricity",  # Output 1: electricity
            bus2="heat",  # Output 2: heat
            p_nom=500,  # 500 kW thermal input capacity
            efficiency=chp_specs['electrical_efficiency'],  # 35% electrical
            efficiency2=chp_specs['thermal_efficiency'],  # 45% thermal
            marginal_cost=10,  # Lower O&M for biogas
            capital_cost=chp_specs['capex'] * chp_specs['electrical_efficiency'] * 500
        )

        print(f"      CHP (natural gas): 1 MW thermal input, {chp_specs['electrical_efficiency']*100}% elec, {chp_specs['thermal_efficiency']*100}% heat")
        print(f"      CHP (biogas): 500 kW thermal input, {chp_specs['electrical_efficiency']*100}% elec, {chp_specs['thermal_efficiency']*100}% heat")

        # ====================================================================================
        # 5. GAS BOILER
        # ====================================================================================
        print(f"\n   5. Gas boiler...")

        boiler_specs = self.boiler.get_specs()

        # Boiler from natural gas
        self.network.add(
            "Link",
            "Boiler_NaturalGas",
            bus0="natural_gas",  # Input: natural gas
            bus1="heat",  # Output 1: heat
            bus2="co2_emissions",  # Output 2: CO2
            p_nom=2000,  # 2 MW thermal input capacity
            efficiency=boiler_specs['thermal_efficiency'],  # 85% thermal
            efficiency2=boiler_specs['emissions_natural_gas'],  # CO2 emissions
            marginal_cost=5,  # O&M cost
            capital_cost=boiler_specs['capex'] * boiler_specs['thermal_efficiency'] * 2000
        )

        # Boiler from biogas
        self.network.add(
            "Link",
            "Boiler_Biogas",
            bus0="biogas",  # Input: biogas
            bus1="heat",  # Output: heat
            p_nom=1000,  # 1 MW thermal input capacity
            efficiency=boiler_specs['thermal_efficiency'],  # 85% thermal
            marginal_cost=3,  # Lower O&M for biogas
            capital_cost=boiler_specs['capex'] * boiler_specs['thermal_efficiency'] * 1000
        )

        print(f"      Boiler (natural gas): 2 MW thermal input, {boiler_specs['thermal_efficiency']*100}% efficiency")
        print(f"      Boiler (biogas): 1 MW thermal input, {boiler_specs['thermal_efficiency']*100}% efficiency")

        # ====================================================================================
        # 6. SLUDGE MANAGEMENT SYSTEM
        # ====================================================================================
        print(f"\n   6. Sludge management system...")

        # 6a. Sludge production from wastewater treatment
        # Assume sludge is produced from wastewater (1 kg sludge per 13 m³ wastewater, roughly)
        # We'll model this as a byproduct of wastewater treatment

        # Add sludge accumulation store
        self.network.add(
            "Store",
            "Sludge_Accumulation",
            bus="sludge",
            e_nom=10000,  # Large capacity (kg)
            e_cyclic=False,
            e_initial=0
        )

        # 6b. Composting: sludge + biomass → compost
        compost_specs = self.sludge_system.get_composting_specs()

        self.network.add(
            "Link",
            "Composting",
            bus0="sludge",  # Input 1: sludge (70%)
            bus1="biomass",  # Input 2: biomass (30%)
            bus2="compost",  # Output: compost
            p_nom=100,  # 100 kg/h processing capacity
            efficiency=compost_specs['sludge_input_ratio'] / compost_specs['compost_output_ratio'],  # Sludge to compost
            efficiency2=compost_specs['biomass_input_ratio'] / compost_specs['compost_output_ratio'],  # Biomass to compost
            marginal_cost=10,  # Processing cost
            capital_cost=compost_specs['capex']
        )

        # 6c. Anaerobic digester: sludge + biomass + heat + electricity → biogas + digestate
        digester_specs = self.sludge_system.get_digester_specs()

        self.network.add(
            "Link",
            "Anaerobic_Digester",
            bus0="sludge",  # Input 1: sludge
            bus1="biomass",  # Input 2: biomass
            bus2="electricity",  # Input 3: electricity (for mixing)
            bus3="heat",  # Input 4: heat (for temperature)
            bus4="biogas",  # Output 1: biogas
            bus5="digestate",  # Output 2: digestate
            p_nom=200,  # 200 kg/h organic matter input capacity
            efficiency=digester_specs['sludge_input_ratio'] * digester_specs['biogas_yield_m3_per_kg'] * digester_specs['biogas_lhv'],  # Sludge to biogas energy
            efficiency2=digester_specs['biomass_input_ratio'] * digester_specs['biogas_yield_m3_per_kg'] * digester_specs['biogas_lhv'],  # Biomass to biogas energy
            efficiency3=digester_specs['electricity_consumption_kwh_per_m3'] / digester_specs['biogas_lhv'],  # Electricity consumption ratio
            efficiency4=digester_specs['heat_consumption_kwh_per_m3'] / digester_specs['biogas_lhv'],  # Heat consumption ratio
            efficiency5=digester_specs['digestate_output_ratio'],  # Digestate output
            marginal_cost=15,  # Processing cost
            capital_cost=digester_specs['capex']
        )

        print(f"      Composting: {compost_specs['compost_output_ratio']*100}% mass recovery")
        print(f"      Anaerobic digester: {digester_specs['biogas_yield_m3_per_kg']} m³ biogas/kg organic matter")

        # ====================================================================================
        # 7. CCU SYSTEM (Carbon Capture & Utilization)
        # ====================================================================================
        print(f"\n   7. CCU (Carbon Capture & Utilization)...")

        ccu_specs = self.ccu.get_specs()

        # CCU captures CO2 from emissions bus
        self.network.add(
            "Link",
            "CCU_Capture",
            bus0="co2_emissions",  # Input 1: CO2 from combustion
            bus1="electricity",  # Input 2: electricity for capture
            bus2="co2_captured",  # Output: captured CO2
            p_nom=100,  # 100 kg CO2/h capacity
            efficiency=ccu_specs['capture_efficiency'],  # 90% capture
            efficiency2=ccu_specs['electricity_kwh_per_kg_co2'],  # Electricity consumption
            marginal_cost=50,  # Processing cost ($/ton CO2 = $0.05/kg)
            capital_cost=ccu_specs['capex_per_ton_day'] * 100 / 1000 * 24  # Convert to hourly capacity
        )

        print(f"      CCU: {ccu_specs['capture_efficiency']*100}% capture efficiency")
        print(f"      Energy: {ccu_specs['electricity_kwh_per_kg_co2']} kWh/kg CO2")

        # ====================================================================================
        # 8. MARKET (Sales of Products)
        # ====================================================================================
        print(f"\n   8. Market (product sales)...")

        market_prices = self.market.get_prices()
        market_limits = self.market.get_limits()

        # Market for compost (negative cost = revenue)
        self.network.add(
            "Link",
            "Market_Compost",
            bus0="compost",
            bus1="market_compost",
            p_nom=market_limits['compost_tons_year'] / 8760,  # Convert annual to hourly
            efficiency=1.0,
            marginal_cost=-market_prices['compost_per_ton']  # Negative = revenue
        )

        # Market for digestate
        self.network.add(
            "Link",
            "Market_Digestate",
            bus0="digestate",
            bus1="market_digestate",
            p_nom=market_limits['digestate_tons_year'] / 8760,
            efficiency=1.0,
            marginal_cost=-market_prices['digestate_per_ton']  # Negative = revenue
        )

        # Market for CO2
        self.network.add(
            "Link",
            "Market_CO2",
            bus0="co2_captured",
            bus1="market_co2",
            p_nom=market_limits['co2_kg_year'] / 8760,  # kg/h
            efficiency=1.0,
            marginal_cost=-market_prices['co2_per_kg'] * 1000  # Negative = revenue ($/ton = $/1000 kg)
        )

        # Market for excess electricity (feed-in to grid)
        self.network.add(
            "Link",
            "Market_Electricity",
            bus0="electricity",
            bus1="market_electricity",
            p_nom=market_limits['electricity_kwh_year'] / 8760,  # kW
            efficiency=1.0,
            marginal_cost=-market_prices['electricity_per_kwh']  # Negative = revenue
        )

        # Market for excess heat (to industrial customers)
        self.network.add(
            "Link",
            "Market_Heat",
            bus0="heat",
            bus1="market_heat",
            p_nom=market_limits['heat_kwh_year'] / 8760,  # kW
            efficiency=1.0,
            marginal_cost=-market_prices['heat_per_kwh_thermal']  # Negative = revenue
        )

        # Add market sinks (unlimited absorption)
        for market_bus in ['market_compost', 'market_digestate', 'market_co2', 'market_electricity', 'market_heat']:
            self.network.add(
                "Store",
                f"{market_bus}_sink",
                bus=market_bus,
                e_nom=1e9,  # Unlimited
                e_cyclic=False,
                e_initial=0
            )

        # CO2 emissions sink (atmosphere)
        self.network.add(
            "Store",
            "CO2_Atmosphere",
            bus="co2_emissions",
            e_nom=1e9,  # Unlimited
            e_cyclic=False,
            e_initial=0,
            standing_losses=0  # CO2 stays in atmosphere
        )

        print(f"      Market prices:")
        print(f"         Compost: ${market_prices['compost_per_ton']}/ton")
        print(f"         Digestate: ${market_prices['digestate_per_ton']}/ton")
        print(f"         CO2: ${market_prices['co2_per_kg']}/kg")
        print(f"         Electricity: ${market_prices['electricity_per_kwh']}/kWh")
        print(f"         Heat: ${market_prices['heat_per_kwh_thermal']}/kWh-thermal")

        print(f"\n✅ Thermal and carbon systems added successfully!")

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
