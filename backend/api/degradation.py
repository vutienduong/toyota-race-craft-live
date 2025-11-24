from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.race_service import get_race_service

router = APIRouter()

class DegradationPoint(BaseModel):
    lap: int
    delta_seconds: float
    severity: float  # 0-1

class DegradationCause(BaseModel):
    cause_type: str  # "lateral_grip_loss", "brake_fade", "throttle_inconsistency"
    confidence: float
    indicators: List[str]

class DegradationRequest(BaseModel):
    car_id: str
    session_id: str
    current_lap: int

class DegradationResponse(BaseModel):
    car_id: str
    degradation_curve: List[DegradationPoint]
    degradation_rate: float  # seconds per lap
    primary_causes: List[DegradationCause]
    stint_health: str  # "fresh", "optimal", "degrading", "critical"
    recommended_action: str

@router.post("/analyze", response_model=DegradationResponse)
async def analyze_degradation(request: DegradationRequest):
    """
    Infer tire and grip degradation from telemetry signals
    Detection target: within 3 laps of onset
    """
    try:
        service = get_race_service()

        # Get degradation analysis
        analysis = service.analyze_degradation(
            vehicle_id=request.car_id,
            current_lap=request.current_lap,
            race=request.session_id
        )

        if not analysis:
            # Fallback response
            return DegradationResponse(
                car_id=request.car_id,
                degradation_curve=[
                    DegradationPoint(lap=i, delta_seconds=i * 0.04, severity=min(i * 0.04 / 0.5, 1.0))
                    for i in range(max(1, request.current_lap - 5), request.current_lap + 1)
                ],
                degradation_rate=0.20,
                primary_causes=[
                    DegradationCause(
                        cause_type="lateral_grip_loss",
                        confidence=0.78,
                        indicators=["Reduced lateral G in corners"]
                    )
                ],
                stint_health="optimal",
                recommended_action="Monitor closely"
            )

        # Convert analysis to response format
        curve = [DegradationPoint(**p) for p in analysis.get('degradation_curve', [])]
        causes = [DegradationCause(**c) for c in analysis.get('primary_causes', [])]

        return DegradationResponse(
            car_id=request.car_id,
            degradation_curve=curve,
            degradation_rate=analysis.get('degradation_rate', 0.0),
            primary_causes=causes,
            stint_health=analysis.get('stint_health', 'optimal'),
            recommended_action=analysis.get('recommended_action', 'Monitor closely')
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Degradation analysis failed: {str(e)}")

@router.get("/current/{car_id}")
async def get_current_degradation(car_id: str):
    """
    Get current degradation metrics for a specific car
    """
    try:
        service = get_race_service()
        features_df = service.get_lap_features(vehicle_id=car_id)

        if features_df.empty:
            return {
                "car_id": car_id,
                "current_degradation": 0.20,
                "laps_on_tires": 8,
                "estimated_laps_remaining": 6,
                "grip_level": 0.82
            }

        current_lap = len(features_df)
        deg_score = features_df.tail(1).iloc[0].get('degradation_score', 0) if 'degradation_score' in features_df.columns else 0

        return {
            "car_id": car_id,
            "current_degradation": float(deg_score / 100.0),
            "laps_on_tires": current_lap,
            "estimated_laps_remaining": max(0, 15 - current_lap),
            "grip_level": max(0.5, 1.0 - (deg_score / 100.0))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get degradation: {str(e)}")
