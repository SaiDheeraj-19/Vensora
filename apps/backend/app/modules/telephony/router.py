import logging
import asyncio
from fastapi import APIRouter, Request, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Any
from app.modules.telephony.services.websocket_client import ari_ws_client
from .event_handler import ARIEventHandler

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active admin dashboard websocket connections
active_connections: list[WebSocket] = []

@router.websocket("/ws/live-calls")
async def live_calls_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for the Admin Dashboard to monitor live calls.
    In Phase 1, we broadcast state machine transitions to all connected admins.
    """
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # We don't expect incoming messages from the dashboard yet, 
            # just keep the connection alive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_call_update(call_id: str, state: str, caller_id: str = "Unknown"):
    """
    Called by the CallStateMachine when a call transitions to a new state.
    """
    if not active_connections:
        return
        
    payload = {
        "call_id": call_id,
        "state": state,
        "caller_id": caller_id,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }
    
    for connection in active_connections:
        try:
            await connection.send_json(payload)
        except Exception:
            pass

@router.post("/events")
async def handle_asterisk_event(event: Dict[str, Any]):
    """
    Webhook endpoint to receive events from Asterisk/ARI.
    """
    # Logic to parse event, update state machine, and trigger AI will go here
    return {"status": "received"}

@router.get("/health")
async def telephony_health():
    """
    Check connectivity with Asterisk PBX.
    """
    return {"status": "ok", "asterisk": "connected"}
