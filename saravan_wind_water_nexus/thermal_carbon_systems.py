"""
Thermal and Carbon Systems Models
Includes CHP, Gas Boiler, Sludge Management, CCU, and Market Models
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple


class CHPModel:
    """
    Combined Heat and Power (CHP) Model

    Can operate on:
    - Natural gas (from grid)
    - Biogas (from anaerobic digester)

    Outputs:
    - Electricity
    - Heat
    - CO2 emissions
    """

    def __init__(self):
        """Initialize CHP specifications"""
        self.specs = {
            'electrical_efficiency': 0.35,  # 35% electricity
            'thermal_efficiency': 0.45,     # 45% heat
            'total_efficiency': 0.80,        # 80% combined
            'natural_gas_lhv': 10.0,         # kWh/m³ (Lower Heating Value)
            'biogas_lhv': 6.0,               # kWh/m³ (depends on methane content)
            'emissions_natural_gas': 0.20,   # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,         # Biogenic CO2 (carbon neutral)
            'capex': 1500,                   # $/kW electrical
            'opex_per_kwh': 0.02,            # $/kWh
            'min_load': 0.30,                # 30% minimum load
            'ramp_rate': 0.10                # 10% per hour
        }

    def get_specs(self):
        """Get CHP specifications"""
        return self.specs


class GasBoilerModel:
    """
    Gas Boiler Model

    Can operate on:
    - Natural gas (from grid)
    - Biogas (from anaerobic digester)

    Outputs:
    - Heat
    - CO2 emissions
    """

    def __init__(self):
        """Initialize gas boiler specifications"""
        self.specs = {
            'thermal_efficiency': 0.85,      # 85% efficiency
            'natural_gas_lhv': 10.0,         # kWh/m³
            'biogas_lhv': 6.0,               # kWh/m³
            'emissions_natural_gas': 0.20,   # kg CO2/kWh thermal input
            'emissions_biogas': 0.0,         # Biogenic CO2 (carbon neutral)
            'capex': 150,                    # $/kW thermal
            'opex_per_kwh': 0.01,            # $/kWh
            'min_load': 0.20,                # 20% minimum load
        }

    def get_specs(self):
        """Get boiler specifications"""
        return self.specs


class SludgeManagementSystem:
    """
    Sludge Management System

    Includes:
    1. Composting: Sludge + Biomass → Compost (fertilizer)
    2. Anaerobic Digester: Sludge + Biomass + Heat + Electricity → Biogas + Digestate (fertilizer)
    """

    def __init__(self):
        """Initialize sludge management specifications"""
        self.composting = {
            'sludge_input_ratio': 0.70,          # 70% sludge, 30% biomass
            'biomass_input_ratio': 0.30,
            'compost_output_ratio': 0.50,        # 50% mass reduction (moisture loss)
            'duration_days': 60,                 # 60 days composting
            'n_content': 0.02,                   # 2% nitrogen content
            'p_content': 0.01,                   # 1% phosphorus
            'k_content': 0.01,                   # 1% potassium
            'market_price_per_ton': 50,          # $/ton
            'capex': 50000,                      # $ (for composting facility)
            'opex_per_ton': 10                   # $/ton processed
        }

        self.anaerobic_digester = {
            'sludge_input_ratio': 0.60,          # 60% sludge, 40% biomass
            'biomass_input_ratio': 0.40,
            'biogas_yield_m3_per_kg': 0.40,      # 0.4 m³ biogas per kg organic matter
            'methane_content': 0.60,             # 60% CH4, 40% CO2
            'biogas_lhv': 6.0,                   # kWh/m³
            'digestate_output_ratio': 0.85,      # 85% of input mass
            'digestate_n_content': 0.03,         # 3% nitrogen
            'digestate_p_content': 0.015,        # 1.5% phosphorus
            'digestate_k_content': 0.015,        # 1.5% potassium
            'digestate_market_price_per_ton': 60, # $/ton (higher quality than compost)
            'electricity_consumption_kwh_per_m3': 0.10,  # For mixing, pumping
            'heat_consumption_kwh_per_m3': 2.0,          # For maintaining 35°C
            'capex': 200000,                     # $ (for digester)
            'opex_per_m3_biogas': 0.15,          # $/m³ biogas
            'retention_time_days': 20            # 20 days hydraulic retention time
        }

    def get_composting_specs(self):
        """Get composting specifications"""
        return self.composting

    def get_digester_specs(self):
        """Get anaerobic digester specifications"""
        return self.anaerobic_digester

    def calculate_sludge_production(self, wastewater_treated_m3: float) -> float:
        """
        Calculate sludge production from wastewater treatment

        Args:
            wastewater_treated_m3: Volume of wastewater treated

        Returns:
            Sludge produced (kg dry solids)
        """
        # Typical sludge production: 50-100 g dry solids per m³ wastewater
        sludge_production_kg_per_m3 = 0.075  # 75 g/m³ (average)
        return wastewater_treated_m3 * sludge_production_kg_per_m3


class CCUSystem:
    """
    Carbon Capture and Utilization (CCU) System

    Captures CO2 from:
    - Gas boiler exhaust
    - CHP exhaust

    Output:
    - Pure CO2 for industrial use (food, beverage, greenhouse)
    """

    def __init__(self):
        """Initialize CCU specifications"""
        self.specs = {
            'capture_efficiency': 0.90,      # 90% of CO2 captured
            'electricity_kwh_per_kg_co2': 0.30,  # Energy for capture & compression
            'purity': 0.995,                 # 99.5% pure CO2
            'storage_pressure_bar': 150,     # High pressure storage
            'capex_per_ton_day': 50000,      # $ per ton/day capacity
            'opex_per_kg_co2': 0.05,         # $/kg CO2
            'market_price_per_kg': 0.15,     # $/kg CO2 (food grade)
        }

    def get_specs(self):
        """Get CCU specifications"""
        return self.specs


class MarketModel:
    """
    Market Model for Selling Products

    Products:
    1. Compost (fertilizer)
    2. Digestate (fertilizer)
    3. CO2 (industrial)
    4. Excess electricity (grid)
    5. Excess heat (industrial)
    """

    def __init__(self):
        """Initialize market prices"""
        self.prices = {
            'compost_per_ton': 50,           # $/ton
            'digestate_per_ton': 60,         # $/ton (higher quality)
            'co2_per_kg': 0.15,              # $/kg (food/beverage grade)
            'electricity_per_kwh': 0.10,     # $/kWh (feed-in tariff)
            'heat_per_kwh_thermal': 0.05,    # $/kWh-thermal (industrial)
        }

        # Market limits (annual)
        self.market_limits = {
            'compost_tons_year': 500,        # Local agricultural market
            'digestate_tons_year': 500,      # Local agricultural market
            'co2_kg_year': 50000,            # Local industrial demand
            'electricity_kwh_year': 1e6,     # Grid connection limit
            'heat_kwh_year': 500000,         # Local industrial demand
        }

    def get_prices(self):
        """Get market prices"""
        return self.prices

    def get_limits(self):
        """Get market limits"""
        return self.market_limits

    def calculate_revenue(self, sales: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate revenue from sales

        Args:
            sales: Dictionary with product quantities
                   e.g., {'compost_tons': 100, 'co2_kg': 10000, ...}

        Returns:
            Revenue breakdown
        """
        revenue = {}
        total_revenue = 0

        if 'compost_tons' in sales:
            rev = sales['compost_tons'] * self.prices['compost_per_ton']
            revenue['compost'] = rev
            total_revenue += rev

        if 'digestate_tons' in sales:
            rev = sales['digestate_tons'] * self.prices['digestate_per_ton']
            revenue['digestate'] = rev
            total_revenue += rev

        if 'co2_kg' in sales:
            rev = sales['co2_kg'] * self.prices['co2_per_kg']
            revenue['co2'] = rev
            total_revenue += rev

        if 'electricity_kwh' in sales:
            rev = sales['electricity_kwh'] * self.prices['electricity_per_kwh']
            revenue['electricity'] = rev
            total_revenue += rev

        if 'heat_kwh' in sales:
            rev = sales['heat_kwh'] * self.prices['heat_per_kwh_thermal']
            revenue['heat'] = rev
            total_revenue += rev

        revenue['total'] = total_revenue

        return revenue


