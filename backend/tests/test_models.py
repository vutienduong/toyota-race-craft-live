"""
Unit tests for ML models
"""

import pytest
import pandas as pd
import numpy as np
from models.pace_forecaster import PaceForecaster
from models.threat_detector import ThreatDetector
from models.pit_optimizer import PitOptimizer


class TestPaceForecaster:
    """Test suite for PaceForecaster model"""

    @pytest.fixture
    def forecaster(self):
        return PaceForecaster()

    @pytest.fixture
    def sample_laps(self):
        """Create sample lap data"""
        return pd.DataFrame({
            'lap_number': range(1, 11),
            'lap_time': [90.5, 90.3, 90.4, 90.6, 90.5, 90.4, 90.5, 90.6, 90.7, 90.6],
            'avg_speed': [125.0] * 10,
            'avg_lateral_g': [1.2] * 10,
            'brake_variance': [5.0] * 10,
            'throttle_variance': [3.0] * 10,
        })

    def test_prediction_shape(self, forecaster, sample_laps):
        """Test that predictions have correct shape"""
        predictions = forecaster.predict(sample_laps, laps_ahead=5)

        assert len(predictions) == 5
        assert all('lap_number' in p for p in predictions)
        assert all('predicted_time' in p for p in predictions)
        assert all('confidence' in p for p in predictions)

    def test_prediction_values(self, forecaster, sample_laps):
        """Test that predicted values are reasonable"""
        predictions = forecaster.predict(sample_laps, laps_ahead=3)

        for pred in predictions:
            # Predicted times should be positive
            assert pred['predicted_time'] > 0
            # Confidence should be between 0 and 1
            assert 0 <= pred['confidence'] <= 1
            # Predicted time should be close to average (within 10 seconds)
            assert 80 < pred['predicted_time'] < 100

    def test_feature_preparation(self, forecaster, sample_laps):
        """Test feature preparation for training"""
        # Add required columns
        sample_laps['pace_trend_5lap'] = 0.1
        sample_laps['pace_variance_5lap'] = 0.05

        X, y = forecaster.prepare_features(sample_laps, lookback=3, lookahead=1)

        assert not X.empty
        assert not y.empty
        assert len(X) == len(y)

    def test_consecutive_lap_numbers(self, forecaster, sample_laps):
        """Test that predicted lap numbers are consecutive"""
        predictions = forecaster.predict(sample_laps, laps_ahead=5)

        lap_numbers = [p['lap_number'] for p in predictions]
        for i in range(1, len(lap_numbers)):
            assert lap_numbers[i] == lap_numbers[i-1] + 1


