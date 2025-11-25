"""
Gas Boiler Model
Heat-only boiler for thermal energy production
"""

from typing import Dict
from ..base import TechnologyBase


class GasBoiler(TechnologyBase):
    """
    Gas Boiler System

    Can operate on:
    - Natural gas (from grid)
    - Biogas (from anaerobic digester)

    Outputs:
    - Heat
    - CO2 emissions
    """

    def _define_specs(self) -> Dict:
        """
        Define gas boiler specifications

        Based on: Commercial boiler systems and industry standards
        """
        return {
            'name': 'Gas_Boiler_Heat_Only',
            'thermal_efficiency': 0.85,      # 85% efficiency
            'natural_gas_lhv': 10.0,         # kWh/m³
            'biogas_lhv': 6.0,               # kWh/m³
            'emissions_natural_gas': 0.20,   # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,         # Biogenic CO2 (carbon neutral)
            'capex': 150,                    # $/kW thermal
            'opex': 0.01,                    # $/kWh heat output
            'lifetime': 20,                  # years
            'min_load': 0.20,                # 20% minimum load
            'ramp_rate': 0.20                # 20% per hour (faster than CHP)
        }

    def calculate_heat_output(self, fuel_input_kwh: float,
                             fuel_type: str = 'natural_gas') -> Dict:
        """
        Calculate heat output for given fuel input

        Formula:
            p_gb(t) = η_gb × q_gb(t) × LHV_ch4

        Where:
            p_gb(t): Output heating power of GB (kWh)
            q_gb(t): Amount of NG consumed by GB (m³)
            η_gb: Operating efficiency of the GB
            LHV_ch4: Lower heating value of fuel (kWh/m³)

        Args:
            fuel_input_kwh: Fuel energy input (kWh thermal) = q_gb(t) × LHV_ch4
            fuel_type: 'natural_gas' or 'biogas'

        Returns:
            Dictionary with heat output and emissions
        """
        # Get boiler efficiency η_gb
        eta_gb = self.specs['thermal_efficiency']

        # Calculate heat output using exact formula
        # p_gb(t) = η_gb × q_gb(t) × LHV_ch4
        # where fuel_input_kwh = q_gb(t) × LHV_ch4
        p_gb = eta_gb * fuel_input_kwh
        heat_output = p_gb

        # Calculate emissions
        if fuel_type == 'natural_gas':
            co2_emissions = fuel_input_kwh * self.specs['emissions_natural_gas']
        elif fuel_type == 'biogas':
            co2_emissions = fuel_input_kwh * self.specs['emissions_biogas']
        else:
            co2_emissions = 0

        return {
            'p_gb_kwh': p_gb,
            'heat_kwh': heat_output,
            'eta_gb': eta_gb,
            'fuel_input_kwh': fuel_input_kwh,
            'co2_emissions_kg': co2_emissions,
            'efficiency': heat_output / fuel_input_kwh if fuel_input_kwh > 0 else 0
        }

    def calculate_fuel_requirement(self, heat_demand_kwh: float,
                                   fuel_type: str = 'natural_gas') -> Dict:
        """
        Calculate fuel requirement for desired heat output

        From formula: p_gb(t) = η_gb × q_gb(t) × LHV_ch4
        Solve for q_gb(t): q_gb(t) = p_gb(t) / (η_gb × LHV_ch4)

        Args:
            heat_demand_kwh: Desired heat output (kWh) = p_gb(t)
            fuel_type: 'natural_gas' or 'biogas'

        Returns:
            Dictionary with fuel requirements
        """
        # Get boiler efficiency η_gb
        eta_gb = self.specs['thermal_efficiency']

        # Calculate required fuel input
        # From p_gb(t) = η_gb × q_gb(t) × LHV_ch4
        # fuel_input_kwh = q_gb(t) × LHV_ch4 = p_gb(t) / η_gb
        fuel_input_kwh = heat_demand_kwh / eta_gb

        # Convert to fuel volume
        if fuel_type == 'natural_gas':
            fuel_volume_m3 = fuel_input_kwh / self.specs['natural_gas_lhv']
            co2_emissions = fuel_input_kwh * self.specs['emissions_natural_gas']
        elif fuel_type == 'biogas':
            fuel_volume_m3 = fuel_input_kwh / self.specs['biogas_lhv']
            co2_emissions = 0  # Carbon neutral
        else:
            fuel_volume_m3 = 0
            co2_emissions = 0

        return {
            'fuel_input_kwh': fuel_input_kwh,
            'fuel_volume_m3': fuel_volume_m3,
            'fuel_type': fuel_type,
            'heat_output_kwh': heat_demand_kwh,
            'co2_emissions_kg': co2_emissions
        }

    def check_operational_constraints(self, load_fraction: float,
                                     previous_load: float = None) -> Dict:
        """
        Check if operation satisfies constraints

        Args:
            load_fraction: Current load as fraction of rated capacity (0-1)
            previous_load: Previous hour load fraction (for ramp rate check)

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
            max_ramp = self.specs['ramp_rate']
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
            'ramp_rate': self.specs['ramp_rate']
        }

    def calculate_annual_costs(self, annual_heat_kwh: float,
                              fuel_price_per_m3: float,
                              fuel_type: str = 'natural_gas',
                              capacity_kw: float = 1000) -> Dict:
        """
        Calculate annual costs for boiler operation

        Args:
            annual_heat_kwh: Annual heat output
            fuel_price_per_m3: Fuel price ($/m³)
            fuel_type: 'natural_gas' or 'biogas'
            capacity_kw: Boiler thermal capacity (kW)

        Returns:
            Cost breakdown dictionary
        """
        # Fuel requirements
        fuel_req = self.calculate_fuel_requirement(annual_heat_kwh, fuel_type)

        # Fuel cost
        fuel_cost = fuel_req['fuel_volume_m3'] * fuel_price_per_m3

        # CAPEX (annualized)
        capex_total = self.calculate_total_capex(capacity_kw)
        annual_capex = capex_total / self.specs['lifetime']

        # OPEX
        annual_opex = self.calculate_annual_opex(annual_heat_kwh)

        # Total annual cost
        total_cost = annual_capex + annual_opex + fuel_cost

        return {
            'annual_capex': annual_capex,
            'annual_opex': annual_opex,
            'annual_fuel_cost': fuel_cost,
            'total_annual_cost': total_cost,
            'cost_per_kwh_heat': total_cost / annual_heat_kwh if annual_heat_kwh > 0 else 0
        }

    def compare_with_chp(self, annual_heat_kwh: float,
                        chp_specs: Dict) -> Dict:
        """
        Compare boiler with CHP for heat production

        Args:
            annual_heat_kwh: Annual heat demand
            chp_specs: CHP specifications dictionary

        Returns:
            Comparison results
        """
        # Boiler efficiency
        boiler_fuel_kwh = annual_heat_kwh / self.specs['thermal_efficiency']

        # CHP would need to run at capacity to meet heat demand
        # CHP produces electricity as co-product
        chp_fuel_kwh = annual_heat_kwh / chp_specs.get('thermal_efficiency', 0.45)
        chp_electricity_kwh = chp_fuel_kwh * chp_specs.get('electrical_efficiency', 0.35)

        return {
            'boiler_fuel_kwh': boiler_fuel_kwh,
            'boiler_efficiency': self.specs['thermal_efficiency'],
            'chp_fuel_kwh': chp_fuel_kwh,
            'chp_efficiency': chp_specs.get('total_efficiency', 0.80),
            'chp_bonus_electricity_kwh': chp_electricity_kwh,
            'fuel_savings_pct': (boiler_fuel_kwh - chp_fuel_kwh) / boiler_fuel_kwh * 100 if boiler_fuel_kwh > 0 else 0
        }
