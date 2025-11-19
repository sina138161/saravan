"""
Integrated Water-Energy System Model
Includes groundwater pumping, elevated storage, and potential energy storage
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List


class WaterSystemModel:
    """
    Water system with energy-water nexus integration

    Components:
    - Groundwater wells with submersible pumps
    - Elevated water tanks (potential energy storage)
    - Distribution system (agricultural drip + urban)
    """

    def __init__(self):
        """Initialize water system specifications"""
        self.well_specs = self._define_well_specifications()
        self.storage_specs = self._define_storage_specifications()
        self.distribution_specs = self._define_distribution()
        self.quality_system = self._define_water_quality_system()

    def _define_well_specifications(self) -> Dict:
        """
        Define groundwater well and pump specifications

        Based on: Saravan hydrogeology and typical submersible pumps
        """

        specs = {
            'well_depths': {
                'shallow': {
                    'depth': 50,  # meters
                    'static_water_level': 25,  # meters below surface
                    'sustainable_yield': 30,  # m³/hour
                    'drilling_cost': 15000,  # $ per well
                },
                'medium': {
                    'depth': 100,  # meters
                    'static_water_level': 50,  # meters
                    'sustainable_yield': 50,  # m³/hour
                    'drilling_cost': 25000,  # $ per well
                },
                'deep': {
                    'depth': 150,  # meters
                    'static_water_level': 75,  # meters
                    'sustainable_yield': 40,  # m³/hour (less due to deeper aquifer)
                    'drilling_cost': 40000,  # $ per well
                }
            },

            'submersible_pump': {
                'power_rating': 30,  # kW rated power
                'efficiency': 0.75,  # Pump efficiency
                'motor_efficiency': 0.90,  # Motor efficiency
                'head_loss_coefficient': 0.002,  # Friction loss per meter pipe
                'capex': 8000,  # $ per pump
                'opex_annual': 400,  # $ per year maintenance
                'lifetime': 15,  # years
                'variable_speed': True,  # VFD capability
            }
        }

        return specs

    def _define_storage_specifications(self) -> Dict:
        """
        Define elevated water tank specifications

        Key innovation: Using elevated water for potential energy storage
        """

        specs = {
            'tank_sizes': {
                'small': {
                    'capacity': 1000,  # m³
                    'diameter': 12,  # meters
                    'height': 9,  # meters
                    'material': 'steel',
                    'capex': 45000,  # $
                },
                'medium': {
                    'capacity': 2500,  # m³
                    'diameter': 18,  # meters
                    'height': 10,  # meters
                    'material': 'steel',
                    'capex': 95000,  # $
                },
                'large': {
                    'capacity': 5000,  # m³
                    'diameter': 25,  # meters
                    'height': 10,  # meters
                    'material': 'concrete',
                    'capex': 165000,  # $
                }
            },

            'tower_heights': {
                'low': {
                    'elevation': 15,  # meters
                    'pressure_at_base': 1.5,  # bar
                    'construction_cost_per_m3': 15,  # $ per m³ capacity
                },
                'medium': {
                    'elevation': 20,  # meters
                    'pressure_at_base': 2.0,  # bar
                    'construction_cost_per_m3': 20,  # $ per m³
                },
                'high': {
                    'elevation': 25,  # meters
                    'pressure_at_base': 2.5,  # bar
                    'construction_cost_per_m3': 25,  # $ per m³
                },
                'very_high': {
                    'elevation': 30,  # meters
                    'pressure_at_base': 3.0,  # bar
                    'construction_cost_per_m3': 32,  # $ per m³
                }
            },

        }

        return specs

    def _define_distribution(self) -> Dict:
        """Define water distribution system"""

        specs = {
            'agricultural': {
                'method': 'drip_irrigation',
                'pressure_requirement': 2.0,  # bar
                'efficiency': 0.90,  # 90% irrigation efficiency
                'peak_factor': 2.5,  # Seasonal variation
                'demand_profile': 'high_summer_low_winter',
                'water_quality_required': 'agricultural',  # Lower quality acceptable
                'wastewater_generation_factor': 0.10  # 10% becomes runoff/wastewater
            },

            'urban': {
                'method': 'pressurized_network',
                'pressure_requirement': 3.0,  # bar
                'efficiency': 0.85,  # 15% losses
                'peak_factor': 1.5,  # Daily variation
                'demand_profile': 'constant_with_peaks',
                'water_quality_required': 'potable',  # High quality required
                'wastewater_generation_factor': 0.80  # 80% becomes municipal wastewater
            }
            # NOTE: No industrial sector - Saravan has no industrial water demand
        }

        return specs

    def _define_water_quality_system(self) -> Dict:
        """
        Define water quality treatment system

        Water quality levels:
        - Raw groundwater: From well
        - Agricultural quality: Primary treatment
        - Potable quality: Secondary treatment

        Wastewater recycling:
        - Primary treated wastewater → Agricultural use
        - Secondary treated wastewater → Urban reuse
        """

        quality_system = {
            'groundwater_well': {
                # Extraction limits
                'extraction_limit_m3_per_hour': 200,  # Maximum sustainable extraction (peak capacity)
                'extraction_limit_annual_m3': 640000,  # Annual safe yield (80% of recharge)

                # Aquifer characteristics (unified - this is the only water source)
                'annual_recharge': 800000,  # m³/year (Saravan estimate)
                'safe_yield_factor': 0.80,  # Use 80% of recharge = 640,000 m³/year
                'storage_coefficient': 0.15,  # Storativity
                'transmissivity': 150,  # m²/day
                'specific_drawdown': 0.001,  # m per m³/day

                # Water quality
                'water_quality_level': 'raw',
                'tds_mg_l': 800,  # Total dissolved solids
                'treatment_required': True
            },

            'primary_treatment': {
                'purpose': 'Groundwater → Agricultural quality',
                'process': 'Filtration + Chlorination',
                'removal_efficiency': 0.85,  # 85% contaminant removal
                'energy_kwh_per_m3': 0.15,  # Energy for primary treatment
                'capex_per_m3_capacity': 120,  # $ per m³/day capacity
                'opex_per_m3': 0.08,  # $ per m³
                'output_quality': 'agricultural'
            },

            'secondary_treatment': {
                'purpose': 'Primary treated → Potable quality',
                'process': 'Advanced filtration + UV + RO (partial)',
                'removal_efficiency': 0.95,  # 95% contaminant removal
                'energy_kwh_per_m3': 0.50,  # Higher energy for advanced treatment
                'capex_per_m3_capacity': 350,  # $ per m³/day capacity
                'opex_per_m3': 0.22,  # $ per m³
                'output_quality': 'potable'
            },

            'wastewater_primary_treatment': {
                'purpose': 'Municipal wastewater → Agricultural reuse',
                'process': 'Screening + Sedimentation + Disinfection',
                'removal_efficiency': 0.70,  # 70% removal
                'energy_kwh_per_m3': 0.25,  # Energy for wastewater treatment
                'capex_per_m3_capacity': 200,  # $ per m³/day capacity
                'opex_per_m3': 0.12,  # $ per m³
                'output_quality': 'agricultural',
                'recovery_rate': 0.85  # 85% of wastewater recovered
            },

            'wastewater_secondary_treatment': {
                'purpose': 'Primary treated wastewater → Urban reuse',
                'process': 'Biological treatment + Membrane filtration',
                'removal_efficiency': 0.90,  # 90% removal
                'energy_kwh_per_m3': 0.60,  # High energy for advanced wastewater treatment
                'capex_per_m3_capacity': 450,  # $ per m³/day capacity
                'opex_per_m3': 0.30,  # $ per m³
                'output_quality': 'potable',
                'recovery_rate': 0.75  # 75% of primary treated wastewater recovered
            }
        }

        return quality_system

    def calculate_treatment_energy(self, flow_rate_m3: float, treatment_type: str) -> float:
        """
        Calculate energy required for water treatment

        Args:
            flow_rate_m3: Water flow rate (m³)
            treatment_type: Type of treatment

        Returns:
            Energy required (kWh)
        """

        if treatment_type not in self.quality_system:
            return 0

        energy_per_m3 = self.quality_system[treatment_type].get('energy_kwh_per_m3', 0)
        return flow_rate_m3 * energy_per_m3

    def calculate_pumping_energy(self, flow_rate: float, well_depth: str,
                                  tank_elevation: float = 0) -> float:
        """
        Calculate energy required to pump water

        E = (ρ * g * h * Q) / η

        Args:
            flow_rate: Water flow rate (m³/h)
            well_depth: 'shallow', 'medium', or 'deep'
            tank_elevation: Additional elevation to pump (meters)

        Returns:
            Power required (kW)
        """

        # Water properties
        rho = 1000  # kg/m³
        g = 9.81  # m/s²

        # Get well specs
        well = self.well_specs['well_depths'][well_depth]
        pump = self.well_specs['submersible_pump']

        # Total head
        static_head = well['static_water_level']  # meters
        elevation_head = tank_elevation  # meters
        total_head = static_head + elevation_head

        # Friction losses (simplified)
        pipe_length = well['depth'] + tank_elevation
        friction_loss = pump['head_loss_coefficient'] * pipe_length  # meters
        total_head += friction_loss

        # Flow rate in m³/s
        Q_m3_per_s = flow_rate / 3600  # Convert m³/h to m³/s

        # Hydraulic power
        P_hydraulic = (rho * g * total_head * Q_m3_per_s) / 1000  # kW

        # Account for pump and motor efficiency
        total_efficiency = pump['efficiency'] * pump['motor_efficiency']
        P_electrical = P_hydraulic / total_efficiency

        return P_electrical

    def calculate_potential_energy_storage(self, tank_capacity: str,
                                           elevation: str,
                                           fill_level: float = 1.0) -> float:
        """
        Calculate potential energy stored in elevated water tank

        E = m * g * h = ρ * V * g * h

        Args:
            tank_capacity: 'small', 'medium', or 'large'
            elevation: 'low', 'medium', 'high', or 'very_high'
            fill_level: Fraction full (0-1)

        Returns:
            Energy stored (kWh)
        """

        # Get tank and tower specs
        tank = self.storage_specs['tank_sizes'][tank_capacity]
        tower = self.storage_specs['tower_heights'][elevation]

        # Volume of water
        V = tank['capacity'] * fill_level  # m³

        # Mass of water
        m = V * 1000  # kg

        # Potential energy
        g = 9.81  # m/s²
        h = tower['elevation']  # meters

        E_joules = m * g * h  # Joules
        E_kwh = E_joules / (3.6e6)  # Convert to kWh

        return E_kwh

    # NOTE: Energy recovery from discharge not implemented - no micro-hydro turbine in system design
    # def calculate_energy_recovery_from_discharge(...)
    # This feature was removed as it's not part of the requested system

    def calculate_groundwater_sustainability(self, annual_pumping: float,
                                             n_wells: int = 1) -> Dict:
        """
        Check groundwater sustainability

        Args:
            annual_pumping: Total annual pumping (m³/year)
            n_wells: Number of wells

        Returns:
            Sustainability metrics
        """

        aquifer = self.well_specs['aquifer']

        # Safe yield
        safe_yield = aquifer['annual_recharge'] * aquifer['safe_yield_factor']

        # Sustainability ratio
        sustainability_ratio = annual_pumping / safe_yield

        # Drawdown estimation (simplified)
        daily_pumping = annual_pumping / 365  # m³/day
        drawdown_per_well = daily_pumping * aquifer['specific_drawdown'] / n_wells

        # Annual cumulative drawdown
        annual_drawdown = drawdown_per_well * 365

        return {
            'annual_recharge_m3': aquifer['annual_recharge'],
            'safe_yield_m3': safe_yield,
            'annual_pumping_m3': annual_pumping,
            'sustainability_ratio': sustainability_ratio,
            'is_sustainable': sustainability_ratio <= 1.0,
            'drawdown_per_well_m': drawdown_per_well,
            'annual_drawdown_m': annual_drawdown,
            'recommendation': self._sustainability_recommendation(sustainability_ratio)
        }

    def _sustainability_recommendation(self, ratio: float) -> str:
        """Generate sustainability recommendation"""

        if ratio <= 0.8:
            return "Sustainable - Well within safe limits"
        elif ratio <= 1.0:
            return "Marginally sustainable - Monitor closely"
        elif ratio <= 1.2:
            return "Unsustainable - Reduce pumping by 15-20%"
        else:
            return "Severely unsustainable - Risk of aquifer depletion"

    def design_water_energy_system(self, annual_water_demand: float,
                                   peak_demand: float,
                                   available_land: float = None) -> Dict:
        """
        Design integrated water-energy system

        Args:
            annual_water_demand: Annual water needed (m³/year)
            peak_demand: Peak hourly demand (m³/h)
            available_land: Available land for tanks (optional)

        Returns:
            Optimal system configuration
        """

        # Determine number and type of wells
        daily_avg = annual_water_demand / 365

        # Start with medium wells
        wells_needed = np.ceil(peak_demand / 50)  # 50 m³/h per medium well

        # Check sustainability
        sustainability = self.calculate_groundwater_sustainability(
            annual_water_demand,
            int(wells_needed)
        )

        # Size storage tank (typically 1-2 days of average demand)
        daily_storage_volume = daily_avg * 1.5  # 1.5 days

        # Select tank size
        if daily_storage_volume <= 1000:
            tank_size = 'small'
        elif daily_storage_volume <= 2500:
            tank_size = 'medium'
        else:
            tank_size = 'large'

        # Select elevation (higher is better for energy storage)
        elevation = 'high'  # 25 meters

        # Calculate energy storage capacity
        energy_storage_kwh = self.calculate_potential_energy_storage(
            tank_size,
            elevation,
            fill_level=1.0
        )

        # Calculate pumping energy
        avg_pumping_rate = annual_water_demand / 8760  # m³/h
        pumping_power = self.calculate_pumping_energy(
            avg_pumping_rate,
            'medium',
            25  # Tank elevation
        )

        return {
            'wells': {
                'number': int(wells_needed),
                'type': 'medium',
                'total_capacity_m3_h': wells_needed * 50,
                'total_drilling_cost': wells_needed * 25000,
                'total_pump_cost': wells_needed * 8000
            },
            'storage': {
                'tank_size': tank_size,
                'elevation': elevation,
                'capacity_m3': self.storage_specs['tank_sizes'][tank_size]['capacity'],
                'energy_storage_kwh': energy_storage_kwh,
                'tank_cost': self.storage_specs['tank_sizes'][tank_size]['capex'],
                'tower_cost': self.storage_specs['tank_sizes'][tank_size]['capacity'] *
                             self.storage_specs['tower_heights'][elevation]['construction_cost_per_m3']
            },
            'energy': {
                'avg_pumping_power_kw': pumping_power,
                'annual_pumping_energy_kwh': pumping_power * 8760,
                'potential_energy_storage_kwh': energy_storage_kwh,
                'energy_recovery_possible': False  # No micro-hydro turbine in system
            },
            'sustainability': sustainability,
            'total_capex': (
                wells_needed * (25000 + 8000) +
                self.storage_specs['tank_sizes'][tank_size]['capex'] +
                self.storage_specs['tank_sizes'][tank_size]['capacity'] *
                self.storage_specs['tower_heights'][elevation]['construction_cost_per_m3']
            )
        }

    def simulate_tank_operation(self, inflow_series: np.ndarray,
                                outflow_series: np.ndarray,
                                tank_capacity: float,
                                initial_level: float = 0.5) -> Dict:
        """
        Simulate water tank operation

        Args:
            inflow_series: Hourly inflow (m³/h) - from pumping
            outflow_series: Hourly outflow (m³/h) - to demand
            tank_capacity: Tank capacity (m³)
            initial_level: Initial fill level (fraction)

        Returns:
            Operation statistics
        """

        hours = len(inflow_series)
        tank_level = np.zeros(hours + 1)
        tank_level[0] = tank_capacity * initial_level

        overflow = 0
        deficit = 0

        for t in range(hours):
            # Water balance
            tank_level[t + 1] = tank_level[t] + inflow_series[t] - outflow_series[t]

            # Check constraints
            if tank_level[t + 1] > tank_capacity:
                overflow += (tank_level[t + 1] - tank_capacity)
                tank_level[t + 1] = tank_capacity

            if tank_level[t + 1] < 0:
                deficit += abs(tank_level[t + 1])
                tank_level[t + 1] = 0

        return {
            'final_level_m3': tank_level[-1],
            'final_level_fraction': tank_level[-1] / tank_capacity,
            'min_level_m3': np.min(tank_level),
            'max_level_m3': np.max(tank_level),
            'avg_level_m3': np.mean(tank_level),
            'total_overflow_m3': overflow,
            'total_deficit_m3': deficit,
            'hours_empty': np.sum(tank_level == 0),
            'hours_full': np.sum(tank_level == tank_capacity),
            'utilization_factor': np.mean(tank_level) / tank_capacity
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize water system
    water_system = WaterSystemModel()

    print("=" * 80)
    print("WATER SYSTEM MODEL - SARAVAN WIND-WATER NEXUS")
    print("=" * 80)

    # Test pumping energy calculation
    print("\n1. PUMPING ENERGY REQUIREMENTS")
    print("-" * 80)

    test_flows = [10, 30, 50]  # m³/h
    for flow in test_flows:
        power_shallow = water_system.calculate_pumping_energy(flow, 'shallow', 25)
        power_medium = water_system.calculate_pumping_energy(flow, 'medium', 25)
        power_deep = water_system.calculate_pumping_energy(flow, 'deep', 25)

        print(f"\nFlow rate: {flow} m³/h (to 25m elevated tank)")
        print(f"  Shallow well (50m):  {power_shallow:5.1f} kW")
        print(f"  Medium well (100m):  {power_medium:5.1f} kW")
        print(f"  Deep well (150m):    {power_deep:5.1f} kW")

    # Test potential energy storage
    print("\n\n2. POTENTIAL ENERGY STORAGE IN ELEVATED TANKS")
    print("-" * 80)

    for tank_size in ['small', 'medium', 'large']:
        for elevation in ['low', 'medium', 'high', 'very_high']:
            energy = water_system.calculate_potential_energy_storage(
                tank_size, elevation, fill_level=1.0
            )
            capacity = water_system.storage_specs['tank_sizes'][tank_size]['capacity']
            elev_m = water_system.storage_specs['tower_heights'][elevation]['elevation']

            print(f"{tank_size.capitalize():6s} ({capacity:4.0f} m³) @ {elev_m:2.0f}m: {energy:6.1f} kWh")

    # Design example system
    print("\n\n3. INTEGRATED WATER-ENERGY SYSTEM DESIGN")
    print("-" * 80)

    annual_demand = 500000  # m³/year
    peak_demand = 75  # m³/h

    design = water_system.design_water_energy_system(annual_demand, peak_demand)

    print(f"\nAnnual Water Demand: {annual_demand:,} m³/year")
    print(f"Peak Hourly Demand: {peak_demand} m³/h")

    print(f"\nWELLS:")
    print(f"  Number of wells: {design['wells']['number']}")
    print(f"  Total capacity: {design['wells']['total_capacity_m3_h']} m³/h")
    print(f"  Cost: ${design['wells']['total_drilling_cost'] + design['wells']['total_pump_cost']:,}")

    print(f"\nSTORAGE:")
    print(f"  Tank size: {design['storage']['tank_size']}")
    print(f"  Capacity: {design['storage']['capacity_m3']} m³")
    print(f"  Elevation: {design['storage']['elevation']}")
    print(f"  Energy storage: {design['storage']['energy_storage_kwh']:.1f} kWh")
    print(f"  Cost: ${design['storage']['tank_cost'] + design['storage']['tower_cost']:,}")

    print(f"\nENERGY:")
    print(f"  Avg pumping power: {design['energy']['avg_pumping_power_kw']:.1f} kW")
    print(f"  Annual energy: {design['energy']['annual_pumping_energy_kwh']:,.0f} kWh")

    print(f"\nSUSTAINABILITY:")
    sust = design['sustainability']
    print(f"  Annual recharge: {sust['annual_recharge_m3']:,} m³")
    print(f"  Safe yield: {sust['safe_yield_m3']:,} m³")
    print(f"  Sustainability ratio: {sust['sustainability_ratio']:.2f}")
    print(f"  Status: {sust['recommendation']}")

    print(f"\nTOTAL CAPEX: ${design['total_capex']:,}")
