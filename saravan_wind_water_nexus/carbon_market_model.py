"""
Three-Tier Carbon Market Model for Wind-Water Energy Projects
Based on: Nature Scientific Reports 2025 framework
https://doi.org/10.1038/s41598-025-21623-0
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
from dataclasses import dataclass


@dataclass
class CarbonMarketTier:
    """Carbon market tier specifications"""
    name: str
    price_per_ton: float  # $/tCO2
    transaction_cost: float  # Fraction (0-1)
    eligibility_criteria: str
    verification_cost: float  # $/year
    social_multiplier: float  # Bonus for social benefits


class CarbonMarketModel:
    """
    Three-tier carbon market model integrating:
    - Tier 1: Voluntary Carbon Credits (VCC)
    - Tier 2: Compliance Carbon Credits (CCC)
    - Tier 3: Premium Green Credits (PGC)
    """

    def __init__(self):
        """Initialize carbon market tiers"""
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
                price_per_ton=15.0,  # $/tCO2 (voluntary market average)
                transaction_cost=0.05,  # 5% (brokerage + platform fees)
                eligibility_criteria='Any verified emission reduction',
                verification_cost=5000,  # $/year (third-party verification)
                social_multiplier=1.0  # No bonus
            ),

            'CCC': CarbonMarketTier(
                name='Compliance Carbon Credits',
                price_per_ton=35.0,  # $/tCO2 (EU ETS equivalent)
                transaction_cost=0.10,  # 10% (higher regulatory costs)
                eligibility_criteria='Certified Emission Reductions (CER)',
                verification_cost=15000,  # $/year (rigorous verification)
                social_multiplier=1.0  # No bonus
            ),

            'PGC': CarbonMarketTier(
                name='Premium Green Credits',
                price_per_ton=50.0,  # $/tCO2 (premium market for co-benefits)
                transaction_cost=0.08,  # 8% (specialized platform)
                eligibility_criteria='Renewable energy + water/social benefits',
                verification_cost=12000,  # $/year (sustainability certification)
                social_multiplier=1.3  # 30% bonus for water access improvement
            )
        }

        return tiers

    def _define_baseline_emissions(self) -> Dict:
        """
        Define baseline emissions for different energy sources

        Reference: IPCC 2023 emission factors
        """

        baseline = {
            'grid_electricity_iran': 0.550,  # kgCO2/kWh (Iran grid mix)
            'diesel_generator': 0.650,  # kgCO2/kWh
            'diesel_water_pump': 0.750,  # kgCO2/kWh (less efficient)
            'natural_gas': 0.400,  # kgCO2/kWh
            'coal': 0.900,  # kgCO2/kWh

            # Life-cycle emissions for renewables
            'wind_turbine_lifecycle': 0.011,  # kgCO2/kWh (manufacturing + O&M)
            'battery_lifecycle': 0.015,  # kgCO2/kWh (Li-ion batteries)
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

        # Wind turbine lifecycle emissions
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

        # Typical energy for water pumping: 0.5-1.5 kWh/m³ depending on depth
        # Saravan average well depth ~100m, assume 1.0 kWh/m³
        energy_per_m3 = 1.0  # kWh/m³

        total_energy = annual_water_m3 * energy_per_m3

        # Avoided emissions from using wind instead of diesel for pumping
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
            Dictionary with revenue breakdown
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

        # Annual verification cost
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
                                water_access_improvement: bool = False,
                                project_location: str = 'iran') -> Dict:
        """
        Select optimal carbon market tier based on maximum revenue

        Args:
            co2_avoided_tons: Annual CO2 avoided (tons)
            water_access_improvement: Water access co-benefit
            project_location: Location for eligibility

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

        comparison = pd.DataFrame([
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
        ])

        return {
            'optimal_tier': optimal_tier[0],
            'optimal_tier_data': optimal_tier[1],
            'comparison_table': comparison,
            'recommendation': self._generate_recommendation(optimal_tier[0], tier_results)
        }

    def _generate_recommendation(self, optimal_tier: str,
                                 tier_results: Dict) -> str:
        """Generate recommendation text"""

        optimal_data = tier_results[optimal_tier]

        recommendation = f"""
CARBON MARKET TIER RECOMMENDATION:
{'='*70}

Optimal Tier: {optimal_tier} - {optimal_data['tier_name']}

Annual Net Revenue: ${optimal_data['net_revenue']:,.2f}
Effective Price: ${optimal_data['net_price_per_ton']:.2f}/tCO2

Rationale:
"""

        if optimal_tier == 'VCC':
            recommendation += """
- Easiest to access (low barrier to entry)
- Lower verification costs
- Suitable for small-scale projects
- Fast time-to-market for carbon credits
"""
        elif optimal_tier == 'CCC':
            recommendation += """
- Higher carbon price compensates for higher costs
- Regulatory compliance benefits
- Suitable for medium-large scale projects
- More stable long-term pricing
"""
        else:  # PGC
            recommendation += """
- Highest revenue due to social co-benefits premium
- Water access improvement recognized
- Premium market values sustainability
- Best for integrated water-energy projects
"""

        return recommendation

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
            price_escalation: Annual price increase (3% default)

        Returns:
            20-year revenue projection
        """

        years = 20
        annual_revenues = []

        for year in range(years):
            # Escalate price
            escalated_price = self.tiers[tier].price_per_ton * ((1 + price_escalation) ** year)

            # Temporary tier with escalated price
            temp_tier = self.tiers[tier]
            original_price = temp_tier.price_per_ton
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

        df_revenues = pd.DataFrame(annual_revenues)

        # Calculate NPV
        discount_rate = 0.08  # 8% discount rate
        npv = sum(
            row['net_revenue'] / ((1 + discount_rate) ** (row['year'] - 1))
            for _, row in df_revenues.iterrows()
        )

        return {
            'annual_revenues_df': df_revenues,
            'total_nominal': df_revenues['net_revenue'].sum(),
            'npv_at_8pct': npv,
            'average_annual': df_revenues['net_revenue'].mean(),
            'final_year_revenue': df_revenues.iloc[-1]['net_revenue']
        }

    def get_emission_factor(self, source: str) -> float:
        """Get emission factor for a source"""
        return self.baseline_emissions.get(source, 0)


# Example usage and testing
if __name__ == "__main__":
    # Initialize carbon market model
    carbon_market = CarbonMarketModel()

    print("="*80)
    print("THREE-TIER CARBON MARKET MODEL")
    print("="*80)

    # Example: 5000 MWh annual production
    annual_energy = 5_000_000  # kWh (5 GWh)
    annual_water = 500_000  # m³

    # Calculate avoided emissions
    co2_energy = carbon_market.calculate_avoided_emissions(
        annual_energy,
        'diesel_generator'
    )

    co2_water = carbon_market.calculate_water_carbon_benefit(
        annual_water,
        'diesel_water_pump'
    )

    total_co2 = co2_energy + co2_water

    print(f"\nANNUAL EMISSIONS AVOIDED:")
    print(f"  From energy: {co2_energy:,.0f} tons CO2")
    print(f"  From water:  {co2_water:,.0f} tons CO2")
    print(f"  TOTAL:       {total_co2:,.0f} tons CO2")

    # Optimize tier selection
    print("\n" + "="*80)
    print("CARBON MARKET TIER OPTIMIZATION")
    print("="*80)

    optimization = carbon_market.optimize_tier_selection(
        total_co2,
        water_access_improvement=True
    )

    print(f"\nOptimal Tier: {optimization['optimal_tier']}")
    print(f"\nCOMPARISON TABLE:")
    print(optimization['comparison_table'].to_string(index=False))

    print(optimization['recommendation'])

    # 20-year projection
    print("\n" + "="*80)
    print("20-YEAR CARBON REVENUE PROJECTION")
    print("="*80)

    projection = carbon_market.calculate_20year_carbon_revenue(
        total_co2,
        optimization['optimal_tier'],
        water_benefit=True,
        price_escalation=0.03
    )

    print(f"\nTotal Nominal Revenue (20 years): ${projection['total_nominal']:,.0f}")
    print(f"NPV at 8%: ${projection['npv_at_8pct']:,.0f}")
    print(f"Average Annual Revenue: ${projection['average_annual']:,.0f}")

    print("\nFirst 5 years:")
    print(projection['annual_revenues_df'].head().to_string(index=False))
