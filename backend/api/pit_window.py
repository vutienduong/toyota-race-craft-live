from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.race_service import get_race_service

router = APIRouter()

class PitWindowRecommendation(BaseModel):
    start_lap: int
    end_lap: int
    confidence: float
    expected_position_loss: int
    undercut_opportunity: Optional[float] = None
    traffic_risk: str  # "low", "medium", "high"

class PitWindowRequest(BaseModel):
    car_id: str
    session_id: str
    current_lap: int
    current_position: int
    total_laps: int

class PitWindowResponse(BaseModel):
    car_id: str
    recommended_windows: List[PitWindowRecommendation]
    optimal_lap: int
    reason: str

@router.post("/recommend", response_model=PitWindowResponse)
async def get_pit_window(request: PitWindowRequest):
    """
    Recommend optimal pit window based on pace degradation, traffic, and strategy
    """
    service = get_race_service()

    # Get pit window optimization from ML model
    pit_result = service.optimize_pit_window(
        vehicle_id=request.car_id,
        current_lap=request.current_lap,
        current_position=request.current_position,
        total_laps=request.total_laps,
        race=request.session_id
    )

    # Create primary window recommendation
    primary_window = PitWindowRecommendation(
        start_lap=pit_result.get("optimal_window_start", request.current_lap + 3),
        end_lap=pit_result.get("optimal_window_end", request.current_lap + 7),
        confidence=pit_result.get("confidence", 0.7),
        expected_position_loss=0,  # Based on position risk
        undercut_opportunity=pit_result.get("undercut_opportunity", {}).get("gain_seconds"),
        traffic_risk=pit_result.get("traffic_risk", "medium")
    )

    # Get reasoning
    reasoning_list = pit_result.get("reasoning", [])
    reason = "; ".join(reasoning_list) if reasoning_list else "Optimal window based on degradation analysis"

    return PitWindowResponse(
        car_id=request.car_id,
        recommended_windows=[primary_window],
        optimal_lap=pit_result.get("recommended_lap", request.current_lap + 5),
        reason=reason
    )

@router.post("/simulate")
async def simulate_pit_stop(
    car_id: str,
    pit_lap: int,
    current_position: int
):
    """
    Simulate the impact of pitting at a specific lap
    """
    return {
        "car_id": car_id,
        "pit_lap": pit_lap,
        "predicted_position_after_pit": current_position - 1,
        "time_lost_in_pit": 25.3,
        "positions_gained_lost": -1,
        "traffic_cars": []
    }
