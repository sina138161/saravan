"""
Saravan Data Generator
Generates realistic time series for all model inputs
Based on Saravan climate and field measurements

Profiles generated:
1. Wind speed (m/s)
2. Dust PM10 (μg/m³)
3. Temperature (°C)
4. Water demand - Agricultural & Urban only (m³/h)
5. Electricity demand (kWh)
6. Heat demand (kWh-thermal)
7. Biomass availability (ton/h)
8. Gas network availability (seasonal)
9. Groundwater availability (seasonal)

NOTE: No industrial sector - Saravan has no industrial activity
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple
from pathlib import Path
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
        Define Saravan-specific parameters

        Based on:
        - NASA POWER meteorological data
        - Iran Meteorological Organization records
        - Field measurements from Sistan-Baluchestan
        - Iran Gas Company data
        - Regional Water Authority data
        """

        params = {
            # ===== CLIMATE =====
            'wind': {
                'annual_mean': 7.5,  # m/s
                'weibull_k': 2.1,
                'weibull_lambda': 8.5,
                'seasonal_variation': {
                    'spring': 1.3,
                    'summer': 1.4,  # 120-day wind
                    'fall': 0.9,
                    'winter': 0.8
                },
                'diurnal_peak_hour': 14,
                'diurnal_amplitude': 0.3
            },

            'dust': {
                'baseline_pm10': 80,  # μg/m³
                'storm_pm10': 300,
                'storm_frequency': 0.15,
                'seasonal_variation': {
                    'spring': 2.0,
                    'summer': 2.5,
                    'fall': 1.2,
                    'winter': 0.8
                },
                'storm_duration_hours': (6, 24),
                'correlation_with_wind': 0.6
            },

            'temperature': {
                'annual_mean': 28,  # °C
                'summer_max': 45,
                'winter_min': 10,
                'diurnal_range': 15,
                'peak_hour': 15
            },

            # ===== WATER DEMAND (NO INDUSTRIAL) =====
            'water_demand': {
                'agricultural': {
                    'annual_total': 400000,  # m³/year
                    'seasonal_factor': {
                        'spring': 1.2,
                        'summer': 2.0,
                        'fall': 0.8,
                        'winter': 0.4
                    },
                    'daily_pattern': 'daylight'
                },
                'urban': {
                    'annual_total': 80000,  # m³/year
                    'seasonal_factor': {
                        'spring': 1.0,
                        'summer': 1.4,
                        'fall': 1.0,
                        'winter': 0.9
                    },
                    'daily_pattern': 'two_peaks'
                }
                # NOTE: NO INDUSTRIAL - Saravan has no industrial water demand
            },

            # ===== ELECTRICITY DEMAND (NO INDUSTRIAL) =====
            'electricity_demand': {
                'urban': {
                    'annual_total_kwh': 500000,
                    'seasonal_factor': {
                        'spring': 1.0,
                        'summer': 1.5,
                        'fall': 1.0,
                        'winter': 1.2
                    },
                    'daily_pattern': 'two_peaks'
                },
                # NOTE: NO INDUSTRIAL
                'pumping': {
                    'energy_per_m3': 1.2  # kWh/m³
                },
                'treatment': {
                    'primary_kwh_per_m3': 0.15,
                    'secondary_kwh_per_m3': 0.50,
                    'wastewater_primary_kwh_per_m3': 0.25,
                    'wastewater_secondary_kwh_per_m3': 0.60
                }
            },

            # ===== HEAT DEMAND =====
            'heat_demand': {
                'urban': {
                    'annual_total_kwh_thermal': 300000,
                    'seasonal_factor': {
                        'spring': 0.6,
                        'summer': 0.3,
                        'fall': 0.8,
                        'winter': 1.8
                    },
                    'daily_pattern': 'morning_evening'
                }
            },

            # ===== BIOMASS (ton/h) =====
            'biomass': {
                'local_availability': {
                    'agricultural_residue': 50,   # ton/year
                    'animal_waste': 30,           # ton/year
                    'urban_organic_waste': 20     # ton/year
                },  # TOTAL: 100 ton/year
                'energy_content_kwh_per_ton': 4200,  # kWh/ton (LHV)
                'seasonal_pattern': {
                    'spring': 0.8,
                    'summer': 1.2,
                    'fall': 1.3,
                    'winter': 0.7
                },
                'moisture_content': 0.15
            },

            # ===== GAS NETWORK (NEW) =====
            'gas_network': {
                'max_capacity_mw': 10.0,  # MW thermal equivalent
                'base_availability': 0.95,  # 95% base availability
                'seasonal_factor': {
                    'spring': 1.0,    # Normal
                    'summer': 0.85,   # Reduced (maintenance + exports)
                    'fall': 1.0,      # Normal
                    'winter': 0.75    # Lowest (high domestic demand)
                },
                'price_per_mwh': 40,  # $/MWh thermal
                'maintenance_days_per_year': 10  # Planned maintenance
            },

            # ===== GROUNDWATER (NEW) =====
            'groundwater': {
                'max_extraction_m3h': 100,  # m³/hour max
                'aquifer_depth_m': 80,      # meters
                'seasonal_factor': {
                    'spring': 1.0,    # Normal recharge
                    'summer': 0.70,   # Low (high demand, low recharge)
                    'fall': 0.85,     # Recovery
                    'winter': 1.1     # High (recharge from rain)
                },
                'safe_yield_percent': 0.80,  # 80% of max is safe
                'quality_tds_mg_l': 1500,    # Total dissolved solids
                'pumping_cost_per_m3': 0.08  # $/m³
            }
        }

        return params

    def generate_wind_data(self, hours: int = 8760,
                          start_date: str = "2025-01-01") -> pd.DataFrame:
        """Generate hourly wind speed data using Weibull distribution"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')

        k = self.saravan_params['wind']['weibull_k']
        lam = self.saravan_params['wind']['weibull_lambda']
        base_wind = np.random.weibull(k, hours) * lam

        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'wind') for ts in timestamps
        ])
        wind_seasonal = base_wind * seasonal_factor

        diurnal_factor = np.array([
            self._get_diurnal_factor(ts.hour,
                                    self.saravan_params['wind']['diurnal_peak_hour'],
                                    self.saravan_params['wind']['diurnal_amplitude'])
            for ts in timestamps
        ])
        wind_hourly = wind_seasonal * diurnal_factor
        wind_hourly = np.clip(wind_hourly, 0, 30)

        return pd.DataFrame({
            'timestamp': timestamps,
            'wind_speed_ms': wind_hourly
        })

    def generate_dust_data(self, hours: int = 8760,
                          start_date: str = "2025-01-01",
                          wind_data: pd.DataFrame = None) -> pd.DataFrame:
        """Generate hourly PM10 dust concentration data"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')
        baseline = self.saravan_params['dust']['baseline_pm10']

        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'dust') for ts in timestamps
        ])
        dust = baseline * seasonal_factor

        # Add dust storms
        storm_prob = self.saravan_params['dust']['storm_frequency'] / 24
        for i in range(hours):
            if np.random.random() < storm_prob:
                duration = np.random.randint(
                    self.saravan_params['dust']['storm_duration_hours'][0],
                    self.saravan_params['dust']['storm_duration_hours'][1]
                )
                intensity = self.saravan_params['dust']['storm_pm10']
                end_hour = min(i + duration, hours)
                dust[i:end_hour] = intensity * seasonal_factor[i:end_hour]

        # Correlate with wind
        if wind_data is not None:
            wind_speeds = wind_data['wind_speed_ms'].values[:hours]
            wind_factor = 1 + 0.3 * (wind_speeds - 7.5) / 7.5
            wind_factor = np.clip(wind_factor, 0.7, 1.5)
            dust = dust * wind_factor

        noise = np.random.lognormal(0, 0.2, hours)
        dust = dust * noise
        dust = np.clip(dust, 20, 500)

        return pd.DataFrame({
            'timestamp': timestamps,
            'pm10_ugm3': dust
        })

    def generate_temperature_data(self, hours: int = 8760,
                                  start_date: str = "2025-01-01") -> pd.DataFrame:
        """Generate hourly temperature data"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')

        day_of_year = np.array([ts.timetuple().tm_yday for ts in timestamps])
        seasonal_temp = (
            self.saravan_params['temperature']['annual_mean'] +
            17 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        )

        hour_of_day = np.array([ts.hour for ts in timestamps])
        diurnal_amplitude = self.saravan_params['temperature']['diurnal_range'] / 2
        diurnal_temp = diurnal_amplitude * np.sin(2 * np.pi * (hour_of_day - 6) / 24)

        temperature = seasonal_temp + diurnal_temp
        noise = np.random.normal(0, 1, hours)
        temperature = np.clip(temperature + noise, 5, 50)

        return pd.DataFrame({
            'timestamp': timestamps,
            'temperature_c': temperature
        })

    def generate_water_demand(self, hours: int = 8760,
                             start_date: str = "2025-01-01") -> pd.DataFrame:
        """Generate hourly water demand - Agricultural & Urban ONLY (no industrial)"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')
        demands = {}

        # Only agricultural and urban (NO INDUSTRIAL)
        for sector in ['agricultural', 'urban']:
            sector_params = self.saravan_params['water_demand'][sector]
            annual_total = sector_params['annual_total']
            avg_hourly = annual_total / 8760

            seasonal_factor = np.array([
                self._get_seasonal_factor(ts, sector, resource='water')
                for ts in timestamps
            ])

            if sector_params['daily_pattern'] == 'daylight':
                daily_factor = np.array([
                    1.5 if 6 <= ts.hour <= 18 else 0.2
                    for ts in timestamps
                ])
            elif sector_params['daily_pattern'] == 'two_peaks':
                daily_factor = np.array([
                    1.5 if ts.hour in [7, 19] else
                    1.2 if 6 <= ts.hour <= 9 or 18 <= ts.hour <= 21 else 0.7
                    for ts in timestamps
                ])
            else:
                daily_factor = np.ones(hours)

            demand = avg_hourly * seasonal_factor * daily_factor
            period_total = annual_total * (hours / 8760)
            demand = demand * (period_total / demand.sum())
            noise = np.random.lognormal(0, 0.1, hours)
            demands[sector] = demand * noise

        demands['total'] = demands['agricultural'] + demands['urban']

        return pd.DataFrame({
            'timestamp': timestamps,
            'agricultural_m3h': demands['agricultural'],
            'urban_m3h': demands['urban'],
            'total_m3h': demands['total']
        })

    def generate_electricity_demand(self, hours: int = 8760,
                                    start_date: str = "2025-01-01",
                                    water_demand_df: pd.DataFrame = None) -> pd.DataFrame:
        """Generate hourly electricity demand - Urban ONLY (no industrial)"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')
        demands = {}

        # Urban only (NO INDUSTRIAL)
        urban_params = self.saravan_params['electricity_demand']['urban']
        annual_total = urban_params['annual_total_kwh']
        avg_hourly = annual_total / 8760

        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'urban', resource='electricity')
            for ts in timestamps
        ])

        daily_factor = np.array([
            1.8 if ts.hour in [8, 19] else
            1.4 if 6 <= ts.hour <= 10 or 17 <= ts.hour <= 22 else 0.6
            for ts in timestamps
        ])

        urban_demand = avg_hourly * seasonal_factor * daily_factor
        period_total = annual_total * (hours / 8760)
        urban_demand = urban_demand * (period_total / urban_demand.sum())
        noise = np.random.lognormal(0, 0.08, hours)
        demands['urban'] = urban_demand * noise

        # Pumping and treatment (dependent on water)
        if water_demand_df is not None:
            water_total = water_demand_df['total_m3h'].values[:hours]
            demands['pumping'] = water_total * self.saravan_params['electricity_demand']['pumping']['energy_per_m3']

            water_agri = water_demand_df['agricultural_m3h'].values[:hours]
            water_urban = water_demand_df['urban_m3h'].values[:hours]
            treatment = self.saravan_params['electricity_demand']['treatment']

            primary = water_agri * treatment['primary_kwh_per_m3']
            secondary = water_urban * treatment['secondary_kwh_per_m3']
            wastewater = water_urban * 0.80 * treatment['wastewater_primary_kwh_per_m3']
            demands['treatment'] = primary + secondary + wastewater
        else:
            demands['pumping'] = np.zeros(hours)
            demands['treatment'] = np.zeros(hours)

        demands['total'] = demands['urban'] + demands['pumping'] + demands['treatment']

        return pd.DataFrame({
            'timestamp': timestamps,
            'urban_kwh': demands['urban'],
            'pumping_kwh': demands['pumping'],
            'treatment_kwh': demands['treatment'],
            'total_kwh': demands['total']
        })

    def generate_heat_demand(self, hours: int = 8760,
                            start_date: str = "2025-01-01") -> pd.DataFrame:
        """Generate hourly heat demand"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')

        urban_params = self.saravan_params['heat_demand']['urban']
        annual_total = urban_params['annual_total_kwh_thermal']
        avg_hourly = annual_total / 8760

        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'urban', resource='heat')
            for ts in timestamps
        ])

        daily_factor = np.array([
            1.8 if ts.hour in [6, 7, 20, 21] else
            1.2 if 5 <= ts.hour <= 9 or 18 <= ts.hour <= 23 else 0.5
            for ts in timestamps
        ])

        heat_demand = avg_hourly * seasonal_factor * daily_factor
        period_total = annual_total * (hours / 8760)
        heat_demand = heat_demand * (period_total / heat_demand.sum())
        noise = np.random.lognormal(0, 0.1, hours)
        heat_demand = heat_demand * noise

        return pd.DataFrame({
            'timestamp': timestamps,
            'urban_kwh_thermal': heat_demand,
            'total_kwh_thermal': heat_demand
        })

    def generate_biomass_availability(self, hours: int = 8760,
                                     start_date: str = "2025-01-01") -> pd.DataFrame:
        """Generate hourly biomass availability in ton/h"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')
        biomass_params = self.saravan_params['biomass']

        # Total annual in tons
        total_annual_ton = sum(biomass_params['local_availability'].values())  # 100 ton/year
        avg_hourly_ton = total_annual_ton / 8760

        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'biomass', resource='biomass')
            for ts in timestamps
        ])

        biomass = avg_hourly_ton * seasonal_factor
        period_total = total_annual_ton * (hours / 8760)
        biomass = biomass * (period_total / biomass.sum())
        noise = np.random.lognormal(0, 0.15, hours)
        biomass = biomass * noise

        # Energy content (kWh/ton)
        energy = biomass * biomass_params['energy_content_kwh_per_ton']

        return pd.DataFrame({
            'timestamp': timestamps,
            'biomass_available_ton_h': biomass,
            'biomass_energy_kwh_h': energy
        })

    def generate_gas_network_availability(self, hours: int = 8760,
                                          start_date: str = "2025-01-01") -> pd.DataFrame:
        """Generate gas network availability profile (seasonal variation)"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')
        gas_params = self.saravan_params['gas_network']

        max_capacity = gas_params['max_capacity_mw']
        base_availability = gas_params['base_availability']

        # Seasonal variation
        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'gas_network', resource='gas')
            for ts in timestamps
        ])

        # Base availability with seasonal variation
        availability = base_availability * seasonal_factor

        # Add random maintenance outages
        maintenance_hours = gas_params['maintenance_days_per_year'] * 24
        maintenance_prob = maintenance_hours / 8760
        for i in range(hours):
            if np.random.random() < maintenance_prob / 24:  # Per hour probability
                duration = np.random.randint(4, 24)  # 4-24 hour outage
                end_hour = min(i + duration, hours)
                availability[i:end_hour] *= 0.5  # 50% capacity during maintenance

        # Small random noise
        noise = np.random.normal(1, 0.02, hours)
        availability = np.clip(availability * noise, 0.3, 1.0)

        # Available capacity in MW
        available_mw = max_capacity * availability

        return pd.DataFrame({
            'timestamp': timestamps,
            'gas_availability_factor': availability,
            'gas_available_mw': available_mw,
            'gas_max_capacity_mw': np.full(hours, max_capacity),
            'gas_price_usd_mwh': np.full(hours, gas_params['price_per_mwh'])
        })

    def generate_groundwater_availability(self, hours: int = 8760,
                                          start_date: str = "2025-01-01") -> pd.DataFrame:
        """Generate groundwater availability profile (seasonal variation)"""

        timestamps = pd.date_range(start=start_date, periods=hours, freq='H')
        gw_params = self.saravan_params['groundwater']

        max_extraction = gw_params['max_extraction_m3h']
        safe_yield = gw_params['safe_yield_percent']

        # Seasonal variation
        seasonal_factor = np.array([
            self._get_seasonal_factor(ts, 'groundwater', resource='groundwater')
            for ts in timestamps
        ])

        # Safe extraction rate with seasonal variation
        safe_extraction = max_extraction * safe_yield * seasonal_factor

        # Add small random variation (aquifer response)
        noise = np.random.normal(1, 0.05, hours)
        safe_extraction = np.clip(safe_extraction * noise,
                                  max_extraction * 0.3,
                                  max_extraction)

        return pd.DataFrame({
            'timestamp': timestamps,
            'gw_availability_factor': seasonal_factor,
            'gw_safe_extraction_m3h': safe_extraction,
            'gw_max_extraction_m3h': np.full(hours, max_extraction),
            'gw_depth_m': np.full(hours, gw_params['aquifer_depth_m']),
            'gw_quality_tds_mg_l': np.full(hours, gw_params['quality_tds_mg_l']),
            'gw_pumping_cost_usd_m3': np.full(hours, gw_params['pumping_cost_per_m3'])
        })

    def generate_complete_dataset(self, hours: int = 8760,
                                 start_date: str = "2025-01-01") -> Dict[str, pd.DataFrame]:
        """Generate complete dataset with all variables"""

        print(f"\n{'='*70}")
        print(f"GENERATING SARAVAN DATA")
        print(f"{'='*70}")
        print(f"Duration: {hours} hours ({hours/24:.0f} days)")
        print(f"Start date: {start_date}")

        print("\n🌪️  Generating wind data...")
        wind_df = self.generate_wind_data(hours, start_date)
        print(f"   Mean: {wind_df['wind_speed_ms'].mean():.2f} m/s")

        print("\n🏜️  Generating dust data...")
        dust_df = self.generate_dust_data(hours, start_date, wind_df)
        print(f"   Mean PM10: {dust_df['pm10_ugm3'].mean():.0f} μg/m³")

        print("\n🌡️  Generating temperature data...")
        temp_df = self.generate_temperature_data(hours, start_date)
        print(f"   Mean: {temp_df['temperature_c'].mean():.1f}°C")

        print("\n💧 Generating water demand (Agricultural + Urban only)...")
        water_df = self.generate_water_demand(hours, start_date)
        print(f"   Total: {water_df['total_m3h'].sum():,.0f} m³ (NO INDUSTRIAL)")

        print("\n⚡ Generating electricity demand (Urban only)...")
        elec_df = self.generate_electricity_demand(hours, start_date, water_df)
        print(f"   Total: {elec_df['total_kwh'].sum():,.0f} kWh (NO INDUSTRIAL)")

        print("\n🔥 Generating heat demand...")
        heat_df = self.generate_heat_demand(hours, start_date)
        print(f"   Total: {heat_df['total_kwh_thermal'].sum():,.0f} kWh-thermal")

        print("\n🌾 Generating biomass availability (ton/h)...")
        biomass_df = self.generate_biomass_availability(hours, start_date)
        print(f"   Total: {biomass_df['biomass_available_ton_h'].sum():,.2f} ton")

        print("\n🔵 Generating gas network availability...")
        gas_df = self.generate_gas_network_availability(hours, start_date)
        print(f"   Mean availability: {gas_df['gas_availability_factor'].mean()*100:.1f}%")

        print("\n💦 Generating groundwater availability...")
        gw_df = self.generate_groundwater_availability(hours, start_date)
        print(f"   Mean safe extraction: {gw_df['gw_safe_extraction_m3h'].mean():.1f} m³/h")

        print(f"\n✅ Data generation complete!")

        return {
            'wind': wind_df,
            'dust': dust_df,
            'temperature': temp_df,
            'water_demand': water_df,
            'electricity_demand': elec_df,
            'heat_demand': heat_df,
            'biomass': biomass_df,
            'gas_network': gas_df,
            'groundwater': gw_df
        }

    def _get_seasonal_factor(self, timestamp: pd.Timestamp,
                            variable: str,
                            resource: str = None) -> float:
        """Get seasonal multiplication factor"""

        month = timestamp.month
        if month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        elif month in [9, 10, 11]:
            season = 'fall'
        else:
            season = 'winter'

        if resource == 'water':
            return self.saravan_params['water_demand'][variable]['seasonal_factor'][season]
        elif resource == 'electricity':
            return self.saravan_params['electricity_demand'][variable]['seasonal_factor'][season]
        elif resource == 'heat':
            return self.saravan_params['heat_demand'][variable]['seasonal_factor'][season]
        elif resource == 'biomass':
            return self.saravan_params['biomass']['seasonal_pattern'][season]
        elif resource == 'gas':
            return self.saravan_params['gas_network']['seasonal_factor'][season]
        elif resource == 'groundwater':
            return self.saravan_params['groundwater']['seasonal_factor'][season]
        else:
            return self.saravan_params[variable]['seasonal_variation'][season]

    def _get_diurnal_factor(self, hour: int, peak_hour: int, amplitude: float) -> float:
        """Get diurnal multiplication factor"""
        factor = 1 + amplitude * np.sin(2 * np.pi * (hour - peak_hour + 6) / 24)
        return max(0.5, factor)

    def export_to_excel(self, dataset: Dict[str, pd.DataFrame],
                       output_dir: str = 'data/input') -> None:
        """Export all data to Excel files"""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*70}")
        print("EXPORTING DATA TO EXCEL")
        print(f"{'='*70}")

        for name, df in dataset.items():
            filename = output_path / f"saravan_{name}.xlsx"
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"   ✓ Saved: {filename}")

        # Also export parameters to Excel
        self._export_parameters_to_excel(output_path)

        print(f"\n✅ All data exported to {output_dir}/")

    def _export_parameters_to_excel(self, output_path: Path) -> None:
        """Export model parameters to Excel"""

        # Economic parameters
        economic_params = {
            'Parameter': [
                'Gas price ($/MWh)',
                'Groundwater pumping cost ($/m³)',
                'Biomass collection cost ($/ton)',
                'Electricity feed-in tariff ($/kWh)',
                'Heat sale price ($/kWh-thermal)',
                'Compost price ($/ton)',
                'Digestate price ($/ton)',
                'CO2 price ($/kg)'
            ],
            'Value': [
                self.saravan_params['gas_network']['price_per_mwh'],
                self.saravan_params['groundwater']['pumping_cost_per_m3'],
                0.05 * 1000,  # Convert $/kg to $/ton
                0.10,
                0.05,
                50,
                60,
                0.15
            ],
            'Unit': ['$/MWh', '$/m³', '$/ton', '$/kWh', '$/kWh-th', '$/ton', '$/ton', '$/kg']
        }
        pd.DataFrame(economic_params).to_excel(
            output_path / 'parameters_economic.xlsx', index=False
        )
        print(f"   ✓ Saved: parameters_economic.xlsx")

        # Technical parameters
        technical_params = {
            'Parameter': [
                'Max groundwater extraction (m³/h)',
                'Aquifer depth (m)',
                'Groundwater TDS (mg/L)',
                'Gas network max capacity (MW)',
                'Biomass energy content (kWh/ton)',
                'CHP electrical efficiency',
                'CHP thermal efficiency',
                'Boiler thermal efficiency',
                'Battery efficiency',
                'Wastewater return rate'
            ],
            'Value': [
                self.saravan_params['groundwater']['max_extraction_m3h'],
                self.saravan_params['groundwater']['aquifer_depth_m'],
                self.saravan_params['groundwater']['quality_tds_mg_l'],
                self.saravan_params['gas_network']['max_capacity_mw'],
                self.saravan_params['biomass']['energy_content_kwh_per_ton'],
                0.35,
                0.45,
                0.85,
                0.92,
                0.80
            ],
            'Unit': ['m³/h', 'm', 'mg/L', 'MW', 'kWh/ton', '-', '-', '-', '-', '-']
        }
        pd.DataFrame(technical_params).to_excel(
            output_path / 'parameters_technical.xlsx', index=False
        )
        print(f"   ✓ Saved: parameters_technical.xlsx")

        # Environmental parameters
        environmental_params = {
            'Parameter': [
                'CO2 emission factor - Natural gas (kg/kWh)',
                'CO2 emission factor - Biogas (kg/kWh)',
                'CO2 emission factor - Grid electricity (kg/kWh)',
                'Water primary treatment energy (kWh/m³)',
                'Water secondary treatment energy (kWh/m³)',
                'Wastewater primary treatment energy (kWh/m³)',
                'Wastewater secondary treatment energy (kWh/m³)',
                'Sludge production (kg/m³ wastewater)'
            ],
            'Value': [0.20, 0.0, 0.45, 0.15, 0.50, 0.25, 0.60, 0.075],
            'Unit': ['kg/kWh', 'kg/kWh', 'kg/kWh', 'kWh/m³', 'kWh/m³', 'kWh/m³', 'kWh/m³', 'kg/m³']
        }
        pd.DataFrame(environmental_params).to_excel(
            output_path / 'parameters_environmental.xlsx', index=False
        )
        print(f"   ✓ Saved: parameters_environmental.xlsx")

    def export_to_csv(self, dataset: Dict[str, pd.DataFrame],
                     output_dir: str = 'data/input') -> None:
        """Export all data to CSV files (legacy support)"""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for name, df in dataset.items():
            filename = output_path / f"saravan_{name}.csv"
            df.to_csv(filename, index=False)


# Example usage
if __name__ == "__main__":
    generator = SaravanDataGenerator(random_seed=42)
    dataset = generator.generate_complete_dataset(hours=8760, start_date="2025-01-01")
    generator.export_to_excel(dataset, output_dir='input')
