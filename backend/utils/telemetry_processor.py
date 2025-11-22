"""
Telemetry processing utilities for RaceCraft Live
Handles data ingestion, normalization, and feature engineering
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TelemetryConfig:
    """Configuration for telemetry processing"""
    track_length_meters: Dict[str, float] = None

    def __post_init__(self):
        if self.track_length_meters is None:
            # Track lengths for GR Cup circuits (approximate)
            self.track_length_meters = {
                "barber": 3830,      # Barber Motorsports Park
                "cota": 5513,        # Circuit of the Americas
                "indy": 4192,        # Indianapolis Motor Speedway Road Course
                "road_america": 6515, # Road America
                "sebring": 6019,     # Sebring International Raceway
                "sonoma": 4052,      # Sonoma Raceway
                "vir": 5280          # Virginia International Raceway
            }


class TelemetryProcessor:
    """Process raw telemetry data from GR Cup races"""

    def __init__(self, config: Optional[TelemetryConfig] = None):
        self.config = config or TelemetryConfig()

    def load_telemetry_csv(self, filepath: str) -> pd.DataFrame:
        """
        Load telemetry CSV file

        Args:
            filepath: Path to CSV file

        Returns:
            DataFrame with telemetry data
        """
        df = pd.read_csv(filepath)
        return df

    def normalize_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize timestamps using meta_time as primary ordering
        ECU timestamps may drift, so meta_time is more reliable

        Args:
            df: Telemetry DataFrame

        Returns:
            DataFrame with normalized timestamps
        """
        df = df.copy()

        # Sort by meta_time to ensure correct ordering
        if 'meta_time' in df.columns:
            df = df.sort_values('meta_time').reset_index(drop=True)

        return df

    def detect_lap_boundaries(
        self,
        df: pd.DataFrame,
        track_name: str
    ) -> List[Tuple[int, int]]:
        """
        Detect lap boundaries using lapdist wraparound
        Lap numbers may be corrupted, so use lapdist instead

        Args:
            df: Telemetry DataFrame with 'lapdist' column
            track_name: Name of the track (e.g., 'cota', 'barber')

        Returns:
            List of (start_idx, end_idx) tuples for each lap
        """
        if 'lapdist' not in df.columns:
            raise ValueError("DataFrame must contain 'lapdist' column")

        track_length = self.config.track_length_meters.get(track_name.lower(), 5000)

        lap_boundaries = []
        lap_start_idx = 0

        for i in range(1, len(df)):
            # Detect wraparound: large negative change in lapdist
            if df['lapdist'].iloc[i] < df['lapdist'].iloc[i-1] - (track_length * 0.5):
                # Lap completed
                lap_boundaries.append((lap_start_idx, i-1))
                lap_start_idx = i

        # Add final lap
        if lap_start_idx < len(df) - 1:
            lap_boundaries.append((lap_start_idx, len(df) - 1))

        return lap_boundaries

    def smooth_gps_kalman(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Kalman filter to smooth GPS coordinates

        Args:
            df: DataFrame with GPS_Lat and GPS_Long columns

        Returns:
            DataFrame with smoothed GPS coordinates
        """
        # TODO: Implement Kalman filter using pykalman
        # For now, use simple moving average
        df = df.copy()

        if 'GPS_Lat' in df.columns and 'GPS_Long' in df.columns:
            window_size = 5
            df['GPS_Lat_smooth'] = df['GPS_Lat'].rolling(
                window=window_size,
                center=True,
                min_periods=1
            ).mean()
            df['GPS_Long_smooth'] = df['GPS_Long'].rolling(
                window=window_size,
                center=True,
                min_periods=1
            ).mean()

        return df

    def extract_lap_features(
        self,
        df: pd.DataFrame,
        lap_start: int,
        lap_end: int
    ) -> Dict[str, float]:
        """
        Extract features for a single lap

        Args:
            df: Telemetry DataFrame
            lap_start: Start index of lap
            lap_end: End index of lap

        Returns:
            Dictionary of lap features
        """
        lap_data = df.iloc[lap_start:lap_end+1]

        features = {}

        # Basic lap metrics
        if 'meta_time' in lap_data.columns:
            lap_time = (
                lap_data['meta_time'].iloc[-1] -
                lap_data['meta_time'].iloc[0]
            )
            features['lap_time'] = lap_time

        # Speed metrics
        if 'Speed' in lap_data.columns:
            features['avg_speed'] = lap_data['Speed'].mean()
            features['max_speed'] = lap_data['Speed'].max()
            features['speed_variance'] = lap_data['Speed'].var()

        # Throttle metrics
        if 'aps' in lap_data.columns:
            features['avg_throttle'] = lap_data['aps'].mean()
            features['throttle_variance'] = lap_data['aps'].var()

        # Brake metrics
        if 'pbrake_f' in lap_data.columns:
            features['avg_brake_front'] = lap_data['pbrake_f'].mean()
            features['max_brake_front'] = lap_data['pbrake_f'].max()

        # G-force metrics (degradation proxies)
        if 'accy_can' in lap_data.columns:
            features['avg_lateral_g'] = lap_data['accy_can'].abs().mean()
            features['max_lateral_g'] = lap_data['accy_can'].abs().max()

        if 'accx_can' in lap_data.columns:
            features['avg_longitudinal_g'] = lap_data['accx_can'].abs().mean()
            features['max_brake_g'] = lap_data['accx_can'].min()

        # Steering metrics
        if 'Steering_Angle' in lap_data.columns:
            features['avg_steering_abs'] = lap_data['Steering_Angle'].abs().mean()
            features['steering_variance'] = lap_data['Steering_Angle'].var()

        return features


def calculate_degradation_indicators(
    lap_features_history: List[Dict[str, float]]
) -> Dict[str, float]:
    """
    Calculate degradation indicators from lap feature history

    Args:
        lap_features_history: List of feature dictionaries for consecutive laps

    Returns:
        Dictionary of degradation indicators
    """
    if len(lap_features_history) < 3:
        return {"degradation_rate": 0.0, "confidence": 0.0}

    # Extract lap times for trend analysis
    lap_times = [lap['lap_time'] for lap in lap_features_history if 'lap_time' in lap]

    if len(lap_times) < 3:
        return {"degradation_rate": 0.0, "confidence": 0.0}

    # Calculate degradation rate (seconds per lap increase)
    degradation_rate = np.mean(np.diff(lap_times))

    # Check lateral G reduction (grip loss indicator)
    lateral_g_values = [
        lap['avg_lateral_g']
        for lap in lap_features_history
        if 'avg_lateral_g' in lap
    ]

    lateral_g_trend = 0.0
    if len(lateral_g_values) >= 3:
        lateral_g_trend = np.mean(np.diff(lateral_g_values))

    # Check steering variance increase (consistency loss)
    steering_variance = [
        lap['steering_variance']
        for lap in lap_features_history
        if 'steering_variance' in lap
    ]

    steering_trend = 0.0
    if len(steering_variance) >= 3:
        steering_trend = np.mean(np.diff(steering_variance))

    return {
        "degradation_rate": degradation_rate,
        "lateral_g_trend": lateral_g_trend,
        "steering_variance_trend": steering_trend,
        "confidence": min(len(lap_times) / 10.0, 1.0)
    }
