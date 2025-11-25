"""
Base class for all technology models
Provides common interface and shared functionality
"""

from typing import Dict, Any
from abc import ABC, abstractmethod


class TechnologyBase(ABC):
    """
    Abstract base class for all technology models

    All technology models should inherit from this class to ensure
    consistent interface and shared economic calculations.
    """

    def __init__(self):
        """Initialize technology specifications"""
        self.specs = self._define_specs()
        self._validate_specs()

    @abstractmethod
    def _define_specs(self) -> Dict[str, Any]:
        """
        Define technology specifications

        Must be implemented by child classes

        Returns:
            Dictionary containing technology specifications
        """
        raise NotImplementedError("Must be implemented by child class")

    def _validate_specs(self):
        """
        Validate that required specifications are present

        Ensures minimum required fields exist in specs
        """
        required_fields = ['capex', 'opex', 'lifetime']

        for field in required_fields:
            if field not in self.specs:
                raise ValueError(
                    f"Missing required specification: '{field}' in {self.__class__.__name__}"
                )

    def get_specs(self) -> Dict[str, Any]:
        """
        Get technology specifications

        Returns:
            Dictionary containing all specifications
        """
        return self.specs

    def calculate_total_capex(self, capacity: float) -> float:
        """
        Calculate total capital expenditure

        Args:
            capacity: Technology capacity (units depend on technology)

        Returns:
            Total CAPEX in dollars
        """
        if 'capex' in self.specs:
            return capacity * self.specs['capex']
        return 0.0

    def calculate_annual_opex(self, annual_output: float) -> float:
        """
        Calculate annual operating expenditure

        Args:
            annual_output: Annual output (units depend on technology)

        Returns:
            Annual OPEX in dollars
        """
        if 'opex' in self.specs:
            return annual_output * self.specs['opex']
        return 0.0

    def calculate_levelized_cost(self, capex: float, annual_opex: float,
                                 annual_output: float,
                                 discount_rate: float = 0.08) -> float:
        """
        Calculate levelized cost of technology (LCOE or equivalent)

        Args:
            capex: Capital expenditure ($)
            annual_opex: Annual operating expenditure ($/year)
            annual_output: Annual output (kWh or other units)
            discount_rate: Discount rate (default 8%)

        Returns:
            Levelized cost ($/unit)
        """
        lifetime = self.specs.get('lifetime', 20)

        # Present value of OPEX over lifetime
        pv_opex = sum(
            annual_opex / ((1 + discount_rate) ** year)
            for year in range(1, lifetime + 1)
        )

        # Present value of output over lifetime
        pv_output = sum(
            annual_output / ((1 + discount_rate) ** year)
            for year in range(1, lifetime + 1)
        )

        # Levelized cost
        if pv_output > 0:
            return (capex + pv_opex) / pv_output
        return 0.0

    def calculate_npv(self, capex: float, annual_revenue: float,
                     annual_opex: float, discount_rate: float = 0.08) -> float:
        """
        Calculate Net Present Value

        Args:
            capex: Capital expenditure ($)
            annual_revenue: Annual revenue ($/year)
            annual_opex: Annual operating expenditure ($/year)
            discount_rate: Discount rate (default 8%)

        Returns:
            NPV in dollars
        """
        lifetime = self.specs.get('lifetime', 20)

        # Annual net cash flow
        annual_net_flow = annual_revenue - annual_opex

        # Present value of cash flows
        pv_flows = sum(
            annual_net_flow / ((1 + discount_rate) ** year)
            for year in range(1, lifetime + 1)
        )

        # NPV = PV of cash flows - initial investment
        npv = pv_flows - capex

        return npv

    def calculate_payback_period(self, capex: float, annual_revenue: float,
                                annual_opex: float) -> float:
        """
        Calculate simple payback period

        Args:
            capex: Capital expenditure ($)
            annual_revenue: Annual revenue ($/year)
            annual_opex: Annual operating expenditure ($/year)

        Returns:
            Payback period in years
        """
        annual_net_flow = annual_revenue - annual_opex

        if annual_net_flow <= 0:
            return float('inf')  # Never pays back

        return capex / annual_net_flow

    def __repr__(self) -> str:
        """String representation of technology"""
        return f"{self.__class__.__name__}()"
