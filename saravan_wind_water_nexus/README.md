# Saravan Wind-Water-Energy-Carbon Nexus Model

PyPSA-based multi-sector optimization model for integrated wind energy, water treatment, thermal systems, and carbon markets in Saravan, Iran.

## Overview

This model optimizes the operation of an integrated wind-water-energy-carbon nexus system including:
- **Wind Energy**: HAWT and Bladeless turbines
- **Energy Storage**: Battery system
- **Water System**: Groundwater pumping, treatment, and storage
- **Thermal Systems**: CHP and gas boiler (dual-fuel: natural gas + biogas)
- **Biogas Production**: Anaerobic digestion of wastewater sludge
- **Carbon Systems**: Carbon capture and utilization (CCU)
- **Carbon Markets**: Revenue from verified carbon credits

## Project Structure

Following PyPSA-standard organization (similar to PyPSA-Eur, PyPSA-Earth):

```
saravan_wind_water_nexus/
├── config.py                    # Central configuration file
├── main.py                      # Main entry point
├── models/                      # Component models
│   ├── wind_turbines.py        # HAWT, Bladeless models
│   ├── water_treatment.py      # Water system model
│   ├── thermal_systems.py      # CHP, Boiler models
│   ├── sludge_biogas.py        # Sludge, biogas, CCU models
│   └── carbon_market.py        # Carbon pricing and revenue
├── scripts/                     # Workflow scripts
│   ├── prepare_data.py         # Data generation
│   ├── build_network.py        # Network construction
│   ├── solve_network.py        # Optimization
│   └── run_analysis.py         # Complete workflow
├── plotting/                    # Visualization modules
│   ├── nexus_plots.py          # Standard plots
│   ├── carbon_plots.py         # Carbon visualizations
│   └── publication_figures.py  # 10 publication figures
├── data/                        # Generated time series data
├── results/                     # Optimization results
└── resources/                   # Static resources
```

## Quick Start

```bash
# Run complete analysis
python main.py

# Or run individual steps
python scripts/prepare_data.py
python scripts/build_network.py
python scripts/solve_network.py
```

## Configuration

All model parameters in `config.py`:

```python
TURBINE_MIX = {'HAWT': 5, 'Bladeless': 15}
BATTERY_CAPACITY_KWH = 1000
SNAPSHOTS_START = "2025-01-01"
SNAPSHOTS_END = "2025-01-08"  # 7 days
```

## Scientific Validation

Designed for transparent review:
1. All parameters centralized in `config.py`
2. All assumptions documented in model files
3. All calculations traceable through modular code
4. All results exported for independent verification

## Key Features

- PyPSA-based optimization
- Multi-sector coupling (energy, water, heat, carbon)
- Dual-fuel systems (natural gas + biogas)
- Carbon market revenue analysis
- Publication-ready figures (300 DPI)
- Fully reproducible