class TestThreatDetector:
    """Test suite for ThreatDetector model"""

    @pytest.fixture
    def detector(self):
        return ThreatDetector()

    @pytest.fixture
    def own_laps(self):
        """Create sample own vehicle lap data"""
        return pd.DataFrame({
            'lap_number': range(1, 11),
            'lap_time': [90.5, 90.3, 90.4, 90.6, 90.5, 90.4, 90.5, 90.6, 90.7, 90.6],
            'avg_speed': [125] * 10,
            'avg_lateral_g': [1.2] * 10,
            'brake_variance': [5.0] * 10,
        })

    @pytest.fixture
    def rival_laps_faster(self):
        """Create sample rival lap data (faster)"""
        return pd.DataFrame({
            'lap_number': range(1, 11),
            'lap_time': [90.0, 89.8, 89.7, 89.6, 89.5, 89.4, 89.3, 89.2, 89.1, 89.0],
            'avg_speed': [127] * 10,
            'avg_lateral_g': [1.25] * 10,
            'brake_variance': [4.0] * 10,
        })

    @pytest.fixture
    def rival_laps_slower(self):
        """Create sample rival lap data (slower)"""
        return pd.DataFrame({
            'lap_number': range(1, 11),
            'lap_time': [91.0, 91.1, 91.2, 91.3, 91.4, 91.5, 91.6, 91.7, 91.8, 91.9],
            'avg_speed': [123] * 10,
            'avg_lateral_g': [1.15] * 10,
            'brake_variance': [6.0] * 10,
        })

    def test_threat_detection_faster_rival(self, detector, own_laps, rival_laps_faster):
        """Test threat detection with faster rival"""
        threat = detector.analyze_threat(
            own_laps=own_laps,
            rival_laps=rival_laps_faster,
            current_gap=2.0,
            current_lap=10
        )

        assert 'attack_probability' in threat
        assert 'threat_level' in threat
        assert 'defensive_recommendations' in threat

        # Faster rival should have higher threat
        assert threat['attack_probability'] > 0.3
        assert threat['threat_level'] in ['low', 'medium', 'high']

    def test_threat_detection_slower_rival(self, detector, own_laps, rival_laps_slower):
        """Test threat detection with slower rival"""
        threat = detector.analyze_threat(
            own_laps=own_laps,
            rival_laps=rival_laps_slower,
            current_gap=2.0,
            current_lap=10
        )

        # Slower rival should have lower threat
        assert threat['attack_probability'] < 0.5
        assert threat['threat_level'] in ['low', 'medium']

    def test_threat_with_small_gap(self, detector, own_laps, rival_laps_faster):
        """Test threat detection with small gap"""
        threat_small_gap = detector.analyze_threat(
            own_laps=own_laps,
            rival_laps=rival_laps_faster,
            current_gap=0.5,
            current_lap=10
        )

        threat_large_gap = detector.analyze_threat(
            own_laps=own_laps,
            rival_laps=rival_laps_faster,
            current_gap=5.0,
            current_lap=10
        )

        # Small gap should result in higher threat probability
        assert threat_small_gap['attack_probability'] >= threat_large_gap['attack_probability']

    def test_defensive_recommendations(self, detector, own_laps, rival_laps_faster):
        """Test that defensive recommendations are provided"""
        threat = detector.analyze_threat(
            own_laps=own_laps,
            rival_laps=rival_laps_faster,
            current_gap=1.0,
            current_lap=10
        )

        assert len(threat['defensive_recommendations']) > 0
        assert all(isinstance(rec, str) for rec in threat['defensive_recommendations'])

    def test_insufficient_data(self, detector):
        """Test handling of insufficient data"""
        empty_laps = pd.DataFrame()

        threat = detector.analyze_threat(
            own_laps=empty_laps,
            rival_laps=empty_laps,
            current_gap=2.0,
            current_lap=1
        )

        assert threat['attack_probability'] == 0.0
        assert threat['threat_level'] == 'low'


