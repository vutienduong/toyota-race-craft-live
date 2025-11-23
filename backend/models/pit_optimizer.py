"""
Pit Window Optimizer
Calculates optimal pit stop timing based on degradation, traffic, and position
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PitOptimizer:
    """
    Optimize pit stop timing for race strategy
    Considers degradation rate, traffic, undercut/overcut opportunities
    """

    def __init__(self):
        self.pit_loss_seconds = 25.0  # Typical pit stop time loss
        self.fresh_tire_advantage = 1.5  # Seconds per lap with fresh tires
        self.degradation_threshold = 0.15  # Seconds per lap degradation

    def optimize_pit_window(
        self,
        own_laps: pd.DataFrame,
        current_lap: int,
        current_position: int,
        total_laps: int,
        rivals_data: Optional[List[Dict]] = None,
        degradation_rate: float = 0.0
    ) -> Dict:
        """
        Calculate optimal pit window

        Args:
            own_laps: DataFrame with own vehicle lap features
            current_lap: Current lap number
            current_position: Current position in race
            total_laps: Total laps in race
            rivals_data: List of rival vehicle data (optional)
            degradation_rate: Current degradation rate (seconds per lap)

        Returns:
            Dictionary with pit window recommendations
        """
        # Calculate when degradation becomes critical
        critical_lap = self._calculate_degradation_critical_lap(
            own_laps, current_lap, total_laps, degradation_rate
        )

        # Calculate optimal window range
        optimal_window = self._calculate_optimal_window(
            current_lap, critical_lap, total_laps
        )

        # Analyze undercut/overcut opportunities
        undercut_gain, overcut_gain = self._analyze_strategic_opportunities(
            current_lap, current_position, rivals_data, degradation_rate
        )

        # Calculate position risks
        position_risk = self._calculate_position_risk(
            current_position, optimal_window, rivals_data
        )

        # Calculate traffic impact
        traffic_risk = self._calculate_traffic_risk(
            optimal_window, current_position, rivals_data
        )

        # Generate recommendation
        recommendation = self._generate_pit_recommendation(
            optimal_window,
            undercut_gain,
            overcut_gain,
            position_risk,
            traffic_risk,
            current_lap,
            total_laps
        )

        return {
            "optimal_window_start": int(optimal_window[0]),
            "optimal_window_end": int(optimal_window[1]),
            "recommended_lap": int(recommendation["lap"]),
            "confidence": float(recommendation["confidence"]),
            "undercut_opportunity": {
                "gain_seconds": float(undercut_gain),
                "viable": undercut_gain > 2.0,
            },
            "overcut_opportunity": {
                "gain_seconds": float(overcut_gain),
                "viable": overcut_gain > 2.0,
            },
            "position_risk": position_risk,
            "traffic_risk": traffic_risk,
            "reasoning": recommendation["reasoning"],
        }

    def _calculate_degradation_critical_lap(
        self,
        own_laps: pd.DataFrame,
        current_lap: int,
        total_laps: int,
        degradation_rate: float
    ) -> int:
        """
        Calculate when tire degradation becomes critical
        """
        if degradation_rate <= 0:
            # No degradation data, use standard strategy
            return int(total_laps * 0.5)  # Mid-race

        # Calculate laps until degradation exceeds threshold
        current_degradation = degradation_rate * (len(own_laps) - 5)  # Approximate

        laps_until_critical = int(
            (self.degradation_threshold * 3 - current_degradation) / degradation_rate
        )

        critical_lap = current_lap + laps_until_critical

        # Ensure within race bounds
        return min(critical_lap, total_laps - 3)

    def _calculate_optimal_window(
        self, current_lap: int, critical_lap: int, total_laps: int
    ) -> Tuple[int, int]:
        """
        Calculate optimal pit window range
        """
        # Start window 3 laps before critical lap
        window_start = max(current_lap + 1, critical_lap - 3)

        # End window 2 laps after critical lap
        window_end = min(critical_lap + 2, total_laps - 5)

        return (window_start, window_end)

    def _analyze_strategic_opportunities(
        self,
        current_lap: int,
        current_position: int,
        rivals_data: Optional[List[Dict]],
        degradation_rate: float
    ) -> Tuple[float, float]:
        """
        Analyze undercut and overcut opportunities

        Returns:
            (undercut_gain, overcut_gain) in seconds
        """
        if not rivals_data:
            return (0.0, 0.0)

        # Undercut: Pit early, gain from fresh tires
        undercut_gain = self.fresh_tire_advantage * 3  # 3 laps advantage

        # Overcut: Stay out longer, gain from rivals' degradation
        # Estimate rivals' degradation (assume similar to ours)
        overcut_gain = degradation_rate * 4  # 4 extra laps of rival degradation

        return (undercut_gain, overcut_gain)

    def _calculate_position_risk(
        self,
        current_position: int,
        optimal_window: Tuple[int, int],
        rivals_data: Optional[List[Dict]]
    ) -> str:
        """
        Calculate risk of losing position during pit stop
        """
        if current_position == 1:
            return "high"  # Leader has most to lose
        elif current_position <= 3:
            return "medium"  # Podium positions
        else:
            return "low"  # Mid-field

    def _calculate_traffic_risk(
        self,
        optimal_window: Tuple[int, int],
        current_position: int,
        rivals_data: Optional[List[Dict]]
    ) -> str:
        """
        Calculate risk of rejoining in traffic after pit stop
        """
        # Simplified calculation
        # In production, would analyze actual traffic patterns

        if current_position <= 5:
            return "medium"  # Front runners less traffic
        else:
            return "high"  # Mid-field more traffic

    def _generate_pit_recommendation(
        self,
        optimal_window: Tuple[int, int],
        undercut_gain: float,
        overcut_gain: float,
        position_risk: str,
        traffic_risk: str,
        current_lap: int,
        total_laps: int
    ) -> Dict:
        """
        Generate specific pit lap recommendation with reasoning
        """
        window_start, window_end = optimal_window

        # Default to middle of window
        recommended_lap = (window_start + window_end) // 2

        reasoning = []
        confidence = 0.7  # Base confidence

        # Adjust based on strategic opportunities
        if undercut_gain > overcut_gain + 1.0:
            # Favor early pit (undercut)
            recommended_lap = window_start
            reasoning.append(f"Undercut opportunity: +{undercut_gain:.1f}s advantage")
            confidence += 0.1

        elif overcut_gain > undercut_gain + 1.0:
            # Favor late pit (overcut)
            recommended_lap = window_end
            reasoning.append(f"Overcut opportunity: +{overcut_gain:.1f}s advantage")
            confidence += 0.1

        # Adjust for position risk
        if position_risk == "high":
            reasoning.append("High position risk - consider strategic timing")
            confidence -= 0.1

        # Adjust for traffic risk
        if traffic_risk == "high":
            reasoning.append("High traffic risk - may lose positions on rejoin")
            confidence -= 0.1
        elif traffic_risk == "low":
            confidence += 0.05

        # Ensure recommended lap is within window
        recommended_lap = max(window_start, min(window_end, recommended_lap))

        # Add window context
        reasoning.append(
            f"Optimal window: laps {window_start}-{window_end} "
            f"({window_end - window_start + 1} lap window)"
        )

        # Add urgency if near end of race
        laps_remaining = total_laps - current_lap
        if laps_remaining < 10:
            reasoning.append("Limited laps remaining - early pit recommended")
            recommended_lap = min(recommended_lap, current_lap + 3)

        return {
            "lap": recommended_lap,
            "confidence": min(1.0, max(0.0, confidence)),
            "reasoning": reasoning,
        }

    def simulate_pit_scenarios(
        self,
        own_laps: pd.DataFrame,
        current_lap: int,
        total_laps: int,
        pit_lap_options: List[int]
    ) -> List[Dict]:
        """
        Simulate different pit lap scenarios

        Args:
            own_laps: DataFrame with lap features
            current_lap: Current lap
            total_laps: Total race laps
            pit_lap_options: List of lap numbers to simulate

        Returns:
            List of scenario results
        """
        scenarios = []

        for pit_lap in pit_lap_options:
            if pit_lap <= current_lap or pit_lap > total_laps - 3:
                continue

            # Calculate estimated final position
            time_loss = self.pit_loss_seconds
            laps_on_old_tires = pit_lap - current_lap
            laps_on_new_tires = total_laps - pit_lap

            # Degradation loss on old tires (simplified)
            old_tire_loss = laps_on_old_tires * 0.1 * laps_on_old_tires

            # Fresh tire gain
            new_tire_gain = min(laps_on_new_tires, 5) * self.fresh_tire_advantage

            net_time = time_loss + old_tire_loss - new_tire_gain

            scenarios.append({
                "pit_lap": pit_lap,
                "estimated_time_loss": float(net_time),
                "laps_on_old_tires": laps_on_old_tires,
                "laps_on_new_tires": laps_on_new_tires,
            })

        # Sort by estimated time loss
        scenarios.sort(key=lambda x: x["estimated_time_loss"])

        return scenarios


# Example usage
if __name__ == "__main__":
    optimizer = PitOptimizer()

    # Simulate lap data
    own_laps = pd.DataFrame({
        'lap_number': range(1, 13),
        'lap_time': [90.5, 90.3, 90.4, 90.6, 90.5, 90.6, 90.7, 90.8, 90.9, 91.0, 91.1, 91.2],
    })

    result = optimizer.optimize_pit_window(
        own_laps=own_laps,
        current_lap=12,
        current_position=5,
        total_laps=27,
        degradation_rate=0.08
    )

    print("Pit Window Optimization:")
    print(f"Optimal Window: Laps {result['optimal_window_start']}-{result['optimal_window_end']}")
    print(f"Recommended Lap: {result['recommended_lap']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Undercut Viable: {result['undercut_opportunity']['viable']}")
    print(f"Position Risk: {result['position_risk']}")
    print(f"Reasoning: {result['reasoning']}")
