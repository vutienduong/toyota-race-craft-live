"""
Lap segmentation for RaceCraft Live
Detects lap boundaries using lapdist wraparound method
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LapSegmenter:
    """
    Segment telemetry data into individual laps using lapdist wraparound detection

    Critical: Do NOT trust the 'lap' column in telemetry data - it may be corrupted.
    Instead, detect laps by analyzing Laptrigger_lapdist_dls wraparound.
    """

    def __init__(
        self,
        track_length: float = 2380.0,
        wraparound_threshold: float = 100.0
    ):
        """
        Args:
            track_length: Track length in meters (Barber = 2380m)
            wraparound_threshold: Distance threshold for wraparound detection (meters)
        """
        self.track_length = track_length
        self.wraparound_threshold = wraparound_threshold

    def detect_lap_boundaries(
        self,
        df: pd.DataFrame,
        lapdist_col: str = "Laptrigger_lapdist_dls"
    ) -> List[Tuple[int, int]]:
        """
        Detect lap boundaries using lapdist wraparound

        Algorithm:
        1. Sort by meta_time
        2. Find where lapdist drops from high value to low value
        3. These are lap completion points

        Args:
            df: Telemetry DataFrame (must be sorted by meta_time)
            lapdist_col: Name of lap distance column

        Returns:
            List of (start_idx, end_idx) tuples for each lap
        """
        if lapdist_col not in df.columns:
            logger.error(f"Column '{lapdist_col}' not found in DataFrame")
            return []

        # Ensure sorted by time
        df = df.sort_values('meta_time').reset_index(drop=True)

        lapdist = df[lapdist_col].values
        lap_boundaries = []
        current_lap_start = 0

        # Detect wraparound: large negative change in lapdist
        for i in range(1, len(lapdist)):
            delta = lapdist[i] - lapdist[i - 1]

            # Wraparound detected: went from end of track back to start
            if delta < -self.wraparound_threshold:
                lap_boundaries.append((current_lap_start, i - 1))
                current_lap_start = i

        # Add final lap
        if current_lap_start < len(df) - 1:
            lap_boundaries.append((current_lap_start, len(df) - 1))

        logger.info(f"Detected {len(lap_boundaries)} laps using lapdist wraparound")

        return lap_boundaries

    def segment_telemetry_by_laps(
        self,
        df: pd.DataFrame,
        vehicle_id: Optional[str] = None
    ) -> Dict[int, pd.DataFrame]:
        """
        Segment telemetry into separate DataFrames for each lap

        Args:
            df: Wide-format telemetry DataFrame
            vehicle_id: Optional vehicle filter

        Returns:
            Dictionary mapping lap_number → DataFrame
        """
        if vehicle_id:
            df = df[df['vehicle_id'] == vehicle_id].copy()

        # Detect lap boundaries
        boundaries = self.detect_lap_boundaries(df)

        # Extract each lap
        laps = {}
        for lap_num, (start, end) in enumerate(boundaries, start=1):
            lap_df = df.iloc[start:end + 1].copy()
            lap_df['detected_lap'] = lap_num
            laps[lap_num] = lap_df

        logger.info(f"Segmented telemetry into {len(laps)} laps")

        return laps

    def calculate_lap_features(
        self,
        lap_df: pd.DataFrame,
        lap_number: int
    ) -> Dict[str, float]:
        """
        Extract features for a single lap

        Args:
            lap_df: DataFrame containing one lap's telemetry
            lap_number: Lap number

        Returns:
            Dictionary of lap features
        """
        if lap_df.empty:
            return {}

        features = {
            "lap_number": lap_number,
            "lap_time": (lap_df['meta_time'].max() - lap_df['meta_time'].min()),
        }

        # Speed metrics
        if 'speed' in lap_df.columns:
            features['avg_speed'] = lap_df['speed'].mean()
            features['max_speed'] = lap_df['speed'].max()
            features['min_speed'] = lap_df['speed'].min()
            features['speed_variance'] = lap_df['speed'].var()

        # Throttle metrics (using aps instead of ath)
        if 'aps' in lap_df.columns:
            features['avg_throttle'] = lap_df['aps'].mean()
            features['throttle_variance'] = lap_df['aps'].var()
            features['full_throttle_pct'] = (lap_df['aps'] > 95).sum() / len(lap_df)

        # Brake metrics
        if 'pbrake_f' in lap_df.columns:
            features['avg_brake_front'] = lap_df['pbrake_f'].mean()
            features['max_brake_front'] = lap_df['pbrake_f'].max()
            features['braking_points'] = (lap_df['pbrake_f'] > 10).sum()

        # Lateral G (grip indicator)
        if 'accy_can' in lap_df.columns:
            features['avg_lateral_g'] = lap_df['accy_can'].abs().mean()
            features['max_lateral_g'] = lap_df['accy_can'].abs().max()

        # Longitudinal G (braking quality)
        if 'accx_can' in lap_df.columns:
            features['avg_longitudinal_g'] = lap_df['accx_can'].abs().mean()
            features['max_brake_g'] = lap_df['accx_can'].min()  # Negative = braking

        # Steering metrics
        if 'Steering_Angle' in lap_df.columns:
            features['avg_steering_abs'] = lap_df['Steering_Angle'].abs().mean()
            features['steering_variance'] = lap_df['Steering_Angle'].var()
            features['max_steering_angle'] = lap_df['Steering_Angle'].abs().max()

        # RPM metrics
        if 'nmot' in lap_df.columns:
            features['avg_rpm'] = lap_df['nmot'].mean()
            features['max_rpm'] = lap_df['nmot'].max()

        return features

    def extract_sector_times(
        self,
        lap_df: pd.DataFrame,
        sector_boundaries: Dict[int, float]
    ) -> Dict[str, float]:
        """
        Calculate sector times based on lapdist boundaries

        Args:
            lap_df: Single lap DataFrame
            sector_boundaries: Dict mapping sector → distance threshold
                e.g., {1: 800, 2: 1600, 3: 2380}

        Returns:
            Dict with sector_1_time, sector_2_time, sector_3_time
        """
        if 'Laptrigger_lapdist_dls' not in lap_df.columns:
            return {}

        lap_df = lap_df.sort_values('meta_time')
        lapdist = lap_df['Laptrigger_lapdist_dls'].values
        time = lap_df['meta_time'].values

        sector_times = {}
        prev_boundary = 0
        prev_time = time[0]

        for sector_num, boundary in sorted(sector_boundaries.items()):
            # Find first index where lapdist exceeds boundary
            sector_end_idx = np.where(lapdist >= boundary)[0]

            if len(sector_end_idx) > 0:
                sector_end_time = time[sector_end_idx[0]]
                sector_times[f'sector_{sector_num}_time'] = sector_end_time - prev_time
                prev_time = sector_end_time
            else:
                sector_times[f'sector_{sector_num}_time'] = None

        return sector_times

    def validate_lap_count(
        self,
        detected_laps: int,
        expected_laps: int,
        tolerance: int = 2
    ) -> bool:
        """
        Validate detected lap count against expected

        Args:
            detected_laps: Number of laps detected by algorithm
            expected_laps: Expected number from lap_time.csv
            tolerance: Acceptable difference

        Returns:
            True if within tolerance
        """
        diff = abs(detected_laps - expected_laps)
        is_valid = diff <= tolerance

        if is_valid:
            logger.info(f"✓ Lap count validation passed: {detected_laps} laps")
        else:
            logger.warning(
                f"⚠ Lap count mismatch: detected {detected_laps}, "
                f"expected {expected_laps} (diff: {diff})"
            )

        return is_valid


# Example usage
if __name__ == "__main__":
    from data_loader import BarberDataLoader

    # Load sample data
    loader = BarberDataLoader()
    df_long = loader.generate_sample_data(num_vehicles=2, num_laps=5)
    df_wide = loader.pivot_telemetry_wide(df_long, vehicle_id="GR86-000-0")

    # Segment laps
    segmenter = LapSegmenter(track_length=2380)
    laps = segmenter.segment_telemetry_by_laps(df_wide)

    print(f"Detected {len(laps)} laps")

    # Extract features for each lap
    for lap_num, lap_df in laps.items():
        features = segmenter.calculate_lap_features(lap_df, lap_num)
        print(f"\nLap {lap_num}: {features.get('lap_time', 0):.2f}s")
        print(f"  Avg Speed: {features.get('avg_speed', 0):.1f} km/h")
        print(f"  Max Lateral G: {features.get('max_lateral_g', 0):.2f}g")
