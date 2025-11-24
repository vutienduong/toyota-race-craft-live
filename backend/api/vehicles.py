from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.race_service import get_race_service

router = APIRouter()

class VehicleInfo(BaseModel):
    vehicle_id: str
    vehicle_number: int
    display_name: str

class VehiclesResponse(BaseModel):
    vehicles: List[VehicleInfo]
    session_id: str

@router.get("/list/{session_id}", response_model=VehiclesResponse)
async def list_vehicles(session_id: str = "R1"):
    """
    Get list of all available vehicles in the session
    """
    service = get_race_service()

    # Get available vehicles from the data
    vehicles = service.get_available_vehicles(race=session_id)

    vehicle_list = [
        VehicleInfo(
            vehicle_id=v["vehicle_id"],
            vehicle_number=v["vehicle_number"],
            display_name=f"{v['vehicle_id']} (#{v['vehicle_number']})"
        )
        for v in vehicles
    ]

    return VehiclesResponse(
        vehicles=vehicle_list,
        session_id=session_id
    )
