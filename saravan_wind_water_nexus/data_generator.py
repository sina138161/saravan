"""
Saravan Data Generator
Generates realistic time series for wind, dust, water demand, and temperature
Based on Saravan climate and field measurements
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


class SaravanDataGenerator:
    """
    Generate realistic time series data for Saravan, Iran

    Location: Saravan, Sistan and Baluchestan Province
    Coordinates: ~27°N, ~62°E
    Climate: Hot desert (BWh), extreme dust storms
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize data generator

        Args:
            random_seed: Random seed for reproducibility
        """
        np.random.seed(random_seed)
        self.saravan_params = self._define_saravan_parameters()

    def _define_saravan_parameters(self) -> Dict:
        """
        Define Saravan-specific climate parameters

        Based on:
        - NASA POWER meteorological data
        - Iran Meteorological Organization records
        - Field measurements from Sistan-Baluchestan
        """

        params = {
            'wind': {
                'annual_mean': 7.5,  # m/s (Saravan has good wind resources)
                'weibull_k': 2.1,    # Shape parameter
                'weibull_lambda': 8.5,  # Scale parameter
                'seasonal_variation': {
                    'spring': 1.3,   # 30% higher (120-day wind season)
                    'summer': 1.4,   # 40% higher (famous 120-day wind)
                    'fall': 0.9,     # 10% lower
                    'winter': 0.8    # 20% lower
                },
                'diurnal_peak_hour': 14,  # Peak at 2 PM
                'diurnal_amplitude': 0.3   # 30% variation
            },

            'dust': {
                'baseline_pm10': 80,  # μg/m³ (background level)
                'storm_pm10': 300,    # μg/m³ (during dust storms)
                'storm_frequency': 0.15,  # 15% of days have storms
                'seasonal_variation': {
                    'spring': 2.0,   # Peak dust season
                    'summer': 2.5,   # Worst dust (120-day wind carries dust)
                    'fall': 1.2,
                    'winter': 0.8    # Lowest dust
                },
                'storm_duration_hours': (6, 24),  # Storm lasts 6-24 hours
                'correlation_with_wind': 0.6  # Moderate correlation
            },

            'temperature': {
                'annual_mean': 28,  # °C
                'summer_max': 45,   # °C (extreme heat)
                'winter_min': 10,   # °C
                'diurnal_range': 15,  # °C (desert: large day-night variation)
                'peak_hour': 15     # Hottest at 3 PM
            },

            'water_demand': {
                'agricultural': {
                    'annual_total': 400000,  # m³/year (dominant sector)
                    'peak_month': 7,         # July (irrigation peak)
                    'seasonal_factor': {
                        'spring': 1.2,
                        'summer': 2.0,  # Double demand (irrigation)
                        'fall': 0.8,
                        'winter': 0.4   # Minimal irrigation
                    },
                    'daily_pattern': 'daylight',  # Irrigate during day
                },
                'urban': {
                    'annual_total': 80000,   # m³/year
                    'peak_month': 7,         # July (cooling + drinking)
                    'seasonal_factor': {
                        'spring': 1.0,
                        'summer': 1.4,
                        'fall': 1.0,
                        'winter': 0.9
                    },
                    'daily_pattern': 'two_peaks',  # Morning + evening
                }
                # NOTE: No industrial sector - Saravan has no industrial water demand
            },

            'electricity_demand': {
                'urban': {
                    'annual_total_kwh': 500000,  # Annual urban electricity demand
                    'seasonal_factor': {
                        'spring': 1.0,
                        'summer': 1.5,  # Higher due to cooling
                        'fall': 1.0,
                        'winter': 1.2   # Heating
                    },
                    'daily_pattern': 'two_peaks',  # Morning 8am, Evening 7pm
                },
                # NOTE: No industrial sector - Saravan has no industrial electricity demand
                'pumping': {
                    'energy_per_m3': 1.2,  # kWh per m³ (well pumping)
                    'dependent_on': 'water_demand'  # Follows water demand pattern
                },
                'treatment': {
                    'primary_kwh_per_m3': 0.15,  # Primary water treatment
                    'secondary_kwh_per_m3': 0.50,  # Secondary water treatment
                    'wastewater_primary_kwh_per_m3': 0.25,  # Wastewater primary treatment
                    'wastewater_secondary_kwh_per_m3': 0.60,  # Wastewater secondary treatment
                }
            }
        }

        return params

    def generate_wind_data(self, hours: int = 8760,
                          start_date: str = "2025-01-01") -> pd.DataFrame:
        """
        Generate hourly wind speed data using Weibull distribution

        Args:
            hours: Number of hours
            start_date: Start date

        Returns:
            DataFrame with timestamps and wind speeds
        """

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')

        # Base wind speed from Weibull distribution
        k = self.saravan_params['wind']['weibull_k']
        lam = self.saravan_params['wind']['weibull_lambda']
        base_wind = np.random.weibull(k, hours) * lam

        # Apply seasonal variation
        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'wind') for ts in timestamps
        ])
        wind_seasonal = base_wind * seasonal_factor

        # Apply diurnal variation
        diurnal_factor = np.array([
            self._get_diurnal_factor(ts.hour,
                                    self.saravan_params['wind']['diurnal_peak_hour'],
                                    self.saravan_params['wind']['diurnal_amplitude'])
            for ts in timestamps
        ])
        wind_hourly = wind_seasonal * diurnal_factor

        # Ensure physically reasonable values
        wind_hourly = np.clip(wind_hourly, 0, 30)  # 0-30 m/s

        df = pd.DataFrame({
            'timestamp': timestamps,
            'wind_speed_ms': wind_hourly
        })

        return df

    def generate_dust_data(self, hours: int = 8760,
                          start_date: str = "2025-01-01",
                          wind_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Generate hourly PM10 dust concentration data

        Args:
            hours: Number of hours
            start_date: Start date
            wind_data: Optional wind data for correlation

        Returns:
            DataFrame with timestamps and PM10 concentrations
        """

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')

        # Baseline dust concentration
        baseline = self.saravan_params['dust']['baseline_pm10']

        # Seasonal variation
        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'dust') for ts in timestamps
        ])

        # Base dust with seasonal variation
        dust = baseline * seasonal_factor

        # Add dust storms (random events)
        storm_prob = self.saravan_params['dust']['storm_frequency'] / 24  # Per hour
        for i in range(hours):
            if np.random.random() < storm_prob:
                # Dust storm starts
                duration = np.random.randint(
                    self.saravan_params['dust']['storm_duration_hours'][0],
                    self.saravan_params['dust']['storm_duration_hours'][1]
                )
                intensity = self.saravan_params['dust']['storm_pm10']

                # Apply storm for duration
                end_hour = min(i + duration, hours)
                dust[i:end_hour] = intensity * seasonal_factor[i:end_hour]

        # Correlate with wind (higher wind → more dust)
        if wind_data is not None:
            wind_speeds = wind_data['wind_speed_ms'].values[:hours]
            wind_factor = 1 + 0.3 * (wind_speeds - 7.5) / 7.5  # ±30% based on wind
            wind_factor = np.clip(wind_factor, 0.7, 1.5)
            dust = dust * wind_factor

        # Add noise
        noise = np.random.lognormal(0, 0.2, hours)
        dust = dust * noise

        # Ensure reasonable range
        dust = np.clip(dust, 20, 500)  # 20-500 μg/m³

        df = pd.DataFrame({
            'timestamp': timestamps,
            'pm10_ugm3': dust
        })

        return df

    def generate_temperature_data(self, hours: int = 8760,
                                  start_date: str = "2025-01-01") -> pd.DataFrame:
        """
        Generate hourly temperature data

        Args:
            hours: Number of hours
            start_date: Start date

        Returns:
            DataFrame with timestamps and temperatures
        """

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')

        # Seasonal temperature (annual cycle)
        day_of_year = np.array([ts.timetuple().tm_yday for ts in timestamps])
        seasonal_temp = (
            self.saravan_params['temperature']['annual_mean'] +
            17 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # Peak in July
        )

        # Diurnal variation
        hour_of_day = np.array([ts.hour for ts in timestamps])
        diurnal_amplitude = self.saravan_params['temperature']['diurnal_range'] / 2
        diurnal_temp = diurnal_amplitude * np.sin(
            2 * np.pi * (hour_of_day - 6) / 24  # Peak at 3 PM
        )

        temperature = seasonal_temp + diurnal_temp

        # Add small random noise
        noise = np.random.normal(0, 1, hours)
        temperature = temperature + noise

        # Ensure reasonable range
        temperature = np.clip(temperature, 5, 50)

        df = pd.DataFrame({
            'timestamp': timestamps,
            'temperature_c': temperature
        })

        return df

    def generate_water_demand(self, hours: int = 8760,
                             start_date: str = "2025-01-01") -> pd.DataFrame:
        """
        Generate hourly water demand for all sectors

        Args:
            hours: Number of hours
            start_date: Start date

        Returns:
            DataFrame with timestamps and water demands by sector
        """

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')

        demands = {}

        # Only agricultural and urban sectors (no industrial in Saravan)
        for sector in ['agricultural', 'urban']:
            sector_params = self.saravan_params['water_demand'][sector]

            # Annual average hourly demand
            annual_total = sector_params['annual_total']
            avg_hourly = annual_total / 8760

            # Seasonal variation
            seasonal_factor = np.array([
                self._get_seasonal_factor(ts, sector, resource='water')
                for ts in timestamps
            ])

            # Daily pattern
            if sector_params['daily_pattern'] == 'daylight':
                # Agricultural: irrigate 6 AM - 6 PM
                daily_factor = np.array([
                    1.5 if 6 <= ts.hour <= 18 else 0.2
                    for ts in timestamps
                ])
            elif sector_params['daily_pattern'] == 'two_peaks':
                # Urban: peaks at 7 AM and 7 PM
                daily_factor = np.array([
                    1.5 if ts.hour in [7, 19] else
                    1.2 if 6 <= ts.hour <= 9 or 18 <= ts.hour <= 21 else
                    0.7
                    for ts in timestamps
                ])
            else:  # constant
                daily_factor = np.ones(hours)

            # Combine factors
            demand = avg_hourly * seasonal_factor * daily_factor

            # Normalize to maintain period total (scaled from annual)
            period_total = annual_total * (hours / 8760)
            demand = demand * (period_total / demand.sum())

            # Add small noise
            noise = np.random.lognormal(0, 0.1, hours)
            demand = demand * noise

            demands[sector] = demand

        # Calculate total (only agricultural + urban)
        demands['total'] = sum(demands.values())

        df = pd.DataFrame({
            'timestamp': timestamps,
            'agricultural_m3h': demands['agricultural'],
            'urban_m3h': demands['urban'],
            'total_m3h': demands['total']
        })

        return df

    def generate_electricity_demand(self, hours: int = 8760,
                                    start_date: str = "2025-01-01",
                                    water_demand_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Generate hourly electricity demand for all sectors

        Args:
            hours: Number of hours
            start_date: Start date
            water_demand_df: Water demand dataframe for calculating pumping and treatment loads

        Returns:
            DataFrame with timestamps and electricity demands by sector
        """

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')
        demands = {}

        # Urban electricity demand
        urban_params = self.saravan_params['electricity_demand']['urban']
        annual_total = urban_params['annual_total_kwh']
        avg_hourly = annual_total / 8760

        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'urban', resource='electricity')
            for ts in timestamps
        ])

        # Daily pattern: two peaks (8am and 7pm)
        daily_factor = np.array([
            1.8 if ts.hour in [8, 19] else
            1.4 if 6 <= ts.hour <= 10 or 17 <= ts.hour <= 22 else
            0.6
            for ts in timestamps
        ])

        urban_demand = avg_hourly * seasonal_factor * daily_factor
        period_total = annual_total * (hours / 8760)
        urban_demand = urban_demand * (period_total / urban_demand.sum())
        noise = np.random.lognormal(0, 0.08, hours)
        demands['urban'] = urban_demand * noise

        # NOTE: No industrial electricity demand - Saravan has no industrial sector

        # Pumping electricity demand (dependent on water demand)
        if water_demand_df is not None:
            water_total = water_demand_df['total_m3h'].values[:hours]
            pumping_params = self.saravan_params['electricity_demand']['pumping']
            demands['pumping'] = water_total * pumping_params['energy_per_m3']
        else:
            demands['pumping'] = np.zeros(hours)

        # Treatment electricity demand (dependent on water demand)
        if water_demand_df is not None:
            water_agri = water_demand_df['agricultural_m3h'].values[:hours]
            water_urban = water_demand_df['urban_m3h'].values[:hours]

            treatment_params = self.saravan_params['electricity_demand']['treatment']

            # Primary treatment for agricultural water
            primary_treatment = water_agri * treatment_params['primary_kwh_per_m3']

            # Secondary treatment for urban water
            secondary_treatment = water_urban * treatment_params['secondary_kwh_per_m3']

            # Wastewater treatment (80% of urban water becomes wastewater)
            wastewater_volume = water_urban * 0.80
            wastewater_treatment_primary = wastewater_volume * treatment_params['wastewater_primary_kwh_per_m3']

            demands['treatment'] = primary_treatment + secondary_treatment + wastewater_treatment_primary
        else:
            demands['treatment'] = np.zeros(hours)

        # Total demand (only urban + pumping + treatment, no industrial)
        demands['total'] = demands['urban'] + demands['pumping'] + demands['treatment']

        df = pd.DataFrame({
            'timestamp': timestamps,
            'urban_kwh': demands['urban'],
            'pumping_kwh': demands['pumping'],
            'treatment_kwh': demands['treatment'],
            'total_kwh': demands['total']
        })

        return df

    def generate_complete_dataset(self, hours: int = 8760,
                                 start_date: str = "2025-01-01") -> Dict[str, pd.DataFrame]:
        """
        Generate complete dataset with all variables

        Args:
            hours: Number of hours (default: 8760 = 1 year)
            start_date: Start date

        Returns:
            Dictionary of DataFrames for each variable
        """

        print(f"\n{'='*70}")
        print(f"GENERATING SARAVAN DATA")
        print(f"{'='*70}")
        print(f"Duration: {hours} hours ({hours/24:.0f} days)")
        print(f"Start date: {start_date}")

        # Generate wind data
        print("\n🌪️  Generating wind data...")
        wind_df = self.generate_wind_data(hours, start_date)
        print(f"   Mean wind speed: {wind_df['wind_speed_ms'].mean():.2f} m/s")
        print(f"   Max wind speed: {wind_df['wind_speed_ms'].max():.2f} m/s")

        # Generate dust data (correlated with wind)
        print("\n🏜️  Generating dust data...")
        dust_df = self.generate_dust_data(hours, start_date, wind_df)
        print(f"   Mean PM10: {dust_df['pm10_ugm3'].mean():.0f} μg/m³")
        print(f"   Max PM10: {dust_df['pm10_ugm3'].max():.0f} μg/m³")
        n_storms = np.sum(dust_df['pm10_ugm3'] > 200)
        print(f"   Hours with storms (PM10>200): {n_storms} ({n_storms/hours*100:.1f}%)")

        # Generate temperature data
        print("\n🌡️  Generating temperature data...")
        temp_df = self.generate_temperature_data(hours, start_date)
        print(f"   Mean temperature: {temp_df['temperature_c'].mean():.1f}°C")
        print(f"   Max temperature: {temp_df['temperature_c'].max():.1f}°C")
        print(f"   Min temperature: {temp_df['temperature_c'].min():.1f}°C")

        # Generate water demand
        print("\n💧 Generating water demand...")
        water_df = self.generate_water_demand(hours, start_date)
        print(f"   Annual agricultural: {water_df['agricultural_m3h'].sum():,.0f} m³")
        print(f"   Annual urban: {water_df['urban_m3h'].sum():,.0f} m³")
        print(f"   TOTAL annual: {water_df['total_m3h'].sum():,.0f} m³ (no industrial)")

        # Generate electricity demand
        print("\n⚡ Generating electricity demand...")
        elec_df = self.generate_electricity_demand(hours, start_date, water_df)
        print(f"   Annual urban: {elec_df['urban_kwh'].sum():,.0f} kWh")
        print(f"   Annual pumping: {elec_df['pumping_kwh'].sum():,.0f} kWh")
        print(f"   Annual treatment: {elec_df['treatment_kwh'].sum():,.0f} kWh")
        print(f"   TOTAL annual: {elec_df['total_kwh'].sum():,.0f} kWh (no industrial)")

        dataset = {
            'wind': wind_df,
            'dust': dust_df,
            'temperature': temp_df,
            'water_demand': water_df,
            'electricity_demand': elec_df
        }

        print(f"\n✅ Data generation complete!")

        return dataset

    def _get_seasonal_factor(self, timestamp: pd.Timestamp,
                            variable: str,
                            resource: str = None) -> float:
        """Get seasonal multiplication factor"""

        month = timestamp.month

        # Determine season
        if month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        elif month in [9, 10, 11]:
            season = 'fall'
        else:
            season = 'winter'

        # Get factor
        if resource == 'water':
            # Water demand has sector-specific seasonality
            return self.saravan_params['water_demand'][variable]['seasonal_factor'][season]
        elif resource == 'electricity':
            # Electricity demand has sector-specific seasonality
            return self.saravan_params['electricity_demand'][variable]['seasonal_factor'][season]
        else:
            # Wind and dust
            return self.saravan_params[variable]['seasonal_variation'][season]

    def _get_diurnal_factor(self, hour: int, peak_hour: int,
                           amplitude: float) -> float:
        """Get diurnal (daily) multiplication factor"""

        # Sinusoidal variation centered on peak hour
        factor = 1 + amplitude * np.sin(2 * np.pi * (hour - peak_hour + 6) / 24)

        return max(0.5, factor)  # Ensure minimum 50%

    def export_to_csv(self, dataset: Dict[str, pd.DataFrame],
                     output_dir: str = 'data') -> None:
        """
        Export generated data to CSV files

        Args:
            dataset: Dictionary of DataFrames
            output_dir: Output directory
        """

        import os
        os.makedirs(output_dir, exist_ok=True)

        for name, df in dataset.items():
            filename = f"{output_dir}/saravan_{name}.csv"
            df.to_csv(filename, index=False)
            print(f"   Saved: {filename}")

        print(f"\n✅ Data exported to {output_dir}/")


# Example usage and testing
if __name__ == "__main__":
    # Initialize generator
    generator = SaravanDataGenerator(random_seed=42)

    # Generate 1 year of data
    dataset = generator.generate_complete_dataset(
        hours=8760,
        start_date="2025-01-01"
    )

    # Export to CSV
    print(f"\n{'='*70}")
    print("EXPORTING DATA TO CSV")
    print(f"{'='*70}")
    generator.export_to_csv(dataset, output_dir='data')

    # Show sample data
    print(f"\n{'='*70}")
    print("SAMPLE DATA (first 24 hours)")
    print(f"{'='*70}")

    print("\nWind Speed (m/s):")
    print(dataset['wind']['wind_speed_ms'].head(24).values)

    print("\nPM10 Dust (μg/m³):")
    print(dataset['dust']['pm10_ugm3'].head(24).values)

    print("\nTemperature (°C):")
    print(dataset['temperature']['temperature_c'].head(24).values)

    print("\nWater Demand (m³/h):")
    print(dataset['water_demand'][['agricultural_m3h', 'urban_m3h', 'total_m3h']].head(10))

    # Statistics
    print(f"\n{'='*70}")
    print("ANNUAL STATISTICS")
    print(f"{'='*70}")

    print(f"\nWind:")
    print(f"  Mean: {dataset['wind']['wind_speed_ms'].mean():.2f} m/s")
    print(f"  Std: {dataset['wind']['wind_speed_ms'].std():.2f} m/s")
    print(f"  Hours >5 m/s: {(dataset['wind']['wind_speed_ms'] > 5).sum()} ({(dataset['wind']['wind_speed_ms'] > 5).sum()/8760*100:.1f}%)")
    print(f"  Hours >10 m/s: {(dataset['wind']['wind_speed_ms'] > 10).sum()} ({(dataset['wind']['wind_speed_ms'] > 10).sum()/8760*100:.1f}%)")

    print(f"\nDust:")
    print(f"  Mean PM10: {dataset['dust']['pm10_ugm3'].mean():.0f} μg/m³")
    print(f"  Hours with storm (>200): {(dataset['dust']['pm10_ugm3'] > 200).sum()}")
    print(f"  Hours with severe storm (>300): {(dataset['dust']['pm10_ugm3'] > 300).sum()}")

    print(f"\nWater:")
    print(f"  Total annual demand: {dataset['water_demand']['total_m3h'].sum():,.0f} m³")
    print(f"  Agricultural share: {dataset['water_demand']['agricultural_m3h'].sum() / dataset['water_demand']['total_m3h'].sum() * 100:.1f}%")
    print(f"  Peak hourly demand: {dataset['water_demand']['total_m3h'].max():.1f} m³/h")
