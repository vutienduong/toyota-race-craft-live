from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional

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
    # TODO: Implement actual threat detection logic
    # This is a placeholder implementation

    threats = [
        ThreatAnalysis(
            rival_car_id="GR86-022",
            gap_seconds=0.6,
            closing_rate=0.15,
            attack_probability=0.71,
            laps_until_attack=2,
            sector_advantages=[
                SectorAdvantage(sector=1, time_delta=0.12, corner="T1 braking"),
                SectorAdvantage(sector=3, time_delta=0.08, corner="T9 exit")
            ],
            defensive_recommendation="Defend T1 entry, push T9 exit"
        )
    ]

    return ThreatDetectionResponse(
        car_id=request.car_id,
        threats=threats,
        overall_threat_level="high"
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
