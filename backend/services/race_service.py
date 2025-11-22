"""
Race Service - Manages race data and ML model inference
"""

import pandas as pd
from typing import Dict, List, Optional
import logging
from pathlib import Path

from utils.data_loader import BarberDataLoader
from utils.lap_segmentation import LapSegmenter
from utils.feature_engineering import FeatureEngineer
from models.pace_forecaster import PaceForecaster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RaceService:
    """
    Service layer for race data processing and ML inference
    """

    def __init__(self, data_dir: str = "data/barber", model_dir: str = "models/trained"):
        self.data_loader = BarberDataLoader(data_dir)
        self.lap_segmenter = LapSegmenter()
        self.feature_engineer = FeatureEngineer()
        self.pace_forecaster = PaceForecaster()

        self.model_dir = Path(model_dir)

        # Cache for processed data
        self.race_data_cache: Dict[str, pd.DataFrame] = {}
        self.lap_features_cache: Dict[str, pd.DataFrame] = {}

    def load_race_data(
        self,
        race: str = "R1",
        vehicle_id: Optional[str] = None,
        use_sample: bool = True
    ) -> pd.DataFrame:
        """
        Load and process race telemetry data

        Args:
            race: Race identifier ("R1" or "R2")
            vehicle_id: Specific vehicle to load
            use_sample: If True, generate sample data (for testing without real files)

        Returns:
            Wide-format telemetry DataFrame
        """
        cache_key = f"{race}_{vehicle_id or 'all'}"

        if cache_key in self.race_data_cache:
            return self.race_data_cache[cache_key]

        if use_sample:
            logger.info("Using sample data for testing")
            df_long = self.data_loader.generate_sample_data(
                num_vehicles=1 if vehicle_id else 5,
                num_laps=20
            )
        else:
            df_long = self.data_loader.load_telemetry_long(race)

        if df_long.empty:
            logger.warning(f"No data loaded for {race}")
            return pd.DataFrame()

        # Convert to wide format
        df_wide = self.data_loader.pivot_telemetry_wide(df_long, vehicle_id)

        self.race_data_cache[cache_key] = df_wide
        return df_wide

    def get_lap_features(
        self,
        race: str = "R1",
        vehicle_id: str = "GR86-000-0",
        use_sample: bool = True
    ) -> pd.DataFrame:
        """
        Get engineered features for all laps

        Args:
            race: Race identifier
            vehicle_id: Vehicle to analyze
            use_sample: Use sample data if True

        Returns:
            DataFrame with engineered lap features
        """
        cache_key = f"{race}_{vehicle_id}_features"

        if cache_key in self.lap_features_cache:
            return self.lap_features_cache[cache_key]

        # Load telemetry
        df_wide = self.load_race_data(race, vehicle_id, use_sample)

        if df_wide.empty:
            return pd.DataFrame()

        # Segment into laps
        laps = self.lap_segmenter.segment_telemetry_by_laps(df_wide, vehicle_id)

        # Extract features for each lap
        lap_features_list = []
        for lap_num, lap_df in laps.items():
            features = self.lap_segmenter.calculate_lap_features(lap_df, lap_num)
            lap_features_list.append(features)

        # Engineer features
        features_df = self.feature_engineer.engineer_pace_features(lap_features_list)

        self.lap_features_cache[cache_key] = features_df
        return features_df

    def predict_pace(
        self,
        vehicle_id: str,
        current_lap: int,
        laps_ahead: int = 5,
        race: str = "R1"
    ) -> List[Dict[str, float]]:
        """
        Predict lap times for next N laps

        Args:
            vehicle_id: Vehicle identifier
            current_lap: Current lap number
            laps_ahead: Number of laps to predict
            race: Race identifier

        Returns:
            List of predictions with lap_number, predicted_time, delta, confidence
        """
        # Get features for recent laps
        features_df = self.get_lap_features(race, vehicle_id, use_sample=True)

        if features_df.empty or len(features_df) < 5:
            logger.warning("Not enough lap data for prediction")
            return []

        # Get recent laps (up to current lap)
        recent_laps = features_df[features_df['lap_number'] <= current_lap].tail(10)

        # Train model if not already trained (using available data)
        if self.pace_forecaster.model is None:
            logger.info("Training pace forecaster on available data...")
            X, y = self.pace_forecaster.prepare_features(features_df, lookback=5, lookahead=1)

            if not X.empty:
                self.pace_forecaster.train(X, y)
            else:
                logger.error("Cannot train model: insufficient data")
                return []

        # Make predictions
        predictions = self.pace_forecaster.predict(recent_laps, laps_ahead=laps_ahead)

        return predictions

    def analyze_degradation(
        self,
        vehicle_id: str,
        current_lap: int,
        race: str = "R1"
    ) -> Dict:
        """
        Analyze tire degradation for a vehicle

        Args:
            vehicle_id: Vehicle identifier
            current_lap: Current lap number
            race: Race identifier

        Returns:
            Dictionary with degradation analysis
        """
        features_df = self.get_lap_features(race, vehicle_id, use_sample=True)

        if features_df.empty:
            return {}

        # Get degradation features
        deg_df = self.feature_engineer.engineer_degradation_features(
            features_df.to_dict('records')
        )

        # Get current lap data
        current = deg_df[deg_df['lap_number'] == current_lap]

        if current.empty:
            return {}

        current_row = current.iloc[0]

        # Build degradation curve (last 10 laps)
        recent = deg_df[deg_df['lap_number'] <= current_lap].tail(10)
        curve = []

        for _, row in recent.iterrows():
            curve.append({
                "lap": int(row['lap_number']),
                "delta_seconds": float(row.get('lap_time', 0) - deg_df['lap_time'].min()),
                "severity": float(row.get('degradation_score', 0) / 100.0)
            })

        # Determine primary causes
        causes = []

        if current_row.get('lateral_g_degradation', 0) < -5:
            causes.append({
                "cause_type": "lateral_grip_loss",
                "confidence": 0.78,
                "indicators": ["Reduced lateral G in corners", "Understeering detected"]
            })

        if current_row.get('steering_increase', 0) > 10:
            causes.append({
                "cause_type": "understeer",
                "confidence": 0.65,
                "indicators": ["Increased steering angle", "Compensation for grip loss"]
            })

        # Determine stint health
        deg_score = current_row.get('degradation_score', 0)
        if deg_score < 5:
            health = "optimal"
        elif deg_score < 10:
            health = "degrading"
        else:
            health = "critical"

        return {
            "degradation_curve": curve,
            "degradation_rate": float(current_row.get('pace_trend_slope', 0)),
            "primary_causes": causes,
            "stint_health": health,
            "recommended_action": "Consider pit window in next 2-3 laps" if health == "critical" else "Monitor closely"
        }


# Singleton instance
_race_service = None

def get_race_service() -> RaceService:
    """Get or create singleton race service"""
    global _race_service
    if _race_service is None:
        _race_service = RaceService()
    return _race_service
