"""
WebSocket API for real-time race data updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
import logging
from services.race_service import get_race_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.race_subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, race_id: str = "R1"):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # Add to race-specific subscriptions
        if race_id not in self.race_subscriptions:
            self.race_subscriptions[race_id] = []
        self.race_subscriptions[race_id].append(websocket)

        logger.info(f"WebSocket connected for race {race_id}. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all race subscriptions
        for race_id in self.race_subscriptions:
            if websocket in self.race_subscriptions[race_id]:
                self.race_subscriptions[race_id].remove(websocket)

        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict, race_id: str = None):
        """Broadcast message to all clients or race-specific clients"""
        connections = (
            self.race_subscriptions.get(race_id, [])
            if race_id
            else self.active_connections
        )

        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/race/{race_id}/{vehicle_id}")
async def race_data_stream(websocket: WebSocket, race_id: str, vehicle_id: str):
    """
    WebSocket endpoint for real-time race data streaming

    Args:
        race_id: Race session identifier (R1, R2)
        vehicle_id: Vehicle to monitor

    Sends updates every 1-2 seconds with:
    - Current pace
    - Degradation status
    - Threat analysis
    - Pit recommendations
    """
    await manager.connect(websocket, race_id)
    service = get_race_service()

    try:
        # Initial state
        current_lap = 1
        total_laps = 27  # Typical GR Cup race length

        # Send initial connection confirmation
        await manager.send_personal_message(
            {
                "type": "connection_established",
                "race_id": race_id,
                "vehicle_id": vehicle_id,
                "message": "Connected to real-time race data stream",
            },
            websocket,
        )

        # Main update loop
        while True:
            try:
                # Receive client messages (for lap updates, commands)
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=0.1
                )
                message = json.loads(data)

                # Handle lap update from client
                if message.get("type") == "lap_update":
                    current_lap = message.get("lap", current_lap)

            except asyncio.TimeoutError:
                # No message from client, continue with updates
                pass
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from client")
                continue

            # Gather all race data
            race_update = await get_race_update(
                service, vehicle_id, current_lap, total_laps, race_id
            )

            # Send update to client
            await manager.send_personal_message(race_update, websocket)

            # Wait before next update (2 second interval)
            await asyncio.sleep(2.0)

            # Simulate lap progression (for demo purposes)
            # In production, this would come from actual race timing
            if current_lap < total_laps:
                current_lap += 0.1  # Gradual progression

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected: {vehicle_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def get_race_update(
    service,
    vehicle_id: str,
    current_lap: int,
    total_laps: int,
    race_id: str
) -> Dict:
    """
    Gather all race data for update

    Returns comprehensive race state including pace, degradation, threats, pit window
    """
    try:
        current_lap_int = int(current_lap)

        # Get pace data
        pace_data = service.get_current_pace(
            vehicle_id=vehicle_id,
            race=race_id,
            window_size=5
        )

        # Get degradation analysis
        degradation_data = service.analyze_degradation(
            vehicle_id=vehicle_id,
            current_lap=current_lap_int,
            race=race_id
        )

        # Get threat detection (simplified - single rival)
        threat_data = service.detect_threat(
            vehicle_id=vehicle_id,
            rival_id="GR86-001-10",
            current_lap=current_lap_int,
            current_gap=2.5,
            race=race_id
        )

        # Get pit window recommendation
        pit_data = service.optimize_pit_window(
            vehicle_id=vehicle_id,
            current_lap=current_lap_int,
            current_position=5,
            total_laps=total_laps,
            race=race_id
        )

        return {
            "type": "race_update",
            "timestamp": asyncio.get_event_loop().time(),
            "vehicle_id": vehicle_id,
            "race_id": race_id,
            "current_lap": current_lap_int,
            "total_laps": total_laps,
            "pace": {
                "current": pace_data.get("current_pace", 0.0),
                "average": pace_data.get("average_pace", 0.0),
                "best": pace_data.get("best_lap", 0.0),
                "trend": pace_data.get("pace_trend", "stable"),
            },
            "degradation": {
                "rate": degradation_data.get("degradation_rate", 0.0),
                "health": degradation_data.get("stint_health", "optimal"),
                "action": degradation_data.get("recommended_action", "Monitor"),
            },
            "threat": {
                "level": threat_data.get("threat_level", "low"),
                "probability": threat_data.get("attack_probability", 0.0),
                "laps_until": threat_data.get("laps_until_threat", 999),
                "recommendations": threat_data.get("defensive_recommendations", []),
            },
            "pit_window": {
                "optimal_lap": pit_data.get("recommended_lap", current_lap_int + 5),
                "window_start": pit_data.get("optimal_window_start", current_lap_int + 3),
                "window_end": pit_data.get("optimal_window_end", current_lap_int + 7),
                "confidence": pit_data.get("confidence", 0.7),
            },
        }

    except Exception as e:
        logger.error(f"Error gathering race update: {e}")
        return {
            "type": "error",
            "message": str(e),
            "vehicle_id": vehicle_id,
        }


@router.websocket("/broadcast/{race_id}")
async def race_broadcast(websocket: WebSocket, race_id: str):
    """
    Broadcast endpoint for race-wide updates

    Sends updates about all vehicles in a race
    Useful for timing screens and overall race status
    """
    await manager.connect(websocket, race_id)

    try:
        await manager.send_personal_message(
            {
                "type": "broadcast_connected",
                "race_id": race_id,
                "message": "Connected to race broadcast stream",
            },
            websocket,
        )

        while True:
            # Broadcast race-wide updates every 5 seconds
            await asyncio.sleep(5.0)

            broadcast_data = {
                "type": "race_broadcast",
                "race_id": race_id,
                "timestamp": asyncio.get_event_loop().time(),
                "message": "Race broadcast update",
                # Add race-wide data here (leaderboard, etc.)
            }

            await manager.broadcast(broadcast_data, race_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        manager.disconnect(websocket)
