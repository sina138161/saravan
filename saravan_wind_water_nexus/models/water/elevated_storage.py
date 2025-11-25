"""
Elevated Water Storage Tank Model
Water storage with potential energy storage capability
"""

import numpy as np
from typing import Dict
from ..base import TechnologyBase


class ElevatedStorage(TechnologyBase):
    """
    Elevated Water Storage Tank

    Features:
    - Water storage for demand buffering
    - Potential energy storage
    - Gravity-fed distribution
    """

    def __init__(self, tank_size: str = 'medium', elevation: str = 'high'):
        """
        Initialize elevated storage

        Args:
            tank_size: 'small', 'medium', or 'large'
            elevation: 'low', 'medium', 'high', or 'very_high'
        """
        self.tank_size = tank_size
        self.elevation = elevation
        super().__init__()

    def _define_specs(self) -> Dict:
        """
        Define elevated storage specifications
        """
        tank_sizes = {
            'small': {
                'capacity': 1000,  # m³
                'diameter': 12,  # meters
                'height': 9,  # meters
                'material': 'steel',
                'tank_capex': 45000,  # $
            },
            'medium': {
                'capacity': 2500,  # m³
                'diameter': 18,  # meters
                'height': 10,  # meters
                'material': 'steel',
                'tank_capex': 95000,  # $
            },
            'large': {
                'capacity': 5000,  # m³
                'diameter': 25,  # meters
                'height': 10,  # meters
                'material': 'concrete',
                'tank_capex': 165000,  # $
            }
        }

        tower_heights = {
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
        }

        tank_spec = tank_sizes[self.tank_size]
        tower_spec = tower_heights[self.elevation]

        # Total CAPEX
        total_capex = tank_spec['tank_capex'] + (tank_spec['capacity'] * tower_spec['construction_cost_per_m3'])

        # OPEX (maintenance)
        annual_opex = total_capex * 0.02  # 2% of CAPEX per year

        return {
            'name': f'{self.tank_size.capitalize()}_Tank_{self.elevation.capitalize()}_Elevation',
            'tank_size': self.tank_size,
            'elevation': self.elevation,
            'tank_specs': tank_spec,
            'tower_specs': tower_spec,

            # Exact formula parameters
            'V_awt_max': tank_spec['capacity'],  # Maximum capacity (m³)
            'V_awt_min': tank_spec['capacity'] * 0.10,  # Minimum capacity (10% of max)
            'theta_awt': 0.0001,  # Evaporation and seepage rate per hour (0.01%/h)

            # Economics
            'capex': total_capex,
            'opex': annual_opex,
            'lifetime': 30  # years
        }

    def calculate_tank_state_exact(self, v_awt_prev: float,
                                    v_awt_in: float,
                                    v_awt_out: float,
                                    delta_t: float = 1.0,
                                    u: int = None) -> Dict:
        """
        Calculate tank state using exact formula

        Formula:
            v_awt(t) = (1 - ϑ_awt × Δt) × v_awt(t-1) + v_awt,in(t) - v_awt,out(t)

        Constraints:
            V_awt,min ≤ v_awt(t) ≤ V_awt,max

        Binary Variable (if used):
            u(t) ∈ {0,1}
            v_awt,in(t) ≤ u(t) × V_awt,max
            v_awt,out(t) ≤ (1-u(t)) × V_awt,max

        Args:
            v_awt_prev: Previous water volume v_awt(t-1) (m³)
            v_awt_in: Water inflow v_awt,in(t) (m³)
            v_awt_out: Water outflow v_awt,out(t) (m³)
            delta_t: Time step Δt (hours, default 1.0)
            u: Binary variable for charging/discharging mode (0 or 1, optional)

        Returns:
            Dictionary with tank state and constraint checks
        """
        # Get specs
        theta_awt = self.specs['theta_awt']
        V_awt_max = self.specs['V_awt_max']
        V_awt_min = self.specs['V_awt_min']

        # Formula: v_awt(t) = (1 - ϑ_awt × Δt) × v_awt(t-1) + v_awt,in(t) - v_awt,out(t)
        v_awt = (1 - theta_awt * delta_t) * v_awt_prev + v_awt_in - v_awt_out

        # Constraint 1: Capacity limits
        # V_awt,min ≤ v_awt(t) ≤ V_awt,max
        capacity_constraint_met = V_awt_min <= v_awt <= V_awt_max
        violations = []

        if v_awt < V_awt_min:
            violations.append(f"Tank volume {v_awt:.2f} m³ below minimum {V_awt_min:.2f} m³")
        elif v_awt > V_awt_max:
            violations.append(f"Tank volume {v_awt:.2f} m³ exceeds maximum {V_awt_max:.2f} m³")

        # Constraint 2: Binary variable (if provided)
        # u(t) ∈ {0,1}
        # v_awt,in(t) ≤ u(t) × V_awt,max
        # v_awt,out(t) ≤ (1-u(t)) × V_awt,max
        binary_constraint_met = True
        if u is not None:
            if u not in [0, 1]:
                binary_constraint_met = False
                violations.append(f"Binary variable u={u} must be 0 or 1")
            else:
                # Check inflow constraint
                if v_awt_in > u * V_awt_max:
                    binary_constraint_met = False
                    violations.append(f"Inflow {v_awt_in:.2f} m³ exceeds u×V_max = {u * V_awt_max:.2f} m³")

                # Check outflow constraint
                if v_awt_out > (1 - u) * V_awt_max:
                    binary_constraint_met = False
                    violations.append(f"Outflow {v_awt_out:.2f} m³ exceeds (1-u)×V_max = {(1-u) * V_awt_max:.2f} m³")

        # Calculate fill level
        fill_level = v_awt / V_awt_max if V_awt_max > 0 else 0

        # Water loss due to evaporation/seepage
        water_loss = theta_awt * delta_t * v_awt_prev

        return {
            # Inputs
            'v_awt_prev_m3': v_awt_prev,
            'v_awt_in_m3': v_awt_in,
            'v_awt_out_m3': v_awt_out,
            'delta_t_hours': delta_t,
            'u': u,

            # Output
            'v_awt_m3': v_awt,
            'fill_level': fill_level,
            'fill_level_pct': fill_level * 100,

            # Parameters
            'theta_awt': theta_awt,
            'V_awt_max': V_awt_max,
            'V_awt_min': V_awt_min,

            # Water balance
            'water_loss_m3': water_loss,
            'net_change_m3': v_awt - v_awt_prev,

            # Constraints
            'capacity_constraint_met': capacity_constraint_met,
            'binary_constraint_met': binary_constraint_met if u is not None else True,
            'all_constraints_met': capacity_constraint_met and (binary_constraint_met if u is not None else True),
            'violations': violations,

            # Formula used
            'formula': 'v_awt(t) = (1 - ϑ_awt × Δt) × v_awt(t-1) + v_awt,in(t) - v_awt,out(t)'
        }

    def calculate_potential_energy_storage(self, fill_level: float = 1.0) -> Dict:
        """
        Calculate potential energy stored in elevated water

        E = m * g * h = ρ * V * g * h

        Args:
            fill_level: Fraction full (0-1)

        Returns:
            Energy storage details
        """
        # Get tank and tower specs
        tank = self.specs['tank_specs']
        tower = self.specs['tower_specs']

        # Volume of water
        V = tank['capacity'] * fill_level  # m³

        # Mass of water
        m = V * 1000  # kg

        # Potential energy
        g = 9.81  # m/s²
        h = tower['elevation']  # meters

        E_joules = m * g * h  # Joules
        E_kwh = E_joules / (3.6e6)  # Convert to kWh

        # Specific energy (kWh per m³)
        specific_energy_kwh_per_m3 = E_kwh / V if V > 0 else 0

        return {
            'fill_level': fill_level,
            'water_volume_m3': V,
            'water_mass_kg': m,
            'elevation_m': h,
            'potential_energy_joules': E_joules,
            'potential_energy_kwh': E_kwh,
            'specific_energy_kwh_per_m3': specific_energy_kwh_per_m3,
            'tank_capacity_m3': tank['capacity']
        }

    def calculate_pressure_at_base(self) -> Dict:
        """
        Calculate water pressure at tank base

        P = ρ * g * h

        Returns:
            Pressure details
        """
        tower = self.specs['tower_specs']

        # Pressure from elevation
        rho = 1000  # kg/m³
        g = 9.81  # m/s²
        h = tower['elevation']  # meters

        # Pressure in Pascals
        pressure_pa = rho * g * h

        # Convert to bar
        pressure_bar = pressure_pa / 1e5

        return {
            'elevation_m': h,
            'pressure_pa': pressure_pa,
            'pressure_bar': pressure_bar,
            'pressure_psi': pressure_bar * 14.5038,
            'suitable_for_drip_irrigation': pressure_bar >= 2.0,
            'suitable_for_urban_supply': pressure_bar >= 3.0
        }

    def simulate_tank_operation(self, inflow_series: np.ndarray,
                                outflow_series: np.ndarray,
                                initial_level: float = 0.5) -> Dict:
        """
        Simulate water tank operation

        Args:
            inflow_series: Hourly inflow (m³/h) - from pumping
            outflow_series: Hourly outflow (m³/h) - to demand
            initial_level: Initial fill level (fraction)

        Returns:
            Operation statistics
        """
        tank_capacity = self.specs['tank_specs']['capacity']
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
            'tank_capacity_m3': tank_capacity,
            'initial_level_m3': tank_level[0],
            'final_level_m3': tank_level[-1],
            'final_level_fraction': tank_level[-1] / tank_capacity,
            'min_level_m3': np.min(tank_level),
            'max_level_m3': np.max(tank_level),
            'avg_level_m3': np.mean(tank_level),
            'total_overflow_m3': overflow,
            'total_deficit_m3': deficit,
            'hours_empty': np.sum(tank_level == 0),
            'hours_full': np.sum(tank_level == tank_capacity),
            'utilization_factor': np.mean(tank_level) / tank_capacity,
            'hours_simulated': hours
        }

    def calculate_storage_capacity_days(self, daily_demand_m3: float) -> Dict:
        """
        Calculate storage capacity in days of demand

        Args:
            daily_demand_m3: Daily water demand (m³/day)

        Returns:
            Storage capacity details
        """
        tank_capacity = self.specs['tank_specs']['capacity']

        # Days of storage
        days_of_storage = tank_capacity / daily_demand_m3 if daily_demand_m3 > 0 else 0

        # Is capacity adequate? (typically need 1-2 days)
        adequate_capacity = days_of_storage >= 1.0

        return {
            'tank_capacity_m3': tank_capacity,
            'daily_demand_m3': daily_demand_m3,
            'days_of_storage': days_of_storage,
            'adequate_capacity': adequate_capacity,
            'recommended_minimum_days': 1.0,
            'recommended_optimal_days': 1.5
        }

    def design_storage_system(self, peak_demand_m3_h: float,
                             average_demand_m3_h: float,
                             peak_factor: float = 2.0) -> Dict:
        """
        Design storage system for demand profile

        Args:
            peak_demand_m3_h: Peak hourly demand (m³/h)
            average_demand_m3_h: Average hourly demand (m³/h)
            peak_factor: Ratio of peak to average demand

        Returns:
            Design recommendations
        """
        # Daily demand
        daily_demand_m3 = average_demand_m3_h * 24

        # Storage capacity (current tank)
        tank_capacity = self.specs['tank_specs']['capacity']
        days_of_storage = tank_capacity / daily_demand_m3 if daily_demand_m3 > 0 else 0

        # Recommended storage (1.5 days)
        recommended_capacity_m3 = daily_demand_m3 * 1.5

        # Is current tank adequate?
        adequate = tank_capacity >= recommended_capacity_m3

        # Pressure check
        pressure = self.calculate_pressure_at_base()

        # Energy storage
        energy_storage = self.calculate_potential_energy_storage(fill_level=1.0)

        return {
            'peak_demand_m3_h': peak_demand_m3_h,
            'average_demand_m3_h': average_demand_m3_h,
            'daily_demand_m3': daily_demand_m3,
            'current_capacity_m3': tank_capacity,
            'days_of_storage': days_of_storage,
            'recommended_capacity_m3': recommended_capacity_m3,
            'adequate_capacity': adequate,
            'pressure_bar': pressure['pressure_bar'],
            'energy_storage_kwh': energy_storage['potential_energy_kwh'],
            'total_capex': self.specs['capex'],
            'tank_size': self.tank_size,
            'elevation': self.elevation
        }

    def calculate_pumping_schedule_optimization(self, hourly_demand: np.ndarray,
                                               electricity_prices: np.ndarray) -> Dict:
        """
        Optimize pumping schedule using tank as buffer

        Pump during low-price hours, use tank during high-price hours

        Args:
            hourly_demand: 24-hour demand profile (m³/h)
            electricity_prices: 24-hour electricity price profile ($/kWh)

        Returns:
            Optimized pumping schedule
        """
        tank_capacity = self.specs['tank_specs']['capacity']

        # Total daily demand
        daily_demand = np.sum(hourly_demand)

        # Simple strategy: pump during lowest-price hours to meet daily demand
        # More sophisticated optimization would use LP/MIP

        # Find hours to pump (lowest price hours sufficient to meet daily demand)
        price_sorted_indices = np.argsort(electricity_prices)

        pumping_schedule = np.zeros(24)
        cumulative_pumped = 0
        hours_pumping = 0

        for hour_idx in price_sorted_indices:
            if cumulative_pumped < daily_demand:
                # Pump at maximum sustainable rate (assume 50 m³/h)
                pump_rate = min(50, daily_demand - cumulative_pumped)
                pumping_schedule[hour_idx] = pump_rate
                cumulative_pumped += pump_rate
                hours_pumping += 1

        # Calculate cost savings
        # Baseline: pump to meet demand each hour
        baseline_cost = np.sum(hourly_demand * electricity_prices * 1.0)  # Assume 1 kWh/m³

        # Optimized: pump during low-price hours
        optimized_cost = np.sum(pumping_schedule * electricity_prices * 1.0)

        cost_savings = baseline_cost - optimized_cost
        savings_pct = (cost_savings / baseline_cost * 100) if baseline_cost > 0 else 0

        return {
            'daily_demand_m3': daily_demand,
            'hours_pumping': hours_pumping,
            'baseline_cost': baseline_cost,
            'optimized_cost': optimized_cost,
            'cost_savings': cost_savings,
            'savings_pct': savings_pct,
            'pumping_schedule': pumping_schedule
        }
