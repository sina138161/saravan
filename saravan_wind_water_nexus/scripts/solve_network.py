"""
Network Optimization Script

Solves the PyPSA network optimization problem to find optimal dispatch
of all components (turbines, battery, water pumps, CHP, boiler, etc.).
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import config


def solve_network(network_builder, solver=None, solver_options=None):
    """
    Solve PyPSA network optimization

    Args:
        network_builder: WindWaterNetworkBuilder instance
        solver: Solver name (default from config)
        solver_options: Solver options dict (default from config)

    Returns:
        Optimization results dictionary
    """

    # Use config defaults if not specified
    if solver is None:
        solver = config.SOLVER

    if solver_options is None:
        solver_options = config.SOLVER_OPTIONS

    print("="*70)
    print("OPTIMIZATION")
    print("="*70)
    print(f"Solver: {solver}")
    print(f"Options: {solver_options}")

    # Solve
    results = network_builder.optimize(solver=solver)

    # Print results summary
    print("\nOptimization Results:")
    print(f"  Status: {results.get('status', 'Unknown')}")

    if 'objective' in results:
        print(f"  Objective value: ${results['objective']:,.2f}")

    return results


if __name__ == "__main__":
    from prepare_data import prepare_data
    from build_network import build_network

    # Prepare data
    dataset = prepare_data()

    # Build network
    network, builder = build_network(dataset)

    # Solve
    results = solve_network(builder)

    print("\n✅ Optimization complete!")
