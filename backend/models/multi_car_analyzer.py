"""
Multi-car comparison and race analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiCarAnalyzer:
    """
    Analyze and compare performance across multiple vehicles
    """

    def __init__(self):
        self.comparison_metrics = [
            'lap_time',
            'avg_speed',
            'consistency',
            'pace_trend',
        ]

    def compare_vehicles(
        self,
        vehicles_data: Dict[str, pd.DataFrame],
        current_lap: int
    ) -> Dict:
        """
        Compare performance across multiple vehicles

        Args:
            vehicles_data: Dictionary mapping vehicle_id to lap features DataFrame
            current_lap: Current lap number

        Returns:
            Dictionary with comparison results
        """
        if not vehicles_data:
            return {}

        comparisons = []

        # Calculate metrics for each vehicle
        for vehicle_id, laps_df in vehicles_data.items():
            if laps_df.empty:
                continue

            # Get recent laps
            recent_laps = laps_df[laps_df['lap_number'] <= current_lap].tail(5)

            if len(recent_laps) < 2:
                continue

            metrics = self._calculate_vehicle_metrics(recent_laps, vehicle_id)
            comparisons.append(metrics)

        if not comparisons:
            return {}

        # Sort by average pace (fastest first)
        comparisons.sort(key=lambda x: x['avg_pace'])

        # Calculate gaps to leader
        leader_pace = comparisons[0]['avg_pace']
        for i, comp in enumerate(comparisons):
            comp['position'] = i + 1
            comp['gap_to_leader'] = comp['avg_pace'] - leader_pace

        # Identify fastest in each metric
        fastest_lap = min(comparisons, key=lambda x: x['best_lap'])
        most_consistent = max(comparisons, key=lambda x: x['consistency_score'])

        return {
            'comparisons': comparisons,
            'fastest_overall': comparisons[0]['vehicle_id'],
            'fastest_single_lap': fastest_lap['vehicle_id'],
            'most_consistent': most_consistent['vehicle_id'],
            'total_vehicles': len(comparisons),
        }

    def _calculate_vehicle_metrics(
        self,
        laps_df: pd.DataFrame,
        vehicle_id: str
    ) -> Dict:
        """Calculate performance metrics for a vehicle"""
        avg_pace = laps_df['lap_time'].mean()
        best_lap = laps_df['lap_time'].min()
        worst_lap = laps_df['lap_time'].max()
        lap_std = laps_df['lap_time'].std()

        # Consistency score (0-1, higher is better)
        consistency_score = max(0, min(1, 1 - (lap_std / avg_pace)))

        # Pace trend
        if len(laps_df) >= 3:
            first_half = laps_df['lap_time'].iloc[:len(laps_df)//2].mean()
            second_half = laps_df['lap_time'].iloc[len(laps_df)//2:].mean()

            if second_half < first_half - 0.1:
                trend = "improving"
            elif second_half > first_half + 0.1:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            'vehicle_id': vehicle_id,
            'avg_pace': float(avg_pace),
            'best_lap': float(best_lap),
            'worst_lap': float(worst_lap),
            'consistency_score': float(consistency_score),
            'pace_trend': trend,
            'lap_count': len(laps_df),
        }

    def generate_race_leaderboard(
        self,
        vehicles_data: Dict[str, pd.DataFrame],
        current_lap: int,
        gaps: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Generate race leaderboard with current positions and gaps

        Args:
            vehicles_data: Dictionary mapping vehicle_id to lap features
            current_lap: Current lap number
            gaps: Optional dictionary of time gaps to leader

        Returns:
            Sorted leaderboard
        """
        leaderboard = []

        for vehicle_id, laps_df in vehicles_data.items():
            if laps_df.empty:
                continue

            recent_laps = laps_df[laps_df['lap_number'] <= current_lap]

            if recent_laps.empty:
                continue

            # Get latest lap info
            latest_lap = recent_laps.iloc[-1]
            current_pace = latest_lap['lap_time']

            # Calculate total race time (sum of all laps)
            total_time = recent_laps['lap_time'].sum()

            entry = {
                'vehicle_id': vehicle_id,
                'laps_completed': len(recent_laps),
                'total_time': float(total_time),
                'current_pace': float(current_pace),
                'last_lap': int(latest_lap['lap_number']),
            }

            # Add gap if provided
            if gaps and vehicle_id in gaps:
                entry['gap'] = gaps[vehicle_id]

            leaderboard.append(entry)

        # Sort by laps completed (descending) then total time (ascending)
        leaderboard.sort(key=lambda x: (-x['laps_completed'], x['total_time']))

        # Add positions and calculate gaps
        for i, entry in enumerate(leaderboard):
            entry['position'] = i + 1

            if i == 0:
                entry['gap_to_leader'] = 0.0
                entry['gap_to_ahead'] = 0.0
            else:
                leader_time = leaderboard[0]['total_time']
                ahead_time = leaderboard[i-1]['total_time']

                entry['gap_to_leader'] = entry['total_time'] - leader_time
                entry['gap_to_ahead'] = entry['total_time'] - ahead_time

        return leaderboard

    def predict_position_changes(
        self,
        leaderboard: List[Dict],
        pace_predictions: Dict[str, List[float]],
        laps_ahead: int = 3
    ) -> List[Dict]:
        """
        Predict position changes based on pace forecasts

        Args:
            leaderboard: Current leaderboard
            pace_predictions: Dictionary mapping vehicle_id to predicted lap times
            laps_ahead: Number of laps to predict

        Returns:
            List of predicted position changes
        """
        predictions = []

        # Simulate future laps
        simulated_times = {}
        for entry in leaderboard:
            vehicle_id = entry['vehicle_id']
            current_time = entry['total_time']

            if vehicle_id in pace_predictions:
                future_laps = pace_predictions[vehicle_id][:laps_ahead]
                future_time = current_time + sum(future_laps)
            else:
                # Use current pace as fallback
                future_time = current_time + (entry['current_pace'] * laps_ahead)

            simulated_times[vehicle_id] = future_time

        # Sort by predicted time
        predicted_order = sorted(simulated_times.items(), key=lambda x: x[1])

        # Compare with current order
        current_order = [e['vehicle_id'] for e in leaderboard]

        for i, (vehicle_id, predicted_time) in enumerate(predicted_order):
            current_pos = current_order.index(vehicle_id) + 1
            predicted_pos = i + 1
            position_change = current_pos - predicted_pos

            predictions.append({
                'vehicle_id': vehicle_id,
                'current_position': current_pos,
                'predicted_position': predicted_pos,
                'position_change': position_change,
                'predicted_total_time': float(predicted_time),
            })

        return predictions

    def analyze_battle_groups(
        self,
        leaderboard: List[Dict],
        gap_threshold: float = 2.0
    ) -> List[List[str]]:
        """
        Identify groups of cars battling together

        Args:
            leaderboard: Current leaderboard
            gap_threshold: Maximum gap (seconds) to consider cars in same battle

        Returns:
            List of battle groups (lists of vehicle_ids)
        """
        if not leaderboard:
            return []

        battle_groups = []
        current_group = [leaderboard[0]['vehicle_id']]

        for i in range(1, len(leaderboard)):
            gap = leaderboard[i]['gap_to_ahead']

            if gap <= gap_threshold:
                # Add to current battle group
                current_group.append(leaderboard[i]['vehicle_id'])
            else:
                # Start new battle group
                if len(current_group) > 1:
                    battle_groups.append(current_group)
                current_group = [leaderboard[i]['vehicle_id']]

        # Add last group if it has multiple cars
        if len(current_group) > 1:
            battle_groups.append(current_group)

        return battle_groups

    def calculate_relative_pace(
        self,
        vehicle_id: str,
        vehicles_data: Dict[str, pd.DataFrame],
        current_lap: int,
        window_size: int = 5
    ) -> Dict:
        """
        Calculate pace relative to other vehicles

        Args:
            vehicle_id: Target vehicle
            vehicles_data: All vehicles data
            current_lap: Current lap
            window_size: Number of recent laps to compare

        Returns:
            Dictionary with relative pace analysis
        """
        if vehicle_id not in vehicles_data:
            return {}

        own_laps = vehicles_data[vehicle_id]
        own_recent = own_laps[own_laps['lap_number'] <= current_lap].tail(window_size)

        if own_recent.empty:
            return {}

        own_avg_pace = own_recent['lap_time'].mean()

        # Compare with all other vehicles
        pace_comparison = []

        for other_id, other_laps in vehicles_data.items():
            if other_id == vehicle_id:
                continue

            other_recent = other_laps[other_laps['lap_number'] <= current_lap].tail(window_size)

            if not other_recent.empty:
                other_avg_pace = other_recent['lap_time'].mean()
                pace_delta = own_avg_pace - other_avg_pace

                pace_comparison.append({
                    'vehicle_id': other_id,
                    'pace_delta': float(pace_delta),
                    'faster': pace_delta < 0,
                })

        # Sort by pace delta
        pace_comparison.sort(key=lambda x: x['pace_delta'])

        # Count how many cars are faster/slower
        faster_count = sum(1 for p in pace_comparison if p['faster'])
        slower_count = len(pace_comparison) - faster_count

        return {
            'vehicle_id': vehicle_id,
            'avg_pace': float(own_avg_pace),
            'relative_position': faster_count + 1,
            'cars_faster': faster_count,
            'cars_slower': slower_count,
            'pace_comparison': pace_comparison,
        }


# Example usage
if __name__ == "__main__":
    analyzer = MultiCarAnalyzer()

    # Create sample data for multiple vehicles
    vehicles_data = {}

    for i in range(5):
        vehicle_id = f"GR86-00{i}-{i*10}"
        lap_times = [90.0 + np.random.normal(0, 0.3) + (i * 0.2) for _ in range(10)]

        vehicles_data[vehicle_id] = pd.DataFrame({
            'lap_number': range(1, 11),
            'lap_time': lap_times,
        })

    # Compare vehicles
    comparison = analyzer.compare_vehicles(vehicles_data, current_lap=10)

    print("Multi-Car Comparison:")
    print(f"Fastest Overall: {comparison['fastest_overall']}")
    print(f"Most Consistent: {comparison['most_consistent']}")

    print("\nLeaderboard:")
    for comp in comparison['comparisons']:
        print(f"P{comp['position']}: {comp['vehicle_id']} - {comp['avg_pace']:.3f}s (+{comp['gap_to_leader']:.3f}s)")
