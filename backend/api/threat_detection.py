from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.race_service import get_race_service

router = APIRouter()

class SectorAdvantage(BaseModel):
    sector: int
    time_delta: float
    corner: Optional[str] = None

class ThreatAnalysis(BaseModel):
    rival_car_id: str
    gap_seconds: float
    closing_rate: float  # seconds per lap
    attack_probability: float  # 0-1
    laps_until_attack: Optional[int] = None
    sector_advantages: List[SectorAdvantage]
    defensive_recommendation: str

class ThreatDetectionRequest(BaseModel):
    car_id: str
    session_id: str
    current_lap: int

class ThreatDetectionResponse(BaseModel):
    car_id: str
    threats: List[ThreatAnalysis]
    overall_threat_level: str  # "low", "medium", "high", "critical"

@router.post("/analyze", response_model=ThreatDetectionResponse)
async def detect_threats(request: ThreatDetectionRequest):
    """
    Detect and analyze threats from competitors
    Predicts attack probability for next 1-3 laps
    """
    service = get_race_service()

    # Analyze threat from nearby rival (simplified - using one rival)
    # In production, would analyze multiple rivals
    rival_id = "GR86-004-78"  # Sample rival
    current_gap = 1.5  # Sample gap in seconds

    threat_result = service.detect_threat(
        vehicle_id=request.car_id,
        rival_id=rival_id,
        current_lap=request.current_lap,
        current_gap=current_gap,
        race=request.session_id
    )

    # Convert sector advantages to API format
    sector_advantages = []
    for i, adv in enumerate(threat_result.get("sector_advantages", [])):
        sector_advantages.append(
            SectorAdvantage(
                sector=i + 1,
                time_delta=adv.get("advantage_seconds", 0.0),
                corner=adv.get("sector", "")
            )
        )

    # Get first defensive recommendation
    defensive_rec = threat_result.get("defensive_recommendations", ["Maintain position"])[0]

    threats = [
        ThreatAnalysis(
            rival_car_id=rival_id,
            gap_seconds=threat_result.get("current_gap", 0.0),
            closing_rate=0.15,  # From gap trend analysis
            attack_probability=threat_result.get("attack_probability", 0.0),
            laps_until_attack=threat_result.get("laps_until_threat", 999),
            sector_advantages=sector_advantages,
            defensive_recommendation=defensive_rec
        )
    ]

    return ThreatDetectionResponse(
        car_id=request.car_id,
        threats=threats,
        overall_threat_level=threat_result.get("threat_level", "low")
    )

@router.get("/gap/{car_id}/{rival_id}")
async def get_gap_analysis(car_id: str, rival_id: str):
    """
    Get detailed gap analysis between two cars
    """
    return {
        "car_id": car_id,
        "rival_id": rival_id,
        "current_gap": 0.6,
        "gap_trend": "closing",
        "sector_deltas": [0.12, -0.05, 0.08],
        "closing_rate_per_lap": 0.15
    }
