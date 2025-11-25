"""
Carbon Capture and Utilization (CCU) System Model
Captures CO2 from flue gas for industrial use
"""

from typing import Dict
from ..base import TechnologyBase


class CCU(TechnologyBase):
    """
    Carbon Capture and Utilization (CCU) System

    Captures CO2 from:
    - Gas boiler exhaust
    - CHP exhaust
    - Biogas upgrading

    Output:
    - Pure CO2 for industrial use (food, beverage, greenhouse)
    """

    def _define_specs(self) -> Dict:
        """
        Define CCU system specifications

        Based on: Commercial CO2 capture systems
        """
        return {
            'name': 'Carbon_Capture_Utilization',
            'capture_efficiency': 0.90,      # 90% of CO2 captured
            'electricity_kwh_per_kg_co2': 0.30,  # Energy for capture & compression
            'purity': 0.995,                 # 99.5% pure CO2
            'storage_pressure_bar': 150,     # High pressure storage
            'capex': 50000,                  # $ per ton/day capacity
            'opex': 0.05,                    # $/kg CO2 captured
            'lifetime': 20,                  # years
            'market_price_per_kg': 0.15,     # $/kg CO2 (food grade)
            'co2_content_natural_gas': 0.20, # kg CO2 per kWh thermal input
            'co2_content_biogas': 0.40       # Biogas contains 40% CO2 by volume
        }

    def calculate_co2_available(self, fuel_input_kwh: float,
                               fuel_type: str = 'natural_gas') -> Dict:
        """
        Calculate CO2 available for capture from fuel combustion

        Args:
            fuel_input_kwh: Fuel energy input (kWh thermal)
            fuel_type: 'natural_gas' or 'biogas'

        Returns:
            CO2 availability details
        """
        if fuel_type == 'natural_gas':
            co2_produced_kg = fuel_input_kwh * self.specs['co2_content_natural_gas']
        elif fuel_type == 'biogas':
            # Biogas combustion produces CO2, but it's biogenic (carbon neutral)
            # CCU can still capture it for utilization
            co2_produced_kg = fuel_input_kwh * self.specs['co2_content_natural_gas']
        else:
            co2_produced_kg = 0

        # Capturable CO2
        co2_capturable_kg = co2_produced_kg * self.specs['capture_efficiency']

        # Energy requirement
        electricity_required_kwh = co2_capturable_kg * self.specs['electricity_kwh_per_kg_co2']

        return {
            'fuel_input_kwh': fuel_input_kwh,
            'fuel_type': fuel_type,
            'co2_produced_kg': co2_produced_kg,
            'capture_efficiency': self.specs['capture_efficiency'],
            'co2_captured_kg': co2_capturable_kg,
            'co2_purity': self.specs['purity'],
            'electricity_required_kwh': electricity_required_kwh,
            'energy_penalty_pct': electricity_required_kwh / fuel_input_kwh * 100 if fuel_input_kwh > 0 else 0
        }

    def calculate_biogas_upgrading(self, biogas_m3: float,
                                   methane_content: float = 0.60) -> Dict:
        """
        Calculate CO2 recovery from biogas upgrading

        Biogas typically contains 40% CO2 which must be removed to upgrade to
        natural gas quality (>95% CH4)

        Args:
            biogas_m3: Volume of raw biogas (m³)
            methane_content: Methane fraction in biogas (default 0.60)

        Returns:
            CO2 recovery and upgraded gas details
        """
        # CO2 content in biogas
        co2_content = 1 - methane_content  # Remaining is mostly CO2

        # CO2 volume
        co2_volume_m3 = biogas_m3 * co2_content

        # Convert to mass (CO2 density ~1.98 kg/m³ at STP)
        co2_mass_kg = co2_volume_m3 * 1.98

        # Captured CO2 (with efficiency)
        co2_captured_kg = co2_mass_kg * self.specs['capture_efficiency']

        # Energy requirement
        electricity_required_kwh = co2_captured_kg * self.specs['electricity_kwh_per_kg_co2']

        # Upgraded biogas (mostly methane)
        upgraded_biogas_m3 = biogas_m3 * methane_content / 0.95  # Assume 95% purity target

        return {
            'raw_biogas_m3': biogas_m3,
            'methane_content_input': methane_content,
            'co2_volume_m3': co2_volume_m3,
            'co2_mass_kg': co2_mass_kg,
            'co2_captured_kg': co2_captured_kg,
            'upgraded_biogas_m3': upgraded_biogas_m3,
            'upgraded_methane_content': 0.95,
            'electricity_required_kwh': electricity_required_kwh
        }

    def calculate_revenue(self, co2_captured_kg: float) -> Dict:
        """
        Calculate revenue from CO2 sales

        Args:
            co2_captured_kg: CO2 captured (kg)

        Returns:
            Revenue details
        """
        # Market price
        market_price = self.specs['market_price_per_kg']

        # Gross revenue
        gross_revenue = co2_captured_kg * market_price

        # Operating cost
        operating_cost = co2_captured_kg * self.specs['opex']

        # Net revenue
        net_revenue = gross_revenue - operating_cost

        return {
            'co2_captured_kg': co2_captured_kg,
            'co2_captured_ton': co2_captured_kg / 1000,
            'market_price_per_kg': market_price,
            'gross_revenue': gross_revenue,
            'operating_cost': operating_cost,
            'net_revenue': net_revenue,
            'profit_margin': net_revenue / gross_revenue if gross_revenue > 0 else 0
        }

    def calculate_economics(self, annual_fuel_kwh: float,
                           fuel_type: str = 'natural_gas',
                           electricity_cost_per_kwh: float = 0.10) -> Dict:
        """
        Calculate complete economics for CCU system

        Args:
            annual_fuel_kwh: Annual fuel consumption (kWh)
            fuel_type: 'natural_gas' or 'biogas'
            electricity_cost_per_kwh: Cost of electricity ($/kWh)

        Returns:
            Economic analysis
        """
        # CO2 capture
        capture = self.calculate_co2_available(annual_fuel_kwh, fuel_type)

        # Revenue
        revenue = self.calculate_revenue(capture['co2_captured_kg'])

        # Electricity cost
        electricity_cost = capture['electricity_required_kwh'] * electricity_cost_per_kwh

        # CAPEX (based on daily capacity)
        daily_co2_kg = capture['co2_captured_kg'] / 365
        daily_co2_ton = daily_co2_kg / 1000
        total_capex = self.specs['capex'] * daily_co2_ton
        annual_capex = total_capex / self.specs['lifetime']

        # Total annual cost
        total_annual_cost = annual_capex + revenue['operating_cost'] + electricity_cost

        # Net benefit
        net_annual_benefit = revenue['gross_revenue'] - total_annual_cost

        # NPV calculation
        npv = self.calculate_npv(
            capex=total_capex,
            annual_revenue=revenue['gross_revenue'],
            annual_opex=revenue['operating_cost'] + electricity_cost,
            discount_rate=0.08
        )

        return {
            'capture': capture,
            'revenue': revenue,
            'electricity_cost': electricity_cost,
            'capex': total_capex,
            'annual_capex': annual_capex,
            'annual_opex': revenue['operating_cost'],
            'total_annual_cost': total_annual_cost,
            'net_annual_benefit': net_annual_benefit,
            'npv': npv,
            'payback_period': self.calculate_payback_period(
                total_capex,
                revenue['gross_revenue'],
                revenue['operating_cost'] + electricity_cost
            ) if net_annual_benefit > 0 else float('inf')
        }

    def calculate_market_potential(self, annual_co2_captured_kg: float,
                                  market_segments: Dict = None) -> Dict:
        """
        Analyze market potential for captured CO2

        Args:
            annual_co2_captured_kg: Annual CO2 production (kg)
            market_segments: Dictionary of market segments and their limits

        Returns:
            Market analysis
        """
        if market_segments is None:
            # Default market segments (annual kg limits)
            market_segments = {
                'food_beverage': {
                    'demand_kg': 50000,
                    'price_per_kg': 0.18,
                    'description': 'Food grade CO2 for beverages and food processing'
                },
                'greenhouse': {
                    'demand_kg': 30000,
                    'price_per_kg': 0.12,
                    'description': 'Agricultural CO2 for greenhouse enrichment'
                },
                'industrial': {
                    'demand_kg': 20000,
                    'price_per_kg': 0.10,
                    'description': 'Industrial processes and welding'
                }
            }

        # Allocate captured CO2 to markets (priority order)
        remaining_co2 = annual_co2_captured_kg
        allocation = {}
        total_revenue = 0

        for market, details in market_segments.items():
            if remaining_co2 > 0:
                allocated = min(remaining_co2, details['demand_kg'])
                revenue = allocated * details['price_per_kg']

                allocation[market] = {
                    'allocated_kg': allocated,
                    'price_per_kg': details['price_per_kg'],
                    'revenue': revenue,
                    'utilization_pct': allocated / details['demand_kg'] * 100
                }

                total_revenue += revenue
                remaining_co2 -= allocated

        return {
            'total_co2_kg': annual_co2_captured_kg,
            'allocated_kg': annual_co2_captured_kg - remaining_co2,
            'unallocated_kg': remaining_co2,
            'allocation': allocation,
            'total_revenue': total_revenue,
            'avg_price_per_kg': total_revenue / (annual_co2_captured_kg - remaining_co2) if (annual_co2_captured_kg - remaining_co2) > 0 else 0
        }
