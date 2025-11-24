"""
Race Service - Manages race data and ML model inference
"""

import pandas as pd
from typing import Dict, List, Optional
import logging
import os
from pathlib import Path

from utils.data_loader import BarberDataLoader
from utils.lap_segmentation import LapSegmenter
from utils.feature_engineering import FeatureEngineer
from models.pace_forecaster import PaceForecaster
from models.threat_detector import ThreatDetector
from models.pit_optimizer import PitOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RaceService:
    """
    Service layer for race data processing and ML inference
    """

    def __init__(self, data_dir: Optional[str] = None, model_dir: Optional[str] = None):
        # Read configuration from environment variables
        self.data_dir = data_dir or os.getenv("DATA_DIR", "data/barber")
        self.model_dir = Path(model_dir or os.getenv("MODEL_PATH", "models/trained"))
        self.default_race = os.getenv("DEFAULT_RACE", "R1")
        self.data_mode = os.getenv("DATA_MODE", "sample").lower()

        # Initialize components
        self.data_loader = BarberDataLoader(self.data_dir)
        self.lap_segmenter = LapSegmenter()
        self.feature_engineer = FeatureEngineer()
        self.pace_forecaster = PaceForecaster()
        self.threat_detector = ThreatDetector()
        self.pit_optimizer = PitOptimizer()

        # Cache for processed data
        self.race_data_cache: Dict[str, pd.DataFrame] = {}
        self.lap_features_cache: Dict[str, pd.DataFrame] = {}
        self.vehicles_cache: Dict[str, List[Dict]] = {}

        logger.info(f"RaceService initialized - DATA_MODE: {self.data_mode}, DATA_DIR: {self.data_dir}")

        # Optional: Preload vehicle list on startup to warm cache
        if os.getenv("PRELOAD_VEHICLES", "true").lower() == "true":
            try:
                self.get_available_vehicles()
                logger.info("Preloaded vehicle list on startup")
            except Exception as e:
                logger.warning(f"Failed to preload vehicles: {e}")

    def load_race_data(
        self,
        race: Optional[str] = None,
        vehicle_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load and process race telemetry data
        Uses DATA_MODE environment variable to determine whether to use sample or real data

        Args:
            race: Race identifier ("R1" or "R2"), defaults to DEFAULT_RACE from env
            vehicle_id: Specific vehicle to load

        Returns:
            Wide-format telemetry DataFrame
        """
        race = race or self.default_race
        cache_key = f"{race}_{vehicle_id or 'all'}_{self.data_mode}"

        if cache_key in self.race_data_cache:
            logger.debug(f"Using cached data for {cache_key}")
            return self.race_data_cache[cache_key]

        # Use the new get_telemetry_data method which handles DATA_MODE automatically
        df_long = self.data_loader.get_telemetry_data(
            race=race,
            vehicle_id=vehicle_id,
            num_vehicles=1 if vehicle_id else 5,
            num_laps=20
        )

        if df_long.empty:
            logger.warning(f"No data loaded for {race}")
            return pd.DataFrame()

        # Convert to wide format
        df_wide = self.data_loader.pivot_telemetry_wide(df_long, vehicle_id)

        self.race_data_cache[cache_key] = df_wide
        return df_wide

    def get_available_vehicles(self, race: Optional[str] = None) -> List[Dict]:
        """
        Get list of all available vehicles in the race session

        Args:
            race: Race identifier (defaults to DEFAULT_RACE from env)

        Returns:
            List of dicts with vehicle_id and vehicle_number
        """
        race = race or self.default_race

        # Check cache first
        cache_key = f"{race}_vehicles_{self.data_mode}"
        if hasattr(self, 'vehicles_cache') and cache_key in self.vehicles_cache:
            logger.debug(f"Using cached vehicle list for {cache_key}")
            return self.vehicles_cache[cache_key]

        # Load only vehicle columns for efficiency (not all telemetry data)
        df_vehicles = self.data_loader.get_vehicle_list(race=race)

        if df_vehicles.empty:
            logger.warning(f"No vehicles available for race {race}")
            return []

        # Get unique vehicles
        vehicles = df_vehicles[['vehicle_id', 'vehicle_number']].drop_duplicates()
        vehicles = vehicles.sort_values('vehicle_number')

        vehicle_list = [
            {
                "vehicle_id": row['vehicle_id'],
                "vehicle_number": int(row['vehicle_number'])
            }
            for _, row in vehicles.iterrows()
        ]

        # Cache the result
        if not hasattr(self, 'vehicles_cache'):
            self.vehicles_cache = {}
        self.vehicles_cache[cache_key] = vehicle_list

        logger.info(f"Found {len(vehicle_list)} vehicles in race {race}")
        return vehicle_list

    def get_lap_features(
        self,
        race: Optional[str] = None,
        vehicle_id: str = "GR86-000-0"
    ) -> pd.DataFrame:
        """
        Get engineered features for all laps

        Args:
            race: Race identifier (defaults to DEFAULT_RACE from env)
            vehicle_id: Vehicle to analyze

        Returns:
            DataFrame with engineered lap features
        """
        race = race or self.default_race
        cache_key = f"{race}_{vehicle_id}_features_{self.data_mode}"

        if cache_key in self.lap_features_cache:
            logger.debug(f"Using cached features for {cache_key}")
            return self.lap_features_cache[cache_key]

        # Load telemetry
        df_wide = self.load_race_data(race, vehicle_id)

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
        race: Optional[str] = None
    ) -> List[Dict[str, float]]:
        """
        Predict lap times for next N laps

        Args:
            vehicle_id: Vehicle identifier
            current_lap: Current lap number
            laps_ahead: Number of laps to predict
            race: Race identifier (defaults to DEFAULT_RACE from env)

        Returns:
            List of predictions with lap_number, predicted_time, delta, confidence
        """
        # Get features for recent laps
        features_df = self.get_lap_features(race, vehicle_id)

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
        race: Optional[str] = None
    ) -> Dict:
        """
        Analyze tire degradation for a vehicle

        Args:
            vehicle_id: Vehicle identifier
            current_lap: Current lap number
            race: Race identifier (defaults to DEFAULT_RACE from env)

        Returns:
            Dictionary with degradation analysis
        """
        features_df = self.get_lap_features(race, vehicle_id)

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

    def detect_threat(
        self,
        vehicle_id: str,
        rival_id: str,
        current_lap: int,
        current_gap: float,
        race: Optional[str] = None
    ) -> Dict:
        """
        Detect threat from rival vehicle

        Args:
            vehicle_id: Own vehicle identifier
            rival_id: Rival vehicle identifier
            current_lap: Current lap number
            current_gap: Current gap to rival (seconds)
            race: Race identifier

        Returns:
            Dictionary with threat analysis
        """
        # Get features for both vehicles
        own_features = self.get_lap_features(race, vehicle_id)
        rival_features = self.get_lap_features(race, rival_id)

        if own_features.empty or rival_features.empty:
            logger.warning("Insufficient data for threat detection")
            return {
                "attack_probability": 0.0,
                "current_gap": current_gap,
                "gap_trend": "unknown",
                "laps_until_threat": 999,
                "pace_delta": 0.0,
                "sector_advantages": [],
                "defensive_recommendations": ["Insufficient data"],
                "threat_level": "low",
            }

        # Use threat detector model
        threat = self.threat_detector.analyze_threat(
            own_laps=own_features,
            rival_laps=rival_features,
            current_gap=current_gap,
            current_lap=current_lap,
            lookback_laps=5
        )

        return threat

    def optimize_pit_window(
        self,
        vehicle_id: str,
        current_lap: int,
        current_position: int,
        total_laps: int,
        race: Optional[str] = None
    ) -> Dict:
        """
        Calculate optimal pit window

        Args:
            vehicle_id: Vehicle identifier
            current_lap: Current lap number
            current_position: Current position in race
            total_laps: Total laps in race
            race: Race identifier

        Returns:
            Dictionary with pit window optimization
        """
        # Get lap features
        features_df = self.get_lap_features(race, vehicle_id)

        if features_df.empty:
            logger.warning("Insufficient data for pit optimization")
            return {
                "optimal_window_start": current_lap + 3,
                "optimal_window_end": current_lap + 7,
                "recommended_lap": current_lap + 5,
                "confidence": 0.3,
                "undercut_opportunity": {"gain_seconds": 0.0, "viable": False},
                "overcut_opportunity": {"gain_seconds": 0.0, "viable": False},
                "position_risk": "unknown",
                "traffic_risk": "unknown",
                "reasoning": ["Insufficient data for optimization"],
            }

        # Calculate degradation rate
        degradation_analysis = self.analyze_degradation(vehicle_id, current_lap, race)
        degradation_rate = degradation_analysis.get("degradation_rate", 0.05)

        # Use pit optimizer model
        pit_window = self.pit_optimizer.optimize_pit_window(
            own_laps=features_df,
            current_lap=current_lap,
            current_position=current_position,
            total_laps=total_laps,
            rivals_data=None,  # TODO: Add rival data support
            degradation_rate=degradation_rate
        )

        return pit_window

    def get_current_pace(
        self,
        vehicle_id: str,
        race: Optional[str] = None,
        window_size: int = 5
    ) -> Dict:
        """
        Get current pace metrics for a vehicle

        Args:
            vehicle_id: Vehicle identifier
            race: Race identifier
            window_size: Number of recent laps to average

        Returns:
            Dictionary with current pace metrics
        """
        features_df = self.get_lap_features(race, vehicle_id)

        if features_df.empty or len(features_df) < 2:
            return {
                "vehicle_id": vehicle_id,
                "current_pace": 0.0,
                "average_pace": 0.0,
                "best_lap": 0.0,
                "pace_trend": "unknown",
                "consistency": 0.0,
            }

        # Get recent laps
        recent_laps = features_df.tail(window_size)

        # Calculate metrics
        current_pace = recent_laps['lap_time'].iloc[-1] if len(recent_laps) > 0 else 0.0
        average_pace = recent_laps['lap_time'].mean()
        best_lap = features_df['lap_time'].min()
        pace_std = recent_laps['lap_time'].std()

        # Determine trend
        if len(recent_laps) >= 3:
            first_half = recent_laps['lap_time'].iloc[:len(recent_laps)//2].mean()
            second_half = recent_laps['lap_time'].iloc[len(recent_laps)//2:].mean()

            if second_half < first_half - 0.1:
                trend = "improving"
            elif second_half > first_half + 0.1:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Consistency score (lower std = more consistent)
        consistency = max(0.0, min(1.0, 1.0 - (pace_std / 1.0))) if pace_std else 0.9

        return {
            "vehicle_id": vehicle_id,
            "current_pace": float(current_pace),
            "average_pace": float(average_pace),
            "best_lap": float(best_lap),
            "pace_trend": trend,
            "consistency": float(consistency),
            "recent_laps": window_size,
        }


# Singleton instance
_race_service = None

def get_race_service() -> RaceService:
    """Get or create singleton race service"""
    global _race_service
    if _race_service is None:
        _race_service = RaceService()
    return _race_service
