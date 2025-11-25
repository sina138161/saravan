"""
Groundwater Well and Pumping System Model
Wells with submersible pumps for groundwater extraction
"""

from typing import Dict
from ..base import TechnologyBase


class GroundwaterWell(TechnologyBase):
    """
    Groundwater Well with Submersible Pump

    Components:
    - Well (shallow, medium, or deep)
    - Submersible pump with VFD
    - Pumping energy calculations
    - Aquifer sustainability monitoring
    """

    def __init__(self, well_depth: str = 'medium'):
        """
        Initialize groundwater well

        Args:
            well_depth: 'shallow', 'medium', or 'deep'
        """
        self.well_depth = well_depth
        super().__init__()

    def _define_specs(self) -> Dict:
        """
        Define groundwater well specifications

        Based on: Saravan hydrogeology and typical submersible pumps
        """
        well_depths = {
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
        }

        submersible_pump = {
            'power_rating': 30,  # kW rated power
            'efficiency': 0.75,  # Pump efficiency
            'motor_efficiency': 0.90,  # Motor efficiency
            'head_loss_coefficient': 0.002,  # Friction loss per meter pipe
            'capex': 8000,  # $ per pump
            'opex': 400,  # $/year maintenance
            'lifetime': 15,  # years
            'variable_speed': True,  # VFD capability
        }

        # Aquifer characteristics
        aquifer = {
            'annual_recharge': 800000,  # m³/year (Saravan estimate)
            'safe_yield_factor': 0.80,  # Use 80% of recharge
            'storage_coefficient': 0.15,  # Storativity
            'transmissivity': 150,  # m²/day
            'specific_drawdown': 0.001,  # m per m³/day
        }

        # Total CAPEX and OPEX
        well_spec = well_depths[self.well_depth]
        total_capex = well_spec['drilling_cost'] + submersible_pump['capex']
        total_opex = submersible_pump['opex']

        return {
            'name': f'{self.well_depth.capitalize()}_Groundwater_Well',
            'well_depth': self.well_depth,
            'well_specs': well_spec,
            'pump_specs': submersible_pump,
            'aquifer': aquifer,
            'capex': total_capex,
            'opex': total_opex,
            'lifetime': submersible_pump['lifetime']
        }

    def calculate_pumping_energy(self, flow_rate_m3_h: float,
                                 tank_elevation: float = 0) -> Dict:
        """
        Calculate energy required to pump water

        E = (ρ * g * h * Q) / η

        Args:
            flow_rate_m3_h: Water flow rate (m³/h)
            tank_elevation: Additional elevation to pump (meters)

        Returns:
            Power and energy details
        """
        # Water properties
        rho = 1000  # kg/m³
        g = 9.81  # m/s²

        # Get well and pump specs
        well = self.specs['well_specs']
        pump = self.specs['pump_specs']

        # Total head
        static_head = well['static_water_level']  # meters
        elevation_head = tank_elevation  # meters
        total_head = static_head + elevation_head

        # Friction losses (simplified)
        pipe_length = well['depth'] + tank_elevation
        friction_loss = pump['head_loss_coefficient'] * pipe_length  # meters
        total_head += friction_loss

        # Flow rate in m³/s
        Q_m3_per_s = flow_rate_m3_h / 3600  # Convert m³/h to m³/s

        # Hydraulic power
        P_hydraulic = (rho * g * total_head * Q_m3_per_s) / 1000  # kW

        # Account for pump and motor efficiency
        total_efficiency = pump['efficiency'] * pump['motor_efficiency']
        P_electrical = P_hydraulic / total_efficiency

        # Check against rated power
        overload = P_electrical > pump['power_rating']

        return {
            'flow_rate_m3_h': flow_rate_m3_h,
            'static_head_m': static_head,
            'elevation_head_m': elevation_head,
            'friction_loss_m': friction_loss,
            'total_head_m': total_head,
            'hydraulic_power_kw': P_hydraulic,
            'electrical_power_kw': P_electrical,
            'pump_efficiency': pump['efficiency'],
            'motor_efficiency': pump['motor_efficiency'],
            'total_efficiency': total_efficiency,
            'rated_power_kw': pump['power_rating'],
            'overload': overload,
            'capacity_utilization': P_electrical / pump['power_rating'] if not overload else 1.0
        }

    def calculate_annual_pumping_cost(self, annual_water_m3: float,
                                     tank_elevation: float = 0,
                                     electricity_price_per_kwh: float = 0.10) -> Dict:
        """
        Calculate annual cost of pumping

        Args:
            annual_water_m3: Annual water pumped (m³)
            tank_elevation: Elevation to pump (meters)
            electricity_price_per_kwh: Electricity price ($/kWh)

        Returns:
            Cost breakdown
        """
        # Average flow rate (assuming continuous operation)
        avg_flow_rate_m3_h = annual_water_m3 / 8760

        # Pumping energy
        pumping = self.calculate_pumping_energy(avg_flow_rate_m3_h, tank_elevation)

        # Annual energy
        annual_energy_kwh = pumping['electrical_power_kw'] * 8760

        # Energy cost
        energy_cost = annual_energy_kwh * electricity_price_per_kwh

        # OPEX (maintenance)
        maintenance_cost = self.specs['opex']

        # Total cost
        total_cost = energy_cost + maintenance_cost

        # Cost per m³
        cost_per_m3 = total_cost / annual_water_m3 if annual_water_m3 > 0 else 0

        return {
            'annual_water_m3': annual_water_m3,
            'annual_energy_kwh': annual_energy_kwh,
            'electricity_price': electricity_price_per_kwh,
            'energy_cost': energy_cost,
            'maintenance_cost': maintenance_cost,
            'total_annual_cost': total_cost,
            'cost_per_m3': cost_per_m3,
            'energy_per_m3_kwh': annual_energy_kwh / annual_water_m3 if annual_water_m3 > 0 else 0
        }

    def check_sustainability(self, annual_pumping_m3: float,
                            n_wells: int = 1) -> Dict:
        """
        Check groundwater sustainability

        Args:
            annual_pumping_m3: Total annual pumping (m³/year)
            n_wells: Number of wells

        Returns:
            Sustainability metrics
        """
        aquifer = self.specs['aquifer']

        # Safe yield
        safe_yield = aquifer['annual_recharge'] * aquifer['safe_yield_factor']

        # Sustainability ratio
        sustainability_ratio = annual_pumping_m3 / safe_yield

        # Drawdown estimation (simplified)
        daily_pumping = annual_pumping_m3 / 365  # m³/day
        drawdown_per_well = daily_pumping * aquifer['specific_drawdown'] / n_wells

        # Annual cumulative drawdown
        annual_drawdown = drawdown_per_well * 365

        # Recommendation
        if sustainability_ratio <= 0.8:
            recommendation = "Sustainable - Well within safe limits"
        elif sustainability_ratio <= 1.0:
            recommendation = "Marginally sustainable - Monitor closely"
        elif sustainability_ratio <= 1.2:
            recommendation = "Unsustainable - Reduce pumping by 15-20%"
        else:
            recommendation = "Severely unsustainable - Risk of aquifer depletion"

        return {
            'annual_recharge_m3': aquifer['annual_recharge'],
            'safe_yield_m3': safe_yield,
            'annual_pumping_m3': annual_pumping_m3,
            'sustainability_ratio': sustainability_ratio,
            'is_sustainable': sustainability_ratio <= 1.0,
            'drawdown_per_well_m': drawdown_per_well,
            'annual_drawdown_m': annual_drawdown,
            'recommendation': recommendation,
            'n_wells': n_wells
        }

    def design_well_system(self, peak_demand_m3_h: float,
                          annual_demand_m3: float) -> Dict:
        """
        Design well system for given demand

        Args:
            peak_demand_m3_h: Peak hourly demand (m³/h)
            annual_demand_m3: Annual water demand (m³/year)

        Returns:
            System design recommendations
        """
        # Get well capacity
        well_capacity = self.specs['well_specs']['sustainable_yield']

        # Number of wells needed for peak demand
        wells_for_peak = int(peak_demand_m3_h / well_capacity) + 1

        # Check sustainability
        sustainability = self.check_sustainability(annual_demand_m3, wells_for_peak)

        # If not sustainable, increase number of wells
        if not sustainability['is_sustainable']:
            # Recalculate with more wells to reduce individual well pumping
            wells_for_sustainability = int(
                annual_demand_m3 / (self.specs['aquifer']['annual_recharge'] * 0.8 / wells_for_peak)
            ) + 1
            recommended_wells = max(wells_for_peak, wells_for_sustainability)
        else:
            recommended_wells = wells_for_peak

        # Total capacity
        total_capacity = recommended_wells * well_capacity

        # Total cost
        total_capex = recommended_wells * self.specs['capex']
        total_annual_opex = recommended_wells * self.specs['opex']

        return {
            'peak_demand_m3_h': peak_demand_m3_h,
            'annual_demand_m3': annual_demand_m3,
            'well_capacity_m3_h': well_capacity,
            'wells_for_peak': wells_for_peak,
            'recommended_wells': recommended_wells,
            'total_capacity_m3_h': total_capacity,
            'capacity_utilization_peak': peak_demand_m3_h / total_capacity,
            'total_capex': total_capex,
            'total_annual_opex': total_annual_opex,
            'sustainability': sustainability
        }