# Example usage and testing
if __name__ == "__main__":
    print("="*80)
    print("THERMAL AND CARBON SYSTEMS MODELS")
    print("="*80)

    # CHP Model
    print("\n1. CHP (Combined Heat & Power)")
    print("-"*80)
    chp = CHPModel()
    print(f"Electrical efficiency: {chp.specs['electrical_efficiency']*100}%")
    print(f"Thermal efficiency: {chp.specs['thermal_efficiency']*100}%")
    print(f"Total efficiency: {chp.specs['total_efficiency']*100}%")

    # Example: 1000 kWh natural gas input
    gas_input = 1000  # kWh
    elec_output = gas_input * chp.specs['electrical_efficiency']
    heat_output = gas_input * chp.specs['thermal_efficiency']
    co2_emissions = gas_input * chp.specs['emissions_natural_gas']

    print(f"\nExample: {gas_input} kWh natural gas input:")
    print(f"   Electricity output: {elec_output:.1f} kWh")
    print(f"   Heat output: {heat_output:.1f} kWh")
    print(f"   CO2 emissions: {co2_emissions:.1f} kg")

    # Gas Boiler Model
    print("\n\n2. GAS BOILER")
    print("-"*80)
    boiler = GasBoilerModel()
    print(f"Thermal efficiency: {boiler.specs['thermal_efficiency']*100}%")

    heat_output = gas_input * boiler.specs['thermal_efficiency']
    co2_emissions = gas_input * boiler.specs['emissions_natural_gas']

    print(f"\nExample: {gas_input} kWh natural gas input:")
    print(f"   Heat output: {heat_output:.1f} kWh")
    print(f"   CO2 emissions: {co2_emissions:.1f} kg")

    # Sludge Management
    print("\n\n3. SLUDGE MANAGEMENT SYSTEM")
    print("-"*80)
    sludge_system = SludgeManagementSystem()

    print("Composting:")
    print(f"   Compost output: {sludge_system.composting['compost_output_ratio']*100}% of input")
    print(f"   Market price: ${sludge_system.composting['market_price_per_ton']}/ton")

    print("\nAnaerobic Digester:")
    print(f"   Biogas yield: {sludge_system.anaerobic_digester['biogas_yield_m3_per_kg']} m³/kg")
    print(f"   Methane content: {sludge_system.anaerobic_digester['methane_content']*100}%")
    print(f"   Digestate price: ${sludge_system.anaerobic_digester['digestate_market_price_per_ton']}/ton")

    # CCU System
    print("\n\n4. CARBON CAPTURE & UTILIZATION (CCU)")
    print("-"*80)
    ccu = CCUSystem()
    print(f"Capture efficiency: {ccu.specs['capture_efficiency']*100}%")
    print(f"Energy consumption: {ccu.specs['electricity_kwh_per_kg_co2']} kWh/kg CO2")
    print(f"Market price: ${ccu.specs['market_price_per_kg']}/kg CO2")

    # Market Model
    print("\n\n5. MARKET MODEL")
    print("-"*80)
    market = MarketModel()

    print("Market Prices:")
    for product, price in market.prices.items():
        print(f"   {product}: ${price}")

    print("\nMarket Limits (annual):")
    for product, limit in market.market_limits.items():
        print(f"   {product}: {limit:,.0f}")

    # Example revenue calculation
    print("\n\nExample Revenue Calculation:")
    print("-"*80)
    sales = {
        'compost_tons': 100,
        'co2_kg': 10000,
        'electricity_kwh': 50000,
        'heat_kwh': 20000
    }

    revenue = market.calculate_revenue(sales)
    print(f"Sales:")
    for product, quantity in sales.items():
        print(f"   {product}: {quantity:,.0f}")

    print(f"\nRevenue:")
    for product, rev in revenue.items():
        print(f"   {product}: ${rev:,.2f}")
