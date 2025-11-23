"""
Current Race Status API
Real-time metrics for vehicles
"""

from fastapi import APIRouter
from pydantic import BaseModel
from services.race_service import get_race_service

router = APIRouter()


class CurrentPaceResponse(BaseModel):
    vehicle_id: str
    current_pace: float  # Seconds
    average_pace: float  # Seconds
    best_lap: float  # Seconds
    pace_trend: str  # "improving", "stable", "degrading"
    consistency: float  # 0-1 score
    recent_laps: int


class CurrentDegradationResponse(BaseModel):
    vehicle_id: str
    degradation_rate: float  # Seconds per lap
    stint_health: str  # "optimal", "degrading", "critical"
    laps_on_current_tires: int
    recommended_action: str


@router.get("/pace/{car_id}", response_model=CurrentPaceResponse)
async def get_current_pace(car_id: str, session_id: str = "R1"):
    """
    Get current pace metrics for a vehicle

    Args:
        car_id: Vehicle identifier
        session_id: Race session (R1 or R2)

    Returns:
        Current pace analysis
    """
    service = get_race_service()

    pace_data = service.get_current_pace(
        vehicle_id=car_id,
        race=session_id,
        window_size=5
    )

    return CurrentPaceResponse(**pace_data)


@router.get("/degradation/{car_id}", response_model=CurrentDegradationResponse)
async def get_current_degradation(
    car_id: str,
    session_id: str = "R1",
    current_lap: int = 10
):
    """
    Get current degradation status for a vehicle

    Args:
        car_id: Vehicle identifier
        session_id: Race session (R1 or R2)
        current_lap: Current lap number

    Returns:
        Current degradation analysis
    """
    service = get_race_service()

    deg_data = service.analyze_degradation(
        vehicle_id=car_id,
        current_lap=current_lap,
        race=session_id
    )

    return CurrentDegradationResponse(
        vehicle_id=car_id,
        degradation_rate=deg_data.get("degradation_rate", 0.0),
        stint_health=deg_data.get("stint_health", "optimal"),
        laps_on_current_tires=current_lap,  # Simplified
        recommended_action=deg_data.get("recommended_action", "Monitor closely")
    )


@router.get("/status/{car_id}")
async def get_overall_status(
    car_id: str,
    session_id: str = "R1",
    current_lap: int = 10
):
    """
    Get comprehensive current status for a vehicle

    Combines pace, degradation, and position data

    Args:
        car_id: Vehicle identifier
        session_id: Race session
        current_lap: Current lap number

    Returns:
        Complete status overview
    """
    service = get_race_service()

    # Get pace metrics
    pace_data = service.get_current_pace(
        vehicle_id=car_id,
        race=session_id
    )

    # Get degradation metrics
    deg_data = service.analyze_degradation(
        vehicle_id=car_id,
        current_lap=current_lap,
        race=session_id
    )

    return {
        "vehicle_id": car_id,
        "current_lap": current_lap,
        "pace": {
            "current": pace_data.get("current_pace"),
            "average": pace_data.get("average_pace"),
            "best": pace_data.get("best_lap"),
            "trend": pace_data.get("pace_trend"),
            "consistency": pace_data.get("consistency"),
        },
        "degradation": {
            "rate": deg_data.get("degradation_rate"),
            "health": deg_data.get("stint_health"),
            "action": deg_data.get("recommended_action"),
        },
        "session_id": session_id,
    }