class TestPitOptimizer:
    """Test suite for PitOptimizer model"""

    @pytest.fixture
    def optimizer(self):
        return PitOptimizer()

    @pytest.fixture
    def sample_laps(self):
        """Create sample lap data with degradation"""
        return pd.DataFrame({
            'lap_number': range(1, 13),
            'lap_time': [90.5, 90.3, 90.4, 90.6, 90.5, 90.6, 90.7, 90.8, 90.9, 91.0, 91.1, 91.2],
        })

    def test_pit_window_recommendation(self, optimizer, sample_laps):
        """Test pit window recommendation structure"""
        result = optimizer.optimize_pit_window(
            own_laps=sample_laps,
            current_lap=12,
            current_position=5,
            total_laps=27,
            degradation_rate=0.08
        )

        assert 'optimal_window_start' in result
        assert 'optimal_window_end' in result
        assert 'recommended_lap' in result
        assert 'confidence' in result
        assert 'reasoning' in result

    def test_window_bounds(self, optimizer, sample_laps):
        """Test that pit window is within race bounds"""
        result = optimizer.optimize_pit_window(
            own_laps=sample_laps,
            current_lap=12,
            current_position=5,
            total_laps=27,
            degradation_rate=0.08
        )

        # Window should be after current lap and before race end
        assert result['optimal_window_start'] > 12
        assert result['optimal_window_end'] < 27
        assert result['optimal_window_start'] <= result['optimal_window_end']

    def test_recommended_lap_in_window(self, optimizer, sample_laps):
        """Test that recommended lap is within optimal window"""
        result = optimizer.optimize_pit_window(
            own_laps=sample_laps,
            current_lap=12,
            current_position=5,
            total_laps=27,
            degradation_rate=0.08
        )

        assert result['optimal_window_start'] <= result['recommended_lap'] <= result['optimal_window_end']

    def test_confidence_range(self, optimizer, sample_laps):
        """Test that confidence is between 0 and 1"""
        result = optimizer.optimize_pit_window(
            own_laps=sample_laps,
            current_lap=12,
            current_position=5,
            total_laps=27,
            degradation_rate=0.08
        )

        assert 0 <= result['confidence'] <= 1

    def test_undercut_overcut_opportunities(self, optimizer, sample_laps):
        """Test undercut and overcut opportunity detection"""
        result = optimizer.optimize_pit_window(
            own_laps=sample_laps,
            current_lap=12,
            current_position=5,
            total_laps=27,
            degradation_rate=0.08
        )

        assert 'undercut_opportunity' in result
        assert 'overcut_opportunity' in result
        assert 'gain_seconds' in result['undercut_opportunity']
        assert 'gain_seconds' in result['overcut_opportunity']

    def test_pit_scenarios_simulation(self, optimizer, sample_laps):
        """Test pit scenario simulation"""
        scenarios = optimizer.simulate_pit_scenarios(
            own_laps=sample_laps,
            current_lap=12,
            total_laps=27,
            pit_lap_options=[15, 17, 19, 21]
        )

        assert len(scenarios) > 0
        assert all('pit_lap' in s for s in scenarios)
        assert all('estimated_time_loss' in s for s in scenarios)

        # Scenarios should be sorted by time loss
        time_losses = [s['estimated_time_loss'] for s in scenarios]
        assert time_losses == sorted(time_losses)


# Integration test
class TestModelIntegration:
    """Integration tests for multiple models working together"""

    def test_full_race_analysis_workflow(self):
        """Test complete race analysis workflow"""
        # Create sample data
        own_laps = pd.DataFrame({
            'lap_number': range(1, 11),
            'lap_time': [90.5, 90.3, 90.4, 90.6, 90.5, 90.6, 90.7, 90.8, 90.9, 91.0],
            'avg_speed': [125] * 10,
            'avg_lateral_g': [1.2] * 10,
            'brake_variance': [5.0] * 10,
            'throttle_variance': [3.0] * 10,
        })

        rival_laps = pd.DataFrame({
            'lap_number': range(1, 11),
            'lap_time': [90.0, 89.9, 89.8, 89.7, 89.6, 89.5, 89.4, 89.3, 89.2, 89.1],
            'avg_speed': [127] * 10,
            'avg_lateral_g': [1.25] * 10,
            'brake_variance': [4.0] * 10,
        })

        # Initialize models
        pace_forecaster = PaceForecaster()
        threat_detector = ThreatDetector()
        pit_optimizer = PitOptimizer()

        # Run all analyses
        pace_predictions = pace_forecaster.predict(own_laps, laps_ahead=5)
        threat_analysis = threat_detector.analyze_threat(
            own_laps=own_laps,
            rival_laps=rival_laps,
            current_gap=2.0,
            current_lap=10
        )
        pit_strategy = pit_optimizer.optimize_pit_window(
            own_laps=own_laps,
            current_lap=10,
            current_position=5,
            total_laps=27,
            degradation_rate=0.05
        )

        # Verify all analyses completed
        assert len(pace_predictions) == 5
        assert threat_analysis['attack_probability'] > 0
        assert pit_strategy['recommended_lap'] > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
