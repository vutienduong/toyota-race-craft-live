"""
Threat Detection Model
Analyzes competitor behavior to predict attack probability
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatDetector:
    """
    Detect and analyze threats from competing vehicles
    Uses pace delta, gap trends, and sector performance to predict attacks
    """

    def __init__(self):
        self.threat_threshold_pace = 0.3  # seconds per lap faster = threat
        self.threat_threshold_gap = 2.0   # closing gap < 2s = threat
        self.attack_probability_weights = {
            "pace_advantage": 0.35,
            "gap_closing": 0.30,
            "sector_advantage": 0.25,
            "consistency": 0.10,
        }

    def analyze_threat(
        self,
        own_laps: pd.DataFrame,
        rival_laps: pd.DataFrame,
        current_gap: float,
        current_lap: int,
        lookback_laps: int = 5
    ) -> Dict:
        """
        Analyze threat level from a rival vehicle

        Args:
            own_laps: DataFrame with own vehicle lap features
            rival_laps: DataFrame with rival vehicle lap features
            current_gap: Current time gap to rival (seconds)
            current_lap: Current lap number
            lookback_laps: Number of recent laps to analyze

        Returns:
            Dictionary with threat analysis
        """
        # Get recent laps for analysis
        own_recent = own_laps[own_laps['lap_number'] <= current_lap].tail(lookback_laps)
        rival_recent = rival_laps[rival_laps['lap_number'] <= current_lap].tail(lookback_laps)

        if len(own_recent) < 3 or len(rival_recent) < 3:
            logger.warning("Not enough lap data for threat analysis")
            return self._empty_threat_response()

        # Calculate threat factors
        pace_advantage = self._calculate_pace_advantage(own_recent, rival_recent)
        gap_closing_rate = self._calculate_gap_closing_rate(current_gap, lookback_laps)
        sector_advantages = self._calculate_sector_advantages(own_recent, rival_recent)
        consistency_score = self._calculate_consistency_score(rival_recent)

        # Calculate overall attack probability
        attack_probability = self._calculate_attack_probability(
            pace_advantage,
            gap_closing_rate,
            sector_advantages,
            consistency_score,
            current_gap
        )

        # Predict laps until attack range
        laps_until_attack = self._predict_laps_until_attack(
            current_gap, gap_closing_rate
        )

        # Generate defensive recommendations
        recommendations = self._generate_recommendations(
            attack_probability, sector_advantages, pace_advantage
        )

        return {
            "attack_probability": float(attack_probability),
            "current_gap": float(current_gap),
            "gap_trend": "closing" if gap_closing_rate > 0 else "stable" if gap_closing_rate == 0 else "opening",
            "laps_until_threat": int(laps_until_attack) if laps_until_attack > 0 else 0,
            "pace_delta": float(pace_advantage),
            "sector_advantages": sector_advantages,
            "defensive_recommendations": recommendations,
            "threat_level": self._categorize_threat_level(attack_probability),
        }

    def _calculate_pace_advantage(
        self, own_laps: pd.DataFrame, rival_laps: pd.DataFrame
    ) -> float:
        """Calculate rival's pace advantage over recent laps"""
        own_avg_pace = own_laps['lap_time'].mean()
        rival_avg_pace = rival_laps['lap_time'].mean()

        # Positive value = rival is faster
        pace_delta = own_avg_pace - rival_avg_pace
        return pace_delta

    def _calculate_gap_closing_rate(
        self, current_gap: float, lookback_laps: int
    ) -> float:
        """
        Calculate how quickly rival is closing the gap

        For now using simplified calculation
        In production, would track historical gap data
        """
        # Simplified: estimate based on current gap and threat threshold
        if current_gap < self.threat_threshold_gap:
            return 0.5  # Actively closing
        elif current_gap < 5.0:
            return 0.2  # Slowly closing
        else:
            return 0.0  # Not closing

    def _calculate_sector_advantages(
        self, own_laps: pd.DataFrame, rival_laps: pd.DataFrame
    ) -> List[Dict[str, any]]:
        """
        Calculate rival's advantages in specific sectors/corners

        Returns list of sectors where rival is faster
        """
        sector_advantages = []

        # Sector 1 analysis (based on speed variance)
        own_s1_speed = own_laps['avg_speed'].mean()
        rival_s1_speed = rival_laps['avg_speed'].mean()

        if rival_s1_speed > own_s1_speed + 2:  # 2 km/h advantage
            sector_advantages.append({
                "sector": "Sector 1",
                "advantage_seconds": 0.15,
                "type": "straight_speed"
            })

        # Sector 2 analysis (based on lateral G - cornering)
        own_corner = own_laps.get('avg_lateral_g', pd.Series([1.0])).mean()
        rival_corner = rival_laps.get('avg_lateral_g', pd.Series([1.0])).mean()

        if rival_corner > own_corner + 0.05:
            sector_advantages.append({
                "sector": "Sector 2",
                "advantage_seconds": 0.12,
                "type": "cornering_speed"
            })

        # Sector 3 analysis (based on braking performance)
        own_brake = own_laps.get('brake_variance', pd.Series([5.0])).mean()
        rival_brake = rival_laps.get('brake_variance', pd.Series([5.0])).mean()

        if rival_brake < own_brake - 1.0:  # More consistent braking
            sector_advantages.append({
                "sector": "Sector 3",
                "advantage_seconds": 0.10,
                "type": "braking_stability"
            })

        return sector_advantages

    def _calculate_consistency_score(self, rival_laps: pd.DataFrame) -> float:
        """
        Calculate rival's consistency score (0-1)
        Higher score = more consistent = more predictable threat
        """
        if len(rival_laps) < 2:
            return 0.5

        lap_time_std = rival_laps['lap_time'].std()

        # Convert to consistency score (lower std = higher consistency)
        # Assume typical std is around 0.5 seconds
        consistency = max(0.0, min(1.0, 1.0 - (lap_time_std / 1.0)))

        return consistency

    def _calculate_attack_probability(
        self,
        pace_advantage: float,
        gap_closing_rate: float,
        sector_advantages: List[Dict],
        consistency_score: float,
        current_gap: float
    ) -> float:
        """
        Calculate overall attack probability using weighted factors
        Returns probability from 0.0 to 1.0
        """
        weights = self.attack_probability_weights

        # Pace advantage factor (0-1)
        pace_factor = min(1.0, max(0.0, pace_advantage / 1.0))

        # Gap closing factor (0-1)
        gap_factor = min(1.0, max(0.0, gap_closing_rate))

        # Sector advantage factor (0-1)
        sector_factor = min(1.0, len(sector_advantages) / 3.0)

        # Consistency factor (already 0-1)
        consistency_factor = consistency_score

        # Weighted sum
        probability = (
            weights["pace_advantage"] * pace_factor +
            weights["gap_closing"] * gap_factor +
            weights["sector_advantage"] * sector_factor +
            weights["consistency"] * consistency_factor
        )

        # Apply gap proximity multiplier
        if current_gap < 1.0:
            probability *= 1.5  # Imminent threat
        elif current_gap < 2.0:
            probability *= 1.2  # Close threat

        return min(1.0, probability)

    def _predict_laps_until_attack(
        self, current_gap: float, gap_closing_rate: float
    ) -> int:
        """
        Predict number of laps until rival is in attack range (< 1 second)
        """
        if gap_closing_rate <= 0:
            return 999  # Not closing gap

        attack_threshold = 1.0  # seconds
        gap_to_close = current_gap - attack_threshold

        if gap_to_close <= 0:
            return 0  # Already in attack range

        # Estimate laps (assuming closing rate per lap)
        laps = int(np.ceil(gap_to_close / (gap_closing_rate * 0.5)))

        return min(laps, 999)

    def _generate_recommendations(
        self,
        attack_probability: float,
        sector_advantages: List[Dict],
        pace_advantage: float
    ) -> List[str]:
        """Generate defensive driving recommendations"""
        recommendations = []

        if attack_probability > 0.7:
            recommendations.append("High threat - prepare defensive line")
            recommendations.append("Focus on corner exits to maintain speed")

        if pace_advantage > 0.5:
            recommendations.append("Rival has significant pace advantage")
            recommendations.append("Consider pit strategy adjustment")

        for sector in sector_advantages:
            if sector["type"] == "straight_speed":
                recommendations.append(f"Defend inside line on straights in {sector['sector']}")
            elif sector["type"] == "cornering_speed":
                recommendations.append(f"Tighten racing line in {sector['sector']}")
            elif sector["type"] == "braking_stability":
                recommendations.append(f"Late braking defense in {sector['sector']}")

        if not recommendations:
            recommendations.append("Maintain current pace and strategy")

        return recommendations[:3]  # Return top 3 recommendations

    def _categorize_threat_level(self, attack_probability: float) -> str:
        """Categorize threat level based on probability"""
        if attack_probability >= 0.7:
            return "high"
        elif attack_probability >= 0.4:
            return "medium"
        else:
            return "low"

    def _empty_threat_response(self) -> Dict:
        """Return empty threat response when insufficient data"""
        return {
            "attack_probability": 0.0,
            "current_gap": 0.0,
            "gap_trend": "unknown",
            "laps_until_threat": 999,
            "pace_delta": 0.0,
            "sector_advantages": [],
            "defensive_recommendations": ["Insufficient data for threat analysis"],
            "threat_level": "low",
        }


# Example usage
if __name__ == "__main__":
    detector = ThreatDetector()

    # Simulate lap data
    own_laps = pd.DataFrame({
        'lap_number': range(1, 11),
        'lap_time': [90.5, 90.3, 90.4, 90.6, 90.5, 90.4, 90.5, 90.6, 90.7, 90.6],
        'avg_speed': [125] * 10,
        'avg_lateral_g': [1.2] * 10,
        'brake_variance': [5.0] * 10,
    })

    rival_laps = pd.DataFrame({
        'lap_number': range(1, 11),
        'lap_time': [91.0, 90.5, 90.3, 90.2, 90.1, 90.0, 89.9, 89.8, 89.8, 89.7],
        'avg_speed': [127] * 10,
        'avg_lateral_g': [1.25] * 10,
        'brake_variance': [4.0] * 10,
    })

    threat = detector.analyze_threat(own_laps, rival_laps, current_gap=3.5, current_lap=10)

    print("Threat Analysis:")
    print(f"Attack Probability: {threat['attack_probability']:.2%}")
    print(f"Threat Level: {threat['threat_level']}")
    print(f"Laps Until Threat: {threat['laps_until_threat']}")
    print(f"Recommendations: {threat['defensive_recommendations']}")
