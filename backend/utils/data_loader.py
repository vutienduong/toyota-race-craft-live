"""
Data loader for RaceCraft Live telemetry data
Handles long-format CSV files from Barber Motorsports Park
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BarberDataLoader:
    """Load and process Barber Motorsports Park telemetry data"""

    # Track configuration for Barber
    TRACK_CONFIG = {
        "name": "barber",
        "length_meters": 2380,  # 2.38 km
        "sectors": 3,
        "turns": 17,
        "wraparound_threshold": 100,  # Detect lap when lapdist < 100m after > 2200m
    }

    # Expected telemetry signals from DATA_PLAN.md
    TELEMETRY_SIGNALS = [
        "speed",  # km/h
        "Steering_Angle",  # degrees
        "gear",  # 1-6
        "nmot",  # RPM
        "aps",  # Throttle pedal % (using instead of ath)
        "pbrake_f",  # Front brake pressure (bar)
        "pbrake_r",  # Rear brake pressure (bar)
        "accx_can",  # Longitudinal G
        "accy_can",  # Lateral G
        "VBOX_Lat_Min",  # GPS latitude
        "VBOX_Long_Minutes",  # GPS longitude
        "Laptrigger_lapdist_dls",  # Distance from start/finish (meters)
    ]

    def __init__(self, data_dir: str = "data/barber"):
        self.data_dir = Path(data_dir)
        self.data_mode = os.getenv("DATA_MODE", "sample").lower()
        logger.info(f"BarberDataLoader initialized in '{self.data_mode}' mode")

    def get_telemetry_data(
        self,
        race: str = "R1",
        vehicle_id: Optional[str] = None,
        num_vehicles: int = 5,
        num_laps: int = 10
    ) -> pd.DataFrame:
        """
        Get telemetry data based on DATA_MODE environment variable

        Args:
            race: Race identifier ("R1" or "R2") - used for real data mode
            vehicle_id: Optional filter for specific vehicle
            num_vehicles: Number of vehicles for sample data mode
            num_laps: Number of laps for sample data mode

        Returns:
            Long-format DataFrame with telemetry data
        """
        if self.data_mode == "real":
            logger.info(f"Loading real data from {self.data_dir} for race {race}")
            df_long = self.load_telemetry_long(race=race)

            if df_long.empty:
                logger.warning("Real data not found, falling back to sample data")
                df_long = self.generate_sample_data(num_vehicles=num_vehicles, num_laps=num_laps)
        else:
            logger.info(f"Generating sample data: {num_vehicles} vehicles, {num_laps} laps")
            df_long = self.generate_sample_data(num_vehicles=num_vehicles, num_laps=num_laps)

        return df_long

    def load_telemetry_long(
        self,
        race: str = "R1",
        sample_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load telemetry data in long format

        Args:
            race: Race identifier ("R1" or "R2")
            sample_rows: If provided, only load this many rows (for testing)

        Returns:
            DataFrame with columns: meta_time, vehicle_id, telemetry_name, telemetry_value
        """
        filepath = self.data_dir / f"{race}_barber_telemetry_data.csv"

        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            logger.info("Returning empty DataFrame - use generate_sample_data() for testing")
            return pd.DataFrame()

        logger.info(f"Loading telemetry from {filepath}")

        # Load with chunking for large files (1.5GB)
        if sample_rows:
            df = pd.read_csv(filepath, nrows=sample_rows)
            logger.info(f"Loaded {len(df)} sample rows")
        else:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} rows")

        return df

    def pivot_telemetry_wide(
        self,
        df_long: pd.DataFrame,
        vehicle_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Convert long-format telemetry to wide format

        Long format: Each row is one sensor reading
        Wide format: Each row is one timestamp with all sensors

        Args:
            df_long: Long-format DataFrame
            vehicle_id: Optional filter for specific vehicle

        Returns:
            Wide-format DataFrame with one column per telemetry signal
        """
        if df_long.empty:
            return pd.DataFrame()

        # Filter to specific vehicle if requested
        if vehicle_id:
            df_long = df_long[df_long['vehicle_id'] == vehicle_id].copy()

        logger.info(f"Pivoting {len(df_long)} rows to wide format...")

        # Pivot on meta_time and telemetry_name
        df_wide = df_long.pivot_table(
            index=['meta_time', 'vehicle_id', 'vehicle_number', 'lap'],
            columns='telemetry_name',
            values='telemetry_value',
            aggfunc='first'  # Take first value if duplicates
        ).reset_index()

        # Forward-fill missing values (sensor dropouts)
        df_wide = df_wide.sort_values('meta_time')
        df_wide[self.TELEMETRY_SIGNALS] = df_wide[self.TELEMETRY_SIGNALS].ffill()

        logger.info(f"Pivoted to {len(df_wide)} timestamps with {df_wide.shape[1]} columns")

        return df_wide

    def load_lap_times(self, race: str = "R1") -> pd.DataFrame:
        """Load lap completion times"""
        filepath = self.data_dir / f"{race}_barber_lap_time.csv"

        if not filepath.exists():
            return pd.DataFrame()

        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} lap time records")
        return df

    def load_sector_analysis(self, race: str = "R1") -> pd.DataFrame:
        """Load sector timing and race analysis data"""
        filepath = self.data_dir / "23_AnalysisEnduranceWithSections_Race 1_Anonymized.CSV" if race == "R1" else \
                   self.data_dir / "23_AnalysisEnduranceWithSections_Race 2_Anonymized.CSV"

        if not filepath.exists():
            return pd.DataFrame()

        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} sector analysis records")
        return df

    def load_race_results(self, race: str = "R1") -> pd.DataFrame:
        """Load final race results"""
        filepath = self.data_dir / f"03_Provisional Results_Race {race[1]}_Anonymized.CSV"

        if not filepath.exists():
            return pd.DataFrame()

        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} race result records")
        return df

    def generate_sample_data(
        self,
        num_vehicles: int = 5,
        num_laps: int = 10,
        hz: int = 10  # 10Hz sampling
    ) -> pd.DataFrame:
        """
        Generate synthetic telemetry data for testing
        Simulates Barber telemetry in long format

        Args:
            num_vehicles: Number of cars to simulate
            num_laps: Number of laps per vehicle
            hz: Sampling rate (Hz)

        Returns:
            Long-format DataFrame matching Barber schema
        """
        logger.info(f"Generating sample data: {num_vehicles} vehicles, {num_laps} laps")

        records = []
        track_length = self.TRACK_CONFIG["length_meters"]
        lap_time_avg = 90  # seconds (avg ~1:30 lap time at Barber)

        for vehicle_num in range(num_vehicles):
            vehicle_id = f"GR86-{vehicle_num:03d}-{vehicle_num * 10}"

            for lap_num in range(1, num_laps + 1):
                # Simulate lap time variation and degradation
                lap_time = lap_time_avg + np.random.normal(0, 0.5) + (lap_num * 0.05)
                samples_per_lap = int(lap_time * hz)

                for sample in range(samples_per_lap):
                    # Calculate position and time
                    progress = sample / samples_per_lap
                    distance = progress * track_length
                    time_offset = progress * lap_time + (lap_num - 1) * lap_time_avg

                    # Simulate telemetry values
                    telemetry_data = {
                        "speed": 120 + 60 * np.sin(progress * 6 * np.pi) + np.random.normal(0, 2),
                        "Steering_Angle": 100 * np.sin(progress * 8 * np.pi) + np.random.normal(0, 5),
                        "gear": min(6, max(1, int(3 + 2 * np.sin(progress * 6 * np.pi)))),
                        "nmot": 4000 + 2000 * np.sin(progress * 6 * np.pi) + np.random.normal(0, 100),
                        "aps": max(0, min(100, 50 + 40 * np.sin(progress * 6 * np.pi) + np.random.normal(0, 5))),
                        "pbrake_f": max(0, 30 * (1 - np.sin(progress * 6 * np.pi)) + np.random.normal(0, 2)),
                        "pbrake_r": max(0, 20 * (1 - np.sin(progress * 6 * np.pi)) + np.random.normal(0, 1.5)),
                        "accx_can": np.sin(progress * 6 * np.pi) * 1.2 + np.random.normal(0, 0.1),
                        "accy_can": np.cos(progress * 8 * np.pi) * 1.5 + np.random.normal(0, 0.1),
                        "VBOX_Lat_Min": 33.5 + 0.01 * np.sin(progress * 2 * np.pi),
                        "VBOX_Long_Minutes": -86.5 + 0.01 * np.cos(progress * 2 * np.pi),
                        "Laptrigger_lapdist_dls": distance,
                    }

                    # Create long-format records (one per telemetry signal)
                    for signal_name, signal_value in telemetry_data.items():
                        records.append({
                            "meta_time": 1000000 + time_offset,
                            "vehicle_id": vehicle_id,
                            "vehicle_number": vehicle_num,
                            "lap": lap_num,
                            "telemetry_name": signal_name,
                            "telemetry_value": signal_value,
                            "timestamp": time_offset,
                        })

        df = pd.DataFrame(records)
        logger.info(f"Generated {len(df)} telemetry records")
        return df


# Example usage
if __name__ == "__main__":
    loader = BarberDataLoader()

    # Generate sample data
    df_long = loader.generate_sample_data(num_vehicles=3, num_laps=5)
    print(f"Sample long format: {df_long.shape}")
    print(df_long.head(20))

    # Convert to wide format
    df_wide = loader.pivot_telemetry_wide(df_long, vehicle_id="GR86-000-0")
    print(f"\nSample wide format: {df_wide.shape}")
    print(df_wide.head())
