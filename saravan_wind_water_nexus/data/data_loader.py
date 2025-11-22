"""
Data Loader for Saravan Wind-Water-Energy-Carbon Nexus

Loads time series profiles and parameters from Excel files in data/input/
All model code should use this loader to read data.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional


class DataLoader:
    """
    Load data from Excel files in data/input/

    Usage:
        loader = DataLoader()
        dataset = loader.load_all_profiles()
        params = loader.load_parameters()
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data loader

        Args:
            data_dir: Path to data/input directory (default: auto-detect)
        """
        if data_dir is None:
            # Auto-detect data directory
            self.data_dir = Path(__file__).parent / 'input'
        else:
            self.data_dir = Path(data_dir)

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

    def load_profile(self, profile_name: str) -> pd.DataFrame:
        """
        Load a single profile from Excel

        Args:
            profile_name: Name of profile (e.g., 'wind', 'water_demand')

        Returns:
            DataFrame with profile data
        """
        # Try Excel first, then CSV
        excel_path = self.data_dir / f"saravan_{profile_name}.xlsx"
        csv_path = self.data_dir / f"saravan_{profile_name}.csv"

        if excel_path.exists():
            df = pd.read_excel(excel_path, engine='openpyxl')
        elif csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            raise FileNotFoundError(f"Profile not found: {profile_name}")

        # Convert timestamp column if exists
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def load_all_profiles(self) -> Dict[str, pd.DataFrame]:
        """
        Load all time series profiles

        Returns:
            Dictionary of DataFrames for each profile
        """
        profiles = [
            'wind',
            'dust',
            'temperature',
            'water_demand',
            'electricity_demand',
            'heat_demand',
            'biomass',
            'gas_network',
            'groundwater'
        ]

        dataset = {}
        for profile in profiles:
            try:
                dataset[profile] = self.load_profile(profile)
            except FileNotFoundError:
                print(f"Warning: Profile '{profile}' not found, skipping...")

        return dataset

    def load_parameters(self, param_type: str = 'all') -> Dict[str, pd.DataFrame]:
        """
        Load model parameters from Excel

        Args:
            param_type: 'economic', 'technical', 'environmental', or 'all'

        Returns:
            Dictionary of parameter DataFrames
        """
        params = {}

        if param_type in ['economic', 'all']:
            path = self.data_dir / 'parameters_economic.xlsx'
            if path.exists():
                params['economic'] = pd.read_excel(path, engine='openpyxl')

        if param_type in ['technical', 'all']:
            path = self.data_dir / 'parameters_technical.xlsx'
            if path.exists():
                params['technical'] = pd.read_excel(path, engine='openpyxl')

        if param_type in ['environmental', 'all']:
            path = self.data_dir / 'parameters_environmental.xlsx'
            if path.exists():
                params['environmental'] = pd.read_excel(path, engine='openpyxl')

        return params

    def get_parameter_value(self, param_name: str,
                           param_type: str = 'all') -> Optional[float]:
        """
        Get a single parameter value by name

        Args:
            param_name: Name of parameter
            param_type: 'economic', 'technical', 'environmental', or 'all'

        Returns:
            Parameter value or None if not found
        """
        params = self.load_parameters(param_type)

        for df in params.values():
            if 'Parameter' in df.columns and 'Value' in df.columns:
                match = df[df['Parameter'] == param_name]
                if len(match) > 0:
                    return match['Value'].values[0]

        return None

    def get_profile_statistics(self, profile_name: str) -> Dict:
        """
        Get basic statistics for a profile

        Args:
            profile_name: Name of profile

        Returns:
            Dictionary of statistics
        """
        df = self.load_profile(profile_name)

        stats = {}
        for col in df.columns:
            if col != 'timestamp' and df[col].dtype in ['float64', 'int64']:
                stats[col] = {
                    'mean': df[col].mean(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'sum': df[col].sum(),
                    'std': df[col].std()
                }

        return stats


def load_dataset_from_excel(data_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to load all data

    Args:
        data_dir: Path to data/input directory

    Returns:
        Dictionary of DataFrames
    """
    loader = DataLoader(data_dir)
    return loader.load_all_profiles()


def load_parameters_from_excel(data_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to load all parameters

    Args:
        data_dir: Path to data/input directory

    Returns:
        Dictionary of parameter DataFrames
    """
    loader = DataLoader(data_dir)
    return loader.load_parameters()


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("DATA LOADER TEST")
    print("="*70)

    try:
        loader = DataLoader()

        print("\nLoading all profiles...")
        dataset = loader.load_all_profiles()
        print(f"Loaded {len(dataset)} profiles:")
        for name, df in dataset.items():
            print(f"  - {name}: {len(df)} rows, {len(df.columns)} columns")

        print("\nLoading parameters...")
        params = loader.load_parameters()
        for ptype, df in params.items():
            print(f"  - {ptype}: {len(df)} parameters")

        print("\nExample - Get gas price:")
        gas_price = loader.get_parameter_value('Gas price ($/MWh)')
        print(f"  Gas price: ${gas_price}/MWh")

        print("\n✅ Data loader test complete!")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Run prepare_data.py first to generate data files")
