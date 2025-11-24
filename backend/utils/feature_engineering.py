"""
Feature engineering for ML models
Extracts pace, degradation, and threat detection features
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Extract ML-ready features from lap telemetry"""

    def __init__(self):
        self.feature_names = []

    def engineer_pace_features(
        self,
        lap_features: List[Dict[str, float]],
        window_size: int = 5
    ) -> pd.DataFrame:
        """
        Create features for pace forecasting model

        Args:
            lap_features: List of lap feature dictionaries
            window_size: Number of laps for rolling features

        Returns:
            DataFrame with pace forecasting features
        """
        df = pd.DataFrame(lap_features)

        if df.empty or len(df) < window_size:
            return df

        # Convert lap_time from timedelta to seconds for numeric operations
        if pd.api.types.is_timedelta64_dtype(df['lap_time']):
            df['lap_time'] = df['lap_time'].dt.total_seconds()

        # Rolling averages (last N laps)
        df['lap_time_rolling_mean'] = df['lap_time'].rolling(window_size, min_periods=1).mean()
        df['lap_time_rolling_std'] = df['lap_time'].rolling(window_size, min_periods=1).std()

        # Pace trend (linear regression slope over last N laps)
        def calculate_trend(series):
            if len(series) < 2:
                return 0
            x = np.arange(len(series))
            slope, _, _, _, _ = stats.linregress(x, series)
            return slope

        df['pace_trend_slope'] = df['lap_time'].rolling(window_size, min_periods=2).apply(
            calculate_trend, raw=False
        )

        # Delta to personal best
        df['delta_to_best'] = df['lap_time'] - df['lap_time'].min()

        # Lap-over-lap change
        df['lap_time_delta'] = df['lap_time'].diff()

        # Speed variance trend (consistency)
        df['speed_variance_trend'] = df['speed_variance'].diff()

        # Throttle discipline trend
        df['throttle_variance_trend'] = df['throttle_variance'].diff()

        # Lateral grip trend (degradation proxy)
        df['lateral_g_trend'] = df['avg_lateral_g'].diff()

        # Brake stability
        df['brake_variance'] = df['max_brake_front'] - df['avg_brake_front']

        logger.info(f"Engineered pace features: {df.shape[1]} columns, {len(df)} laps")

        return df

    def engineer_degradation_features(
        self,
        lap_features: List[Dict[str, float]],
        baseline_laps: int = 3
    ) -> pd.DataFrame:
        """
        Create features for tire degradation detection

        Args:
            lap_features: List of lap feature dictionaries
            baseline_laps: Number of initial laps for baseline

        Returns:
            DataFrame with degradation indicators
        """
        df = pd.DataFrame(lap_features)

        if df.empty or len(df) < baseline_laps:
            return df

        # Convert lap_time from timedelta to seconds if needed
        if 'lap_time' in df.columns and pd.api.types.is_timedelta64_dtype(df['lap_time']):
            df['lap_time'] = df['lap_time'].dt.total_seconds()

        # Calculate baseline metrics (average of first N laps)
        baseline = df.head(baseline_laps).mean()

        # Degradation indicators (% change from baseline)
        if 'avg_lateral_g' in df.columns:
            df['lateral_g_degradation'] = (
                (df['avg_lateral_g'] - baseline['avg_lateral_g']) / baseline['avg_lateral_g'] * 100
            )

        if 'avg_steering_abs' in df.columns:
            df['steering_increase'] = (
                (df['avg_steering_abs'] - baseline['avg_steering_abs']) / baseline['avg_steering_abs'] * 100
            )

        if 'max_brake_g' in df.columns:
            df['brake_point_shift'] = (
                (df['max_brake_g'] - baseline['max_brake_g']) / abs(baseline['max_brake_g']) * 100
            )

        if 'throttle_variance' in df.columns:
            df['throttle_hesitation'] = (
                (df['throttle_variance'] - baseline['throttle_variance']) / baseline['throttle_variance'] * 100
            )

        # Overall degradation score (weighted average)
        degradation_components = []
        weights = []

        if 'lateral_g_degradation' in df.columns:
            degradation_components.append(-df['lateral_g_degradation'])  # Negative = degraded
            weights.append(0.4)  # Lateral grip is most important

        if 'steering_increase' in df.columns:
            degradation_components.append(df['steering_increase'])  # Positive = degraded
            weights.append(0.3)

        if 'throttle_hesitation' in df.columns:
            degradation_components.append(df['throttle_hesitation'])  # Positive = degraded
            weights.append(0.3)

        if degradation_components:
            df['degradation_score'] = np.average(degradation_components, axis=0, weights=weights)
        else:
            df['degradation_score'] = 0

        # Classify degradation severity
        df['degradation_severity'] = pd.cut(
            df['degradation_score'],
            bins=[-np.inf, 5, 10, np.inf],
            labels=['green', 'yellow', 'red']
        )

        logger.info(f"Engineered degradation features for {len(df)} laps")

        return df

    def engineer_threat_features(
        self,
        own_lap_features: List[Dict[str, float]],
        rival_lap_features: List[Dict[str, float]]
    ) -> pd.DataFrame:
        """
        Create features for threat detection

        Args:
            own_lap_features: Our car's lap features
            rival_lap_features: Rival car's lap features

        Returns:
            DataFrame with threat indicators
        """
        df_own = pd.DataFrame(own_lap_features)
        df_rival = pd.DataFrame(rival_lap_features)

        if df_own.empty or df_rival.empty:
            return pd.DataFrame()

        # Align lap numbers
        df_merged = df_own.merge(
            df_rival,
            on='lap_number',
            suffixes=('_own', '_rival'),
            how='inner'
        )

        # Pace delta (negative = rival faster)
        df_merged['pace_delta'] = df_merged['lap_time_own'] - df_merged['lap_time_rival']

        # Closing rate (pace delta trend)
        df_merged['closing_rate'] = -df_merged['pace_delta'].diff()

        # Speed advantage in corners (proxy for sector advantage)
        df_merged['min_speed_delta'] = df_merged['min_speed_own'] - df_merged['min_speed_rival']

        # Lateral G advantage (cornering speed)
        df_merged['lateral_g_delta'] = df_merged['max_lateral_g_own'] - df_merged['max_lateral_g_rival']

        # Attack probability (simple heuristic)
        # Higher probability if:
        # 1. Rival is faster (negative pace_delta)
        # 2. Gap is closing (positive closing_rate)
        # 3. Rival has corner speed advantage
        def calculate_attack_probability(row):
            prob = 0

            # Rival faster
            if row.get('pace_delta', 0) < 0:
                prob += 30

            # Gap closing
            if row.get('closing_rate', 0) > 0.1:
                prob += 40

            # Corner speed advantage
            if row.get('lateral_g_delta', 0) < 0:
                prob += 20

            # DRS/slipstream zone (if gap < 1.0s cumulative)
            if abs(row.get('pace_delta', 0)) < 1.0:
                prob += 10

            return min(100, prob)

        df_merged['attack_probability'] = df_merged.apply(calculate_attack_probability, axis=1)

        logger.info(f"Engineered threat features for {len(df_merged)} laps")

        return df_merged

    def create_ml_dataset(
        self,
        lap_features: List[Dict[str, float]],
        target_col: str = 'lap_time',
        lookback: int = 5,
        lookahead: int = 1
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create supervised learning dataset for pace forecasting

        Args:
            lap_features: List of lap feature dictionaries
            target_col: Column to predict
            lookback: Number of previous laps to use as features
            lookahead: Number of laps ahead to predict

        Returns:
            (X, y) tuple of features and targets
        """
        df = pd.DataFrame(lap_features)

        if df.empty or len(df) < lookback + lookahead:
            return pd.DataFrame(), pd.Series()

        X_list = []
        y_list = []

        # Create sliding windows
        for i in range(len(df) - lookback - lookahead + 1):
            # Features: last N laps
            window = df.iloc[i:i + lookback]

            # Flatten features
            features = {}
            for lag in range(lookback):
                lap_data = window.iloc[lag]
                for col in ['lap_time', 'avg_speed', 'throttle_variance', 'avg_lateral_g']:
                    if col in lap_data:
                        features[f'{col}_lag_{lag}'] = lap_data[col]

            X_list.append(features)

            # Target: lap time N steps ahead
            target_idx = i + lookback + lookahead - 1
            y_list.append(df.iloc[target_idx][target_col])

        X = pd.DataFrame(X_list)
        y = pd.Series(y_list)

        logger.info(f"Created ML dataset: X={X.shape}, y={len(y)}")

        return X, y


# Example usage
if __name__ == "__main__":
    # Sample lap features
    sample_laps = [
        {"lap_number": i, "lap_time": 90 + i * 0.05 + np.random.normal(0, 0.2),
         "avg_speed": 120 - i * 0.5, "avg_lateral_g": 1.5 - i * 0.02,
         "throttle_variance": 10 + i * 0.5, "avg_steering_abs": 50 + i * 2}
        for i in range(1, 11)
    ]

    engineer = FeatureEngineer()

    # Pace features
    pace_df = engineer.engineer_pace_features(sample_laps)
    print("Pace Features:")
    print(pace_df[['lap_number', 'lap_time', 'pace_trend_slope', 'delta_to_best']].head())

    # Degradation features
    deg_df = engineer.engineer_degradation_features(sample_laps)
    print("\nDegradation Features:")
    print(deg_df[['lap_number', 'degradation_score', 'degradation_severity']].tail())

    # ML dataset
    X, y = engineer.create_ml_dataset(sample_laps, lookback=5, lookahead=1)
    print(f"\nML Dataset: X={X.shape}, y={len(y)}")
