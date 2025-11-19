"""
Data Preparation Script

Generates time series data for wind, dust, temperature, and water demand
for the Saravan Wind-Water-Energy-Carbon Nexus model.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data_generator import SaravanDataGenerator
from config import config


def prepare_data(hours=None, start_date=None, seed=None):
    """
    Generate complete dataset for optimization

    Args:
        hours: Number of hours to simulate (default from config)
        start_date: Start date (default from config)
        seed: Random seed (default from config)

    Returns:
        Complete dataset dictionary
    """

    # Use config defaults if not specified
    if hours is None:
        from pandas import date_range
        snapshots = date_range(
            start=config.SNAPSHOTS_START,
            end=config.SNAPSHOTS_END,
            freq=config.SNAPSHOTS_FREQ
        )
        hours = len(snapshots)

    if start_date is None:
        start_date = config.SNAPSHOTS_START

    if seed is None:
        seed = config.RANDOM_SEED

    print("="*70)
    print("DATA PREPARATION")
    print("="*70)
    print(f"Hours: {hours} ({hours/24:.1f} days)")
    print(f"Start date: {start_date}")
    print(f"Random seed: {seed}")

    # Generate data
    data_generator = SaravanDataGenerator(random_seed=seed)
    dataset = data_generator.generate_complete_dataset(
        hours=hours,
        start_date=start_date
    )

    # Print statistics
    print("\nData Statistics:")
    print(f"  Wind speed: {dataset['wind']['wind_speed_ms'].mean():.2f} m/s (avg)")
    print(f"  Dust PM10: {dataset['dust']['pm10_ugm3'].mean():.0f} μg/m³ (avg)")
    print(f"  Temperature: {dataset['temperature']['temperature_c'].mean():.1f}°C (avg)")
    print(f"  Water demand: {dataset['water_demand']['total_m3h'].sum():,.0f} m³ (total)")

    # Export if requested
    if config.EXPORT_RESULTS_CSV:
        data_dir = config.DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)
        data_generator.export_to_csv(dataset, str(data_dir))
        print(f"\n✓ Data exported to {data_dir}")

    return dataset


if __name__ == "__main__":
    dataset = prepare_data()
    print("\n✅ Data preparation complete!")
