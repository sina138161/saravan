"""
Compatibility wrapper for sludge and biogas system models
Provides backward compatibility for old imports
"""

from typing import Dict


class SludgeManagementSystem:
    """
    Sludge Management System (Composting + Anaerobic Digestion)

    Provides backward compatibility for network_builder_simple.py
    """

    def get_composting_specs(self) -> Dict:
        """
        Get composting system specifications

        Returns:
            Composting specifications dictionary
        """
        return {
            'name': 'Aerobic_Composting',
            'sludge_input_ratio': 0.70,  # 70% sludge
            'biomass_input_ratio': 0.30,  # 30% biomass
            'compost_output_ratio': 0.50,  # 50% mass reduction (moisture loss)
            'duration_days': 60,  # 60 days composting
            'n_content': 0.02,  # 2% nitrogen content
            'p_content': 0.01,  # 1% phosphorus
            'k_content': 0.01,  # 1% potassium
            'market_price_per_ton': 50,  # $/ton
            'capex': 50000,  # $ (for composting facility)
            'opex': 10,  # $/ton processed
            'lifetime': 20  # years
        }

    def get_digester_specs(self) -> Dict:
        """
        Get anaerobic digester specifications

        Returns:
            Digester specifications dictionary
        """
        return {
            'name': 'Anaerobic_Digester',
            'sludge_input_ratio': 0.60,  # 60% sludge
            'biomass_input_ratio': 0.40,  # 40% biomass
            'biogas_yield_m3_per_kg': 0.40,  # m³ biogas per kg organic matter
            'biogas_lhv': 6.0,  # kWh/m³ (60% CH4)
            'methane_content': 0.60,  # 60% CH4
            'digestate_output_ratio': 0.85,  # 85% mass output as digestate
            'electricity_consumption_kwh_per_m3': 0.05,  # Electricity for mixing
            'heat_consumption_kwh_per_m3': 0.15,  # Heat to maintain 35°C
            'retention_time_days': 25,  # HRT
            'digester_temperature': 35,  # °C (mesophilic)
            'capex': 200000,  # $ (digester vessel + equipment)
            'opex': 0.15,  # $/m³ biogas produced
            'lifetime': 20  # years
        }


class CCUSystem:
    """
    Carbon Capture and Utilization System

    Provides backward compatibility for network_builder_simple.py
    """

    def get_specs(self) -> Dict:
        """
        Get CCU system specifications

        Returns:
            CCU specifications dictionary
        """
        return {
            'name': 'CCU_System',
            'capture_efficiency': 0.90,  # 90% CO2 capture
            'purity': 0.95,  # 95% pure CO2
            'electricity_kwh_per_kg_co2': 0.40,  # kWh per kg CO2 captured
            'heat_kwh_per_kg_co2': 0.10,  # kWh thermal per kg CO2
            'capex_per_ton_day': 50000,  # $ per ton/day capacity
            'opex_per_kg_co2': 0.05,  # $/kg CO2 captured
            'lifetime': 20  # years
        }


class MarketModel:
    """
    Market Model for selling products

    Provides backward compatibility for network_builder_simple.py
    """

    def get_prices(self) -> Dict:
        """
        Get market prices for various products

        Returns:
            Price dictionary ($/unit)
        """
        return {
            'compost_per_ton': 50,  # $/ton compost
            'digestate_per_ton': 30,  # $/ton digestate
            'co2_per_kg': 0.015,  # $/kg CO2 (VCC tier: $15/ton = $0.015/kg)
            'electricity_per_kwh': 0.12,  # $/kWh electricity feed-in
            'heat_per_kwh_thermal': 0.05  # $/kWh thermal energy
        }

    def get_limits(self) -> Dict:
        """
        Get market demand limits (maximum that can be sold)

        Returns:
            Limit dictionary (annual units)
        """
        return {
            'compost_tons_year': 1000,  # tons/year
            'digestate_tons_year': 2000,  # tons/year
            'co2_kg_year': 500000,  # kg/year
            'electricity_kwh_year': 1000000,  # kWh/year
            'heat_kwh_year': 500000  # kWh/year
        }
