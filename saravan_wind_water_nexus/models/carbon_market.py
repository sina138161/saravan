"""
Three-Tier Carbon Market Model for Wind-Water Energy Projects
Based on: Nature Scientific Reports 2025 framework
"""

from typing import Dict, List
from dataclasses import dataclass

# Optional pandas import for enhanced dataframe functionality
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None  # Set to None if not available


@dataclass
class CarbonMarketTier:
    """Carbon market tier specifications"""
    name: str
    price_per_ton: float  # $/tCO2
    transaction_cost: float  # Fraction (0-1)
    eligibility_criteria: str
    verification_cost: float  # $/year
    social_multiplier: float  # Bonus for social benefits


class CarbonMarket:
    """
    Three-Tier Carbon Market Model

    Tiers:
    - VCC: Voluntary Carbon Credits
    - CCC: Compliance Carbon Credits
    - PGC: Premium Green Credits (with co-benefits)
    """

    def __init__(self):
        """Initialize carbon market tiers and baseline emissions"""
        self.tiers = self._define_market_tiers()
        self.baseline_emissions = self._define_baseline_emissions()

    def _define_market_tiers(self) -> Dict[str, CarbonMarketTier]:
        """
        Define three-tier carbon market structure

        Based on current global carbon market prices (2024-2025)
        """
        tiers = {
            'VCC': CarbonMarketTier(
                name='Voluntary Carbon Credits',
                price_per_ton=15.0,  # $/tCO2
                transaction_cost=0.05,  # 5%
                eligibility_criteria='Any verified emission reduction',
                verification_cost=5000,  # $/year
                social_multiplier=1.0
            ),

            'CCC': CarbonMarketTier(
                name='Compliance Carbon Credits',
                price_per_ton=35.0,  # $/tCO2 (EU ETS equivalent)
                transaction_cost=0.10,  # 10%
                eligibility_criteria='Certified Emission Reductions (CER)',
                verification_cost=15000,  # $/year
                social_multiplier=1.0
            ),

            'PGC': CarbonMarketTier(
                name='Premium Green Credits',
                price_per_ton=50.0,  # $/tCO2
                transaction_cost=0.08,  # 8%
                eligibility_criteria='Renewable energy + water/social benefits',
                verification_cost=12000,  # $/year
                social_multiplier=1.3  # 30% bonus for co-benefits
            )
        }

        return tiers

    def _define_baseline_emissions(self) -> Dict:
        """
        Define baseline emissions for different energy sources

        Reference: IPCC 2023 emission factors
        """
        baseline = {
            'grid_electricity_iran': 0.550,  # kgCO2/kWh
            'diesel_generator': 0.650,  # kgCO2/kWh
            'diesel_water_pump': 0.750,  # kgCO2/kWh
            'natural_gas': 0.400,  # kgCO2/kWh
            'coal': 0.900,  # kgCO2/kWh

            # Life-cycle emissions for renewables
            'wind_turbine_lifecycle': 0.011,  # kgCO2/kWh
            'battery_lifecycle': 0.015,  # kgCO2/kWh
            'solar_pv_lifecycle': 0.045,  # kgCO2/kWh
        }

        return baseline

    def calculate_avoided_emissions(self, annual_energy_kwh: float,
                                   displaced_source: str = 'diesel_generator',
                                   include_lifecycle: bool = True) -> float:
        """
        Calculate annual CO2 emissions avoided

        Args:
            annual_energy_kwh: Annual energy produced (kWh)
            displaced_source: Baseline energy source being displaced
            include_lifecycle: Include wind turbine lifecycle emissions

        Returns:
            Annual CO2 avoided in metric tons
        """
        # Baseline emissions
        baseline_factor = self.baseline_emissions[displaced_source]
        baseline_emissions = annual_energy_kwh * baseline_factor / 1000  # tons CO2

        # Lifecycle emissions
        if include_lifecycle:
            lifecycle_factor = self.baseline_emissions['wind_turbine_lifecycle']
            lifecycle_emissions = annual_energy_kwh * lifecycle_factor / 1000  # tons CO2
        else:
            lifecycle_emissions = 0

        # Net avoided emissions
        co2_avoided = baseline_emissions - lifecycle_emissions

        return max(0, co2_avoided)

    def calculate_water_carbon_benefit(self, annual_water_m3: float,
                                      traditional_pumping: str = 'diesel_water_pump') -> float:
        """
        Calculate CO2 avoided from water pumping with renewables vs diesel

        Args:
            annual_water_m3: Annual water pumped (m³)
            traditional_pumping: Traditional pumping method

        Returns:
            Additional CO2 avoided (tons)
        """
        # Energy for water pumping (assume 1.0 kWh/m³)
        energy_per_m3 = 1.0  # kWh/m³
        total_energy = annual_water_m3 * energy_per_m3

        # Avoided emissions
        co2_avoided = self.calculate_avoided_emissions(
            total_energy,
            displaced_source=traditional_pumping
        )

        return co2_avoided

    def calculate_tier_revenue(self, co2_avoided_tons: float,
                               tier_name: str,
                               water_access_improvement: bool = False) -> Dict:
        """
        Calculate revenue for specific carbon market tier

        Args:
            co2_avoided_tons: Annual CO2 avoided (tons)
            tier_name: 'VCC', 'CCC', or 'PGC'
            water_access_improvement: Whether project improves water access

        Returns:
            Revenue breakdown dictionary
        """
        tier = self.tiers[tier_name]

        # Base price
        base_revenue = co2_avoided_tons * tier.price_per_ton

        # Apply social multiplier if applicable
        if tier_name == 'PGC' and water_access_improvement:
            multiplier = tier.social_multiplier
        else:
            multiplier = 1.0

        # Gross revenue
        gross_revenue = base_revenue * multiplier

        # Transaction costs
        transaction_cost = gross_revenue * tier.transaction_cost

        # Verification cost
        verification_cost = tier.verification_cost

        # Net revenue
        net_revenue = gross_revenue - transaction_cost - verification_cost

        return {
            'tier': tier_name,
            'tier_name': tier.name,
            'co2_avoided_tons': co2_avoided_tons,
            'price_per_ton': tier.price_per_ton,
            'social_multiplier': multiplier,
            'gross_revenue': gross_revenue,
            'transaction_cost': transaction_cost,
            'verification_cost': verification_cost,
            'net_revenue': net_revenue,
            'net_price_per_ton': net_revenue / co2_avoided_tons if co2_avoided_tons > 0 else 0
        }

    def optimize_tier_selection(self, co2_avoided_tons: float,
                                water_access_improvement: bool = False) -> Dict:
        """
        Select optimal carbon market tier based on maximum revenue

        Args:
            co2_avoided_tons: Annual CO2 avoided (tons)
            water_access_improvement: Water access co-benefit

        Returns:
            Optimal tier selection and comparison
        """
        # Calculate revenue for each tier
        tier_results = {}

        for tier_name in ['VCC', 'CCC', 'PGC']:
            tier_results[tier_name] = self.calculate_tier_revenue(
                co2_avoided_tons,
                tier_name,
                water_access_improvement
            )

        # Find optimal tier
        optimal_tier = max(tier_results.items(),
                          key=lambda x: x[1]['net_revenue'])

        # Comparison table
        comparison_data = [
            {
                'Tier': r['tier'],
                'Tier_Name': r['tier_name'],
                'Gross_Revenue_USD': r['gross_revenue'],
                'Transaction_Cost_USD': r['transaction_cost'],
                'Verification_Cost_USD': r['verification_cost'],
                'Net_Revenue_USD': r['net_revenue'],
                'Effective_Price_per_ton': r['net_price_per_ton']
            }
            for r in tier_results.values()
        ]

        # Use pandas DataFrame if available, otherwise return list of dicts
        comparison = pd.DataFrame(comparison_data) if HAS_PANDAS else comparison_data

        return {
            'optimal_tier': optimal_tier[0],
            'optimal_tier_data': optimal_tier[1],
            'comparison_table': comparison,
            'all_tier_results': tier_results
        }

    def calculate_20year_carbon_revenue(self, annual_co2_avoided: float,
                                       tier: str,
                                       water_benefit: bool = False,
                                       price_escalation: float = 0.03) -> Dict:
        """
        Calculate 20-year carbon revenue stream

        Args:
            annual_co2_avoided: Annual CO2 avoided (tons/year)
            tier: Carbon market tier
            water_benefit: Water access improvement
            price_escalation: Annual price increase (default 3%)

        Returns:
            20-year revenue projection
        """
        years = 20
        annual_revenues = []

        for year in range(years):
            # Escalate price
            escalated_price = self.tiers[tier].price_per_ton * ((1 + price_escalation) ** year)

            # Store original price
            original_price = self.tiers[tier].price_per_ton

            # Update price temporarily
            self.tiers[tier].price_per_ton = escalated_price

            # Calculate revenue
            revenue = self.calculate_tier_revenue(annual_co2_avoided, tier, water_benefit)

            # Restore original price
            self.tiers[tier].price_per_ton = original_price

            annual_revenues.append({
                'year': year + 1,
                'price_per_ton': escalated_price,
                'net_revenue': revenue['net_revenue']
            })

        # Use pandas DataFrame if available, otherwise use list of dicts
        df_revenues = pd.DataFrame(annual_revenues) if HAS_PANDAS else annual_revenues

        # Calculate NPV
        discount_rate = 0.08  # 8% discount rate
        if HAS_PANDAS:
            npv = sum(
                row['net_revenue'] / ((1 + discount_rate) ** (row['year'] - 1))
                for _, row in df_revenues.iterrows()
            )
            total_nominal = df_revenues['net_revenue'].sum()
            average_annual = df_revenues['net_revenue'].mean()
            final_year_revenue = df_revenues.iloc[-1]['net_revenue']
        else:
            npv = sum(
                row['net_revenue'] / ((1 + discount_rate) ** (row['year'] - 1))
                for row in annual_revenues
            )
            revenues_only = [row['net_revenue'] for row in annual_revenues]
            total_nominal = sum(revenues_only)
            average_annual = total_nominal / len(revenues_only) if revenues_only else 0
            final_year_revenue = annual_revenues[-1]['net_revenue'] if annual_revenues else 0

        return {
            'annual_revenues_df': df_revenues,
            'total_nominal': total_nominal,
            'npv_at_8pct': npv,
            'average_annual': average_annual,
            'final_year_revenue': final_year_revenue
        }

    def get_emission_factor(self, source: str) -> float:
        """
        Get emission factor for a source

        Args:
            source: Energy source name

        Returns:
            Emission factor (kgCO2/kWh)
        """
        return self.baseline_emissions.get(source, 0)

    def calculate_project_carbon_revenue(self, annual_energy_kwh: float,
                                         annual_water_m3: float,
                                         displaced_energy_source: str = 'diesel_generator',
                                         water_benefit: bool = True) -> Dict:
        """
        Calculate complete carbon revenue for project

        Args:
            annual_energy_kwh: Annual energy production
            annual_water_m3: Annual water pumped
            displaced_energy_source: Energy source being displaced
            water_benefit: Whether project improves water access

        Returns:
            Complete carbon revenue analysis
        """
        # Calculate emissions avoided
        co2_energy = self.calculate_avoided_emissions(
            annual_energy_kwh,
            displaced_energy_source
        )

        co2_water = self.calculate_water_carbon_benefit(
            annual_water_m3,
            'diesel_water_pump'
        )

        total_co2 = co2_energy + co2_water

        # Optimize tier selection
        optimization = self.optimize_tier_selection(
            total_co2,
            water_access_improvement=water_benefit
        )

        # 20-year projection
        projection = self.calculate_20year_carbon_revenue(
            total_co2,
            optimization['optimal_tier'],
            water_benefit=water_benefit,
            price_escalation=0.03
        )

        return {
            'co2_energy_tons': co2_energy,
            'co2_water_tons': co2_water,
            'total_co2_tons': total_co2,
            'optimization': optimization,
            'projection_20year': projection,
            'annual_revenue': optimization['optimal_tier_data']['net_revenue'],
            'optimal_tier': optimization['optimal_tier']
        }


# Backward compatibility alias
CarbonMarketModel = CarbonMarket
