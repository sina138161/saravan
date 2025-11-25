"""
Economic calculation utilities for all technologies
"""

from typing import Dict, List, Tuple


class EconomicCalculator:
    """
    Shared economic calculation methods for all technologies
    """

    @staticmethod
    def calculate_npv(capex: float, annual_cash_flows: List[float],
                     discount_rate: float = 0.08) -> float:
        """
        Calculate Net Present Value with varying annual cash flows

        Args:
            capex: Initial capital expenditure ($)
            annual_cash_flows: List of annual net cash flows ($/year)
            discount_rate: Discount rate (default 8%)

        Returns:
            NPV in dollars
        """
        pv_flows = sum(
            cf / ((1 + discount_rate) ** (year + 1))
            for year, cf in enumerate(annual_cash_flows)
        )

        return pv_flows - capex

    @staticmethod
    def calculate_irr(capex: float, annual_cash_flows: List[float],
                     guess: float = 0.1) -> float:
        """
        Calculate Internal Rate of Return using Newton-Raphson method

        Args:
            capex: Initial capital expenditure ($)
            annual_cash_flows: List of annual net cash flows ($/year)
            guess: Initial guess for IRR (default 10%)

        Returns:
            IRR as decimal (e.g., 0.15 = 15%)
        """
        def npv_at_rate(rate):
            return sum(
                cf / ((1 + rate) ** (year + 1))
                for year, cf in enumerate(annual_cash_flows)
            ) - capex

        def npv_derivative(rate):
            return sum(
                -cf * (year + 1) / ((1 + rate) ** (year + 2))
                for year, cf in enumerate(annual_cash_flows)
            )

        # Newton-Raphson iteration
        rate = guess
        for _ in range(100):  # Max iterations
            npv = npv_at_rate(rate)
            if abs(npv) < 1e-6:  # Convergence threshold
                return rate

            derivative = npv_derivative(rate)
            if abs(derivative) < 1e-10:
                break

            rate = rate - npv / derivative

            # Keep rate in reasonable bounds
            if rate < -0.99:
                rate = -0.99
            if rate > 10:
                rate = 10

        return rate

    @staticmethod
    def calculate_lcoe(capex: float, annual_opex: float, annual_energy: float,
                      lifetime: int, discount_rate: float = 0.08) -> float:
        """
        Calculate Levelized Cost of Energy

        Args:
            capex: Capital expenditure ($)
            annual_opex: Annual operating expenditure ($/year)
            annual_energy: Annual energy production (kWh/year)
            lifetime: Project lifetime (years)
            discount_rate: Discount rate (default 8%)

        Returns:
            LCOE in $/kWh
        """
        # Present value of costs
        pv_opex = sum(
            annual_opex / ((1 + discount_rate) ** year)
            for year in range(1, lifetime + 1)
        )
        pv_costs = capex + pv_opex

        # Present value of energy
        pv_energy = sum(
            annual_energy / ((1 + discount_rate) ** year)
            for year in range(1, lifetime + 1)
        )

        if pv_energy > 0:
            return pv_costs / pv_energy
        return float('inf')

    @staticmethod
    def calculate_benefit_cost_ratio(capex: float, annual_benefits: float,
                                    annual_costs: float, lifetime: int,
                                    discount_rate: float = 0.08) -> float:
        """
        Calculate Benefit-Cost Ratio (BCR)

        Args:
            capex: Initial capital expenditure ($)
            annual_benefits: Annual benefits ($/year)
            annual_costs: Annual costs ($/year)
            lifetime: Project lifetime (years)
            discount_rate: Discount rate (default 8%)

        Returns:
            BCR (ratio > 1 means benefits exceed costs)
        """
        # Present value of benefits
        pv_benefits = sum(
            annual_benefits / ((1 + discount_rate) ** year)
            for year in range(1, lifetime + 1)
        )

        # Present value of costs
        pv_costs = capex + sum(
            annual_costs / ((1 + discount_rate) ** year)
            for year in range(1, lifetime + 1)
        )

        if pv_costs > 0:
            return pv_benefits / pv_costs
        return 0.0

    @staticmethod
    def annualize_capex(capex: float, lifetime: int,
                       discount_rate: float = 0.08) -> float:
        """
        Convert CAPEX to equivalent annual cost using Capital Recovery Factor

        Args:
            capex: Capital expenditure ($)
            lifetime: Project lifetime (years)
            discount_rate: Discount rate (default 8%)

        Returns:
            Annual equivalent cost ($/year)
        """
        if discount_rate == 0:
            return capex / lifetime

        # Capital Recovery Factor
        crf = (discount_rate * (1 + discount_rate) ** lifetime) / \
              ((1 + discount_rate) ** lifetime - 1)

        return capex * crf

    @staticmethod
    def calculate_sensitivity_analysis(base_npv: float,
                                      parameter_name: str,
                                      base_value: float,
                                      variation_pct: float = 0.20) -> Dict:
        """
        Perform simple sensitivity analysis on a parameter

        Args:
            base_npv: Base case NPV ($)
            parameter_name: Name of parameter being varied
            base_value: Base value of parameter
            variation_pct: Variation percentage (default ±20%)

        Returns:
            Dictionary with sensitivity results
        """
        variations = [-variation_pct, 0, variation_pct]

        results = {
            'parameter': parameter_name,
            'base_value': base_value,
            'base_npv': base_npv,
            'variations': []
        }

        for var in variations:
            new_value = base_value * (1 + var)
            results['variations'].append({
                'change_pct': var * 100,
                'new_value': new_value,
                'note': 'Implement NPV recalculation in specific technology'
            })

        return results

    @staticmethod
    def calculate_depreciation(capex: float, lifetime: int,
                              method: str = 'straight_line') -> List[float]:
        """
        Calculate depreciation schedule

        Args:
            capex: Capital expenditure ($)
            lifetime: Asset lifetime (years)
            method: Depreciation method ('straight_line' or 'declining_balance')

        Returns:
            List of annual depreciation amounts
        """
        if method == 'straight_line':
            annual_depreciation = capex / lifetime
            return [annual_depreciation] * lifetime

        elif method == 'declining_balance':
            rate = 2.0 / lifetime  # Double declining balance
            depreciation = []
            book_value = capex

            for year in range(lifetime):
                annual_dep = book_value * rate
                # Don't depreciate below zero
                if book_value - annual_dep < 0:
                    annual_dep = book_value
                depreciation.append(annual_dep)
                book_value -= annual_dep

            return depreciation

        else:
            raise ValueError(f"Unknown depreciation method: {method}")

    @staticmethod
    def calculate_loan_payment(principal: float, annual_rate: float,
                              years: int) -> Tuple[float, List[Dict]]:
        """
        Calculate loan payment and amortization schedule

        Args:
            principal: Loan amount ($)
            annual_rate: Annual interest rate (decimal, e.g., 0.05 = 5%)
            years: Loan term (years)

        Returns:
            Tuple of (annual_payment, amortization_schedule)
        """
        if annual_rate == 0:
            annual_payment = principal / years
        else:
            # Annual payment using amortization formula
            annual_payment = principal * \
                           (annual_rate * (1 + annual_rate) ** years) / \
                           ((1 + annual_rate) ** years - 1)

        # Generate amortization schedule
        schedule = []
        balance = principal

        for year in range(1, years + 1):
            interest = balance * annual_rate
            principal_payment = annual_payment - interest
            balance -= principal_payment

            schedule.append({
                'year': year,
                'payment': annual_payment,
                'principal': principal_payment,
                'interest': interest,
                'balance': max(0, balance)  # Avoid negative due to rounding
            })

        return annual_payment, schedule
