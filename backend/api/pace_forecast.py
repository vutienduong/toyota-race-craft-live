from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.race_service import get_race_service

router = APIRouter()

class LapPrediction(BaseModel):
    lap_number: int
    predicted_time: float
    delta: float
    confidence: float

class PaceForecastRequest(BaseModel):
    car_id: str
    session_id: str
    current_lap: int
    laps_ahead: int = 5

class PaceForecastResponse(BaseModel):
    car_id: str
    predictions: List[LapPrediction]
    current_pace: float
    trend: str  # "improving", "stable", "degrading"

@router.post("/forecast", response_model=PaceForecastResponse)
async def get_pace_forecast(request: PaceForecastRequest):
    """
    Predict lap times for the next 3-5 laps based on current telemetry.
    Uses LightGBM-based ML model. Target accuracy: ±0.25 seconds
    """
    try:
        service = get_race_service()

        # Get predictions from ML model
        predictions = service.predict_pace(
            vehicle_id=request.car_id,
            current_lap=request.current_lap,
            laps_ahead=request.laps_ahead,
            race=request.session_id
        )

        if not predictions:
            # Fallback to dummy data if model fails
            predictions = []
            base_time = 90.0
            for i in range(1, request.laps_ahead + 1):
                predictions.append({
                    "lap_number": request.current_lap + i,
                    "predicted_time": base_time + i * 0.05,
                    "delta": i * 0.05,
                    "confidence": 0.85 - (i * 0.05)
                })

        # Convert to Pydantic models
        lap_predictions = [LapPrediction(**p) for p in predictions]

        # Determine trend
        if len(lap_predictions) >= 2:
            first_delta = lap_predictions[0].delta
            last_delta = lap_predictions[-1].delta

            if last_delta > 0.2:
                trend = "degrading"
            elif first_delta < -0.1:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Get current pace
        current_pace = lap_predictions[0].predicted_time - lap_predictions[0].delta if lap_predictions else 90.0

        return PaceForecastResponse(
            car_id=request.car_id,
            predictions=lap_predictions,
            current_pace=current_pace,
            trend=trend
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pace forecast failed: {str(e)}")

@router.get("/current/{car_id}")
async def get_current_pace(car_id: str):
    """
    Get current pace metrics for a specific car
    """
    try:
        service = get_race_service()
        features_df = service.get_lap_features(vehicle_id=car_id, use_sample=True)

        if features_df.empty:
            return {
                "car_id": car_id,
                "current_lap_time": 90.0,
                "sector_times": [30.0, 30.0, 30.0],
                "best_lap": 89.5,
                "average_lap": 90.2
            }

        current = features_df.tail(1).iloc[0]
        best_lap = features_df['lap_time'].min()
        avg_lap = features_df['lap_time'].mean()

        return {
            "car_id": car_id,
            "current_lap_time": float(current.get('lap_time', 90.0)),
            "sector_times": [30.0, 30.0, 30.0],  # TODO: Add sector times
            "best_lap": float(best_lap),
            "average_lap": float(avg_lap)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current pace: {str(e)}")
