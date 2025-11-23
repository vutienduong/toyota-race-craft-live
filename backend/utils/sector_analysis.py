"""
Sector timing analysis for detailed performance breakdown
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """
    Analyze sector times and performance breakdown
    Barber Motorsports Park has 3 sectors
    """

    def __init__(self, track_length: float = 2380):
        """
        Args:
            track_length: Track length in meters (Barber = 2380m)
        """
        self.track_length = track_length

        # Define sector boundaries (in meters from start/finish)
        # Barber has 3 sectors
        self.sector_boundaries = {
            1: (0, track_length / 3),          # Sector 1: 0-793m
            2: (track_length / 3, 2 * track_length / 3),  # Sector 2: 793-1587m
            3: (2 * track_length / 3, track_length),      # Sector 3: 1587-2380m
        }

    def calculate_sector_times(
        self,
        telemetry_df: pd.DataFrame,
        lapdist_col: str = "Laptrigger_lapdist_dls",
        time_col: str = "meta_time"
    ) -> List[Dict]:
        """
        Calculate sector times from telemetry data

        Args:
            telemetry_df: Telemetry data with lap distance and time
            lapdist_col: Column name for lap distance
            time_col: Column name for time

        Returns:
            List of sector time records
        """
        if telemetry_df.empty:
            return []

        sector_times = []

        # Sort by time
        df = telemetry_df.sort_values(time_col).copy()

        for sector_num, (start_dist, end_dist) in self.sector_boundaries.items():
            # Find entries where vehicle crosses sector boundaries
            sector_data = df[
                (df[lapdist_col] >= start_dist) &
                (df[lapdist_col] < end_dist)
            ]

            if not sector_data.empty:
                sector_start_time = sector_data[time_col].iloc[0]
                sector_end_time = sector_data[time_col].iloc[-1]
                sector_time = sector_end_time - sector_start_time

                # Calculate average speed in sector
                total_distance = end_dist - start_dist
                avg_speed = (total_distance / sector_time) * 3.6 if sector_time > 0 else 0  # km/h

                # Get telemetry stats for sector
                avg_throttle = sector_data.get('aps', pd.Series([0])).mean()
                avg_brake = sector_data.get('pbrake_f', pd.Series([0])).mean()
                avg_lateral_g = sector_data.get('accy_can', pd.Series([0])).mean()

                sector_times.append({
                    'sector': sector_num,
                    'time': float(sector_time),
                    'avg_speed': float(avg_speed),
                    'avg_throttle': float(avg_throttle),
                    'avg_brake': float(avg_brake),
                    'avg_lateral_g': float(avg_lateral_g),
                    'distance': float(total_distance),
                })

        return sector_times

    def compare_sector_performance(
        self,
        own_sectors: List[Dict],
        rival_sectors: List[Dict]
    ) -> List[Dict]:
        """
        Compare sector times between two vehicles

        Args:
            own_sectors: Own vehicle sector times
            rival_sectors: Rival vehicle sector times

        Returns:
            List of sector comparisons
        """
        comparisons = []

        for sector_num in range(1, 4):
            own_sector = next((s for s in own_sectors if s['sector'] == sector_num), None)
            rival_sector = next((s for s in rival_sectors if s['sector'] == sector_num), None)

            if own_sector and rival_sector:
                time_delta = own_sector['time'] - rival_sector['time']
                speed_delta = own_sector['avg_speed'] - rival_sector['avg_speed']

                # Determine advantage
                if time_delta > 0.05:
                    advantage = "rival"
                    advantage_margin = abs(time_delta)
                elif time_delta < -0.05:
                    advantage = "own"
                    advantage_margin = abs(time_delta)
                else:
                    advantage = "even"
                    advantage_margin = 0.0

                comparisons.append({
                    'sector': sector_num,
                    'own_time': own_sector['time'],
                    'rival_time': rival_sector['time'],
                    'time_delta': float(time_delta),
                    'speed_delta': float(speed_delta),
                    'advantage': advantage,
                    'advantage_margin': float(advantage_margin),
                })

        return comparisons

    def identify_optimal_racing_line_sectors(
        self,
        sector_times_history: List[List[Dict]],
        top_n: int = 3
    ) -> Dict:
        """
        Identify optimal racing line by analyzing best sector times

        Args:
            sector_times_history: List of sector times from multiple laps
            top_n: Number of best laps to consider

        Returns:
            Dictionary with optimal sector characteristics
        """
        if not sector_times_history:
            return {}

        optimal_sectors = {}

        for sector_num in range(1, 4):
            sector_data = []

            # Collect all sector times for this sector
            for lap_sectors in sector_times_history:
                sector = next((s for s in lap_sectors if s['sector'] == sector_num), None)
                if sector:
                    sector_data.append(sector)

            if sector_data:
                # Sort by time and get top N
                sector_data.sort(key=lambda x: x['time'])
                best_sectors = sector_data[:top_n]

                # Calculate optimal characteristics
                optimal_sectors[sector_num] = {
                    'best_time': float(np.mean([s['time'] for s in best_sectors])),
                    'optimal_speed': float(np.mean([s['avg_speed'] for s in best_sectors])),
                    'optimal_throttle': float(np.mean([s['avg_throttle'] for s in best_sectors])),
                    'optimal_brake': float(np.mean([s['avg_brake'] for s in best_sectors])),
                    'consistency': float(np.std([s['time'] for s in sector_data])),
                }

        return optimal_sectors

    def calculate_sector_consistency(
        self,
        sector_times_history: List[List[Dict]]
    ) -> Dict:
        """
        Calculate consistency score for each sector

        Args:
            sector_times_history: List of sector times from multiple laps

        Returns:
            Dictionary with consistency metrics per sector
        """
        consistency_metrics = {}

        for sector_num in range(1, 4):
            times = []

            for lap_sectors in sector_times_history:
                sector = next((s for s in lap_sectors if s['sector'] == sector_num), None)
                if sector:
                    times.append(sector['time'])

            if len(times) >= 2:
                mean_time = np.mean(times)
                std_time = np.std(times)
                coefficient_of_variation = (std_time / mean_time) * 100 if mean_time > 0 else 0

                # Consistency score (0-1, higher is better)
                # Lower CV = higher consistency
                consistency_score = max(0, min(1, 1 - (coefficient_of_variation / 10)))

                consistency_metrics[sector_num] = {
                    'mean_time': float(mean_time),
                    'std_dev': float(std_time),
                    'coefficient_of_variation': float(coefficient_of_variation),
                    'consistency_score': float(consistency_score),
                    'sample_size': len(times),
                }

        return consistency_metrics

    def detect_sector_issues(
        self,
        current_sectors: List[Dict],
        optimal_sectors: Dict
    ) -> List[Dict]:
        """
        Detect issues by comparing current sector times to optimal

        Args:
            current_sectors: Current lap sector times
            optimal_sectors: Optimal sector characteristics

        Returns:
            List of detected issues
        """
        issues = []

        for sector in current_sectors:
            sector_num = sector['sector']

            if sector_num in optimal_sectors:
                optimal = optimal_sectors[sector_num]
                time_diff = sector['time'] - optimal['best_time']

                # Issue if current time is significantly slower
                if time_diff > 0.2:  # 0.2 seconds slower
                    severity = "high" if time_diff > 0.5 else "medium"

                    # Analyze potential causes
                    causes = []

                    if sector['avg_speed'] < optimal['optimal_speed'] - 5:
                        causes.append("Low speed through sector")

                    if sector['avg_throttle'] < optimal['optimal_throttle'] - 10:
                        causes.append("Insufficient throttle application")

                    if sector['avg_brake'] > optimal['optimal_brake'] + 5:
                        causes.append("Excessive braking")

                    issues.append({
                        'sector': sector_num,
                        'time_loss': float(time_diff),
                        'severity': severity,
                        'potential_causes': causes,
                        'recommendation': f"Focus on improving sector {sector_num} performance",
                    })

        return issues


# Example usage
if __name__ == "__main__":
    analyzer = SectorAnalyzer(track_length=2380)

    # Create sample telemetry data
    sample_telemetry = pd.DataFrame({
        'meta_time': np.arange(0, 90, 0.1),
        'Laptrigger_lapdist_dls': np.linspace(0, 2380, 900),
        'aps': np.random.uniform(30, 95, 900),
        'pbrake_f': np.random.uniform(0, 40, 900),
        'accy_can': np.random.uniform(-1.5, 1.5, 900),
    })

    sector_times = analyzer.calculate_sector_times(sample_telemetry)

    print("Sector Times:")
    for sector in sector_times:
        print(f"Sector {sector['sector']}: {sector['time']:.3f}s @ {sector['avg_speed']:.1f} km/h")
