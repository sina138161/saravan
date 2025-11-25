"""
Gas Microturbine Model
Small-scale gas turbine for distributed power generation with heat recovery
"""

from typing import Dict
from ..base import TechnologyBase


class GasMicroturbine(TechnologyBase):
    """
    Gas Microturbine System

    Input:
    - Natural gas or biogas

    Outputs:
    - Electricity
    - High-temperature exhaust heat (for heat recovery)
    - CO2 emissions (for CCU capture)
    """

    def _define_specs(self) -> Dict:
        """
        Define gas microturbine specifications

        Based on: Commercial microturbine systems (e.g., Capstone, Ansaldo)
        """
        return {
            'name': 'Gas_Microturbine',
            'rated_capacity_kw': 200,       # 200 kW electrical
            'electrical_efficiency': 0.28,   # 28% electrical efficiency (lower than CHP)
            'exhaust_temperature': 270,      # °C (high temp for heat recovery)
            'exhaust_heat_kwh_per_kwh_elec': 2.0,  # Heat available per kWh electric
            'natural_gas_lhv': 10.0,         # kWh/m³ (Lower Heating Value)
            'biogas_lhv': 6.0,               # kWh/m³
            'emissions_natural_gas': 0.20,   # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,         # Biogenic CO2 (carbon neutral)
            'capex': 1800,                   # $/kW electrical (higher than CHP)
            'opex': 0.025,                   # $/kWh electrical
            'lifetime': 20,                  # years
            'min_load': 0.40,                # 40% minimum load
            'ramp_rate': 0.15,               # 15% per minute (faster than CHP)
            'start_up_time': 60,             # seconds (fast start)
            'part_load_efficiency_curve': {  # Efficiency at different loads
                0.4: 0.22,  # 22% at 40% load
                0.5: 0.24,
                0.7: 0.26,
                1.0: 0.28   # 28% at full load
            }
        }

    def calculate_outputs(self, fuel_input_kwh: float,
                         fuel_type: str = 'natural_gas',
                         load_fraction: float = 1.0) -> Dict:
        """
        Calculate microturbine outputs for given fuel input

        Args:
            fuel_input_kwh: Fuel energy input (kWh thermal)
            fuel_type: 'natural_gas' or 'biogas'
            load_fraction: Operating load (0.4 to 1.0)

        Returns:
            Dictionary with electricity, heat, and emissions
        """
        # Check minimum load
        if load_fraction < self.specs['min_load']:
            load_fraction = self.specs['min_load']
        elif load_fraction > 1.0:
            load_fraction = 1.0

        # Get efficiency at this load (interpolate)
        eff_curve = self.specs['part_load_efficiency_curve']
        loads = sorted(eff_curve.keys())

        # Find efficiency
        if load_fraction in eff_curve:
            electrical_eff = eff_curve[load_fraction]
        else:
            # Linear interpolation
            for i in range(len(loads) - 1):
                if loads[i] <= load_fraction <= loads[i+1]:
                    # Interpolate
                    x0, x1 = loads[i], loads[i+1]
                    y0, y1 = eff_curve[x0], eff_curve[x1]
                    electrical_eff = y0 + (y1 - y0) * (load_fraction - x0) / (x1 - x0)
                    break
            else:
                electrical_eff = self.specs['electrical_efficiency']

        # Calculate electricity output
        electricity_output = fuel_input_kwh * electrical_eff

        # Calculate exhaust heat available
        # Total energy - electricity = losses + exhaust heat
        # Assume 10% radiation/convection losses
        losses = fuel_input_kwh * 0.10
        exhaust_heat = fuel_input_kwh - electricity_output - losses

        # Calculate CO2 emissions
        if fuel_type == 'natural_gas':
            co2_emissions = fuel_input_kwh * self.specs['emissions_natural_gas']
            co2_concentration = 0.04  # 4% CO2 in exhaust (natural gas)
        elif fuel_type == 'biogas':
            co2_emissions = fuel_input_kwh * self.specs['emissions_biogas']  # Biogenic
            co2_concentration = 0.08  # 8% CO2 in exhaust (biogas has more CO2)
        else:
            co2_emissions = 0
            co2_concentration = 0

        # Exhaust gas flow rate (simplified)
        # Assume ~15 kg exhaust per kg fuel, ~10.5 kWh/kg fuel
        exhaust_flow_kg_h = (fuel_input_kwh / 10.5) * 15

        return {
            'fuel_input_kwh': fuel_input_kwh,
            'fuel_type': fuel_type,
            'load_fraction': load_fraction,
            'electrical_efficiency': electrical_eff,
            'electricity_kwh': electricity_output,
            'exhaust_heat_kwh': exhaust_heat,
            'exhaust_temperature_c': self.specs['exhaust_temperature'],
            'exhaust_flow_kg_h': exhaust_flow_kg_h,
            'co2_emissions_kg': co2_emissions,
            'co2_concentration': co2_concentration,
            'total_efficiency': (electricity_output + exhaust_heat) / fuel_input_kwh if fuel_input_kwh > 0 else 0
        }

    def calculate_fuel_requirement(self, electricity_demand_kwh: float,
                                   fuel_type: str = 'natural_gas',
                                   load_fraction: float = 1.0) -> Dict:
        """
        Calculate fuel requirement for desired electricity output

        Args:
            electricity_demand_kwh: Desired electricity output (kWh)
            fuel_type: 'natural_gas' or 'biogas'
            load_fraction: Operating load fraction

        Returns:
            Dictionary with fuel requirements and outputs
        """
        # Get efficiency at this load
        eff_curve = self.specs['part_load_efficiency_curve']
        loads = sorted(eff_curve.keys())

        if load_fraction in eff_curve:
            electrical_eff = eff_curve[load_fraction]
        else:
            electrical_eff = self.specs['electrical_efficiency']

        # Calculate required fuel input
        fuel_input_kwh = electricity_demand_kwh / electrical_eff

        # Get all outputs
        outputs = self.calculate_outputs(fuel_input_kwh, fuel_type, load_fraction)

        # Convert to fuel volume
        if fuel_type == 'natural_gas':
            fuel_volume_m3 = fuel_input_kwh / self.specs['natural_gas_lhv']
        elif fuel_type == 'biogas':
            fuel_volume_m3 = fuel_input_kwh / self.specs['biogas_lhv']
        else:
            fuel_volume_m3 = 0

        return {
            'electricity_demand_kwh': electricity_demand_kwh,
            'fuel_input_kwh': fuel_input_kwh,
            'fuel_volume_m3': fuel_volume_m3,
            'fuel_type': fuel_type,
            'exhaust_heat_kwh': outputs['exhaust_heat_kwh'],
            'co2_emissions_kg': outputs['co2_emissions_kg'],
            'co2_for_ccu_kg': outputs['co2_emissions_kg'],  # Available for CCU
            'exhaust_temperature_c': outputs['exhaust_temperature_c']
        }

    def check_operational_constraints(self, load_fraction: float,
                                     previous_load: float = None,
                                     time_step_minutes: float = 60) -> Dict:
        """
        Check if operation satisfies constraints

        Args:
            load_fraction: Current load as fraction of rated capacity (0-1)
            previous_load: Previous time step load fraction
            time_step_minutes: Time between steps (minutes)

        Returns:
            Dictionary with constraint check results
        """
        constraints_met = True
        violations = []

        # Minimum load constraint
        if load_fraction > 0 and load_fraction < self.specs['min_load']:
            constraints_met = False
            violations.append(
                f"Load {load_fraction:.1%} below minimum {self.specs['min_load']:.1%}"
            )

        # Ramp rate constraint
        if previous_load is not None:
            load_change = abs(load_fraction - previous_load)
            max_ramp = self.specs['ramp_rate'] * time_step_minutes  # per minute rate
            if load_change > max_ramp:
                constraints_met = False
                violations.append(
                    f"Ramp rate {load_change:.1%} exceeds maximum {max_ramp:.1%}"
                )

        return {
            'constraints_met': constraints_met,
            'violations': violations,
            'load_fraction': load_fraction,
            'min_load': self.specs['min_load'],
            'ramp_rate_per_min': self.specs['ramp_rate']
        }

    def calculate_annual_costs(self, annual_electricity_kwh: float,
                              fuel_price_per_m3: float,
                              fuel_type: str = 'natural_gas',
                              capacity_kw: float = 200) -> Dict:
        """
        Calculate annual costs for microturbine operation

        Args:
            annual_electricity_kwh: Annual electricity output
            fuel_price_per_m3: Fuel price ($/m³)
            fuel_type: 'natural_gas' or 'biogas'
            capacity_kw: Microturbine electrical capacity (kW)

        Returns:
            Cost breakdown dictionary
        """
        # Fuel requirements
        fuel_req = self.calculate_fuel_requirement(annual_electricity_kwh, fuel_type)

        # Fuel cost
        fuel_cost = fuel_req['fuel_volume_m3'] * fuel_price_per_m3

        # CAPEX (annualized)
        capex_total = self.calculate_total_capex(capacity_kw)
        annual_capex = capex_total / self.specs['lifetime']

        # OPEX
        annual_opex = self.calculate_annual_opex(annual_electricity_kwh)

        # Total annual cost
        total_cost = annual_capex + annual_opex + fuel_cost

        return {
            'capacity_kw': capacity_kw,
            'annual_electricity_kwh': annual_electricity_kwh,
            'annual_capex': annual_capex,
            'annual_opex': annual_opex,
            'annual_fuel_cost': fuel_cost,
            'total_annual_cost': total_cost,
            'cost_per_kwh_electricity': total_cost / annual_electricity_kwh if annual_electricity_kwh > 0 else 0,
            'exhaust_heat_kwh': fuel_req['exhaust_heat_kwh'],
            'co2_for_ccu_kg': fuel_req['co2_for_ccu_kg']
        }
