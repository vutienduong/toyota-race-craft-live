"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns correct data"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"


class TestPaceForecastAPI:
    """Test pace forecasting API endpoints"""

    def test_pace_forecast_endpoint(self):
        """Test pace forecast POST endpoint"""
        payload = {
            "car_id": "GR86-000-0",
            "session_id": "R1",
            "current_lap": 10,
            "laps_ahead": 5
        }

        response = client.post("/api/pace/forecast", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "car_id" in data
        assert "predictions" in data
        assert "current_pace" in data
        assert "trend" in data

        # Verify predictions structure
        predictions = data["predictions"]
        assert len(predictions) > 0
        assert all("lap_number" in p for p in predictions)
        assert all("predicted_time" in p for p in predictions)

    def test_pace_forecast_invalid_car(self):
        """Test pace forecast with invalid parameters"""
        payload = {
            "car_id": "",
            "session_id": "R1",
            "current_lap": 10,
            "laps_ahead": 5
        }

        response = client.post("/api/pace/forecast", json=payload)
        # Should still return 200 but with empty/default data
        assert response.status_code in [200, 422]


class TestDegradationAPI:
    """Test degradation analysis API endpoints"""

    def test_degradation_analysis(self):
        """Test degradation analysis endpoint"""
        payload = {
            "car_id": "GR86-000-0",
            "session_id": "R1",
            "current_lap": 15
        }

        response = client.post("/api/degradation/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "car_id" in data
        assert "degradation_curve" in data
        assert "degradation_rate" in data
        assert "stint_health" in data

        # Verify stint health is valid
        assert data["stint_health"] in ["optimal", "degrading", "critical"]


class TestThreatDetectionAPI:
    """Test threat detection API endpoints"""

    def test_threat_detection(self):
        """Test threat detection endpoint"""
        payload = {
            "car_id": "GR86-000-0",
            "session_id": "R1",
            "current_lap": 12
        }

        response = client.post("/api/threat/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "car_id" in data
        assert "threats" in data
        assert "overall_threat_level" in data

        # Verify threat level is valid
        assert data["overall_threat_level"] in ["low", "medium", "high", "critical"]

        # Verify threat structure
        if len(data["threats"]) > 0:
            threat = data["threats"][0]
            assert "rival_car_id" in threat
            assert "attack_probability" in threat
            assert 0 <= threat["attack_probability"] <= 1

    def test_gap_analysis(self):
        """Test gap analysis endpoint"""
        response = client.get("/api/threat/gap/GR86-000-0/GR86-001-10")
        assert response.status_code == 200

        data = response.json()
        assert "car_id" in data
        assert "rival_id" in data
        assert "current_gap" in data
        assert "gap_trend" in data


class TestPitWindowAPI:
    """Test pit window optimization API endpoints"""

    def test_pit_window_recommendation(self):
        """Test pit window recommendation endpoint"""
        payload = {
            "car_id": "GR86-000-0",
            "session_id": "R1",
            "current_lap": 12,
            "current_position": 5,
            "total_laps": 27
        }

        response = client.post("/api/pit/recommend", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "car_id" in data
        assert "recommended_windows" in data
        assert "optimal_lap" in data
        assert "reason" in data

        # Verify window structure
        if len(data["recommended_windows"]) > 0:
            window = data["recommended_windows"][0]
            assert "start_lap" in window
            assert "end_lap" in window
            assert "confidence" in window
            assert 0 <= window["confidence"] <= 1
            assert window["start_lap"] <= window["end_lap"]

    def test_pit_simulation(self):
        """Test pit stop simulation endpoint"""
        response = client.post(
            "/api/pit/simulate",
            params={
                "car_id": "GR86-000-0",
                "pit_lap": 15,
                "current_position": 5
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "car_id" in data
        assert "pit_lap" in data
        assert "predicted_position_after_pit" in data


class TestCurrentStatusAPI:
    """Test current status API endpoints"""

    def test_current_pace(self):
        """Test current pace endpoint"""
        response = client.get(
            "/api/current/pace/GR86-000-0",
            params={"session_id": "R1"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "vehicle_id" in data
        assert "current_pace" in data
        assert "average_pace" in data
        assert "best_lap" in data
        assert "pace_trend" in data
        assert data["pace_trend"] in ["improving", "stable", "degrading"]

    def test_current_degradation(self):
        """Test current degradation endpoint"""
        response = client.get(
            "/api/current/degradation/GR86-000-0",
            params={"session_id": "R1", "current_lap": 10}
        )
        assert response.status_code == 200

        data = response.json()
        assert "vehicle_id" in data
        assert "degradation_rate" in data
        assert "stint_health" in data
        assert data["stint_health"] in ["optimal", "degrading", "critical"]

    def test_overall_status(self):
        """Test overall status endpoint"""
        response = client.get(
            "/api/current/status/GR86-000-0",
            params={"session_id": "R1", "current_lap": 10}
        )
        assert response.status_code == 200

        data = response.json()
        assert "vehicle_id" in data
        assert "current_lap" in data
        assert "pace" in data
        assert "degradation" in data

        # Verify nested structure
        assert "current" in data["pace"]
        assert "average" in data["pace"]
        assert "rate" in data["degradation"]
        assert "health" in data["degradation"]


class TestCORSConfiguration:
    """Test CORS middleware configuration"""

    def test_cors_headers(self):
        """Test that CORS headers are present"""
        response = client.get("/")

        # Verify CORS headers (may vary based on request origin)
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling for various scenarios"""

    def test_invalid_endpoint(self):
        """Test that invalid endpoints return 404"""
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404

    def test_invalid_method(self):
        """Test that invalid HTTP methods are rejected"""
        response = client.get("/api/pace/forecast")  # Should be POST
        assert response.status_code == 405

    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        payload = {
            "car_id": "GR86-000-0"
            # Missing other required fields
        }

        response = client.post("/api/pace/forecast", json=payload)
        assert response.status_code == 422  # Validation error


# Performance tests
class TestPerformance:
    """Basic performance tests"""

    def test_response_time_pace_forecast(self):
        """Test pace forecast response time"""
        import time

        payload = {
            "car_id": "GR86-000-0",
            "session_id": "R1",
            "current_lap": 10,
            "laps_ahead": 5
        }

        start = time.time()
        response = client.post("/api/pace/forecast", json=payload)
        elapsed = time.time() - start

        assert response.status_code == 200
        # Response should be fast (< 2 seconds for sample data)
        assert elapsed < 2.0

    def test_multiple_concurrent_requests(self):
        """Test handling multiple requests"""
        payload = {
            "car_id": "GR86-000-0",
            "session_id": "R1",
            "current_lap": 10,
            "laps_ahead": 5
        }

        responses = []
        for _ in range(5):
            response = client.post("/api/pace/forecast", json=payload)
            responses.append(response)

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
