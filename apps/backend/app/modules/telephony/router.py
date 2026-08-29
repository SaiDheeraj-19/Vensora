import json
import logging
from fastapi import APIRouter, Request, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse
from typing import Dict, Any

from .event_handler import TwilioEventHandler

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active admin dashboard websocket connections
active_connections: list[WebSocket] = []

@router.websocket("/ws/live-calls")
async def live_calls_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for the Admin Dashboard to monitor live calls.
    """
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_call_update(call_id: str, state: str, caller_id: str = "Unknown"):
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

@router.post("/twilio/incoming")
async def twilio_incoming(request: Request):
    """
    Webhook called by Twilio when a user dials the Vensora phone number.
    We return TwiML to connect the call to our Media Stream WebSocket.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    caller = form_data.get("From", "unknown")
    logger.info(f"Incoming call from {caller} (CallSid: {call_sid})")
    
    # The host header gives us the domain ngrok or production uses
    host = request.headers.get("host")
    # Force wss:// since Twilio requires secure websockets for media streams
    # (except for raw localhost testing which we don't do directly with Twilio)
    protocol = "wss" if host and "localhost" not in host else "ws"
    
    stream_url = f"{protocol}://{host}/api/v1/telephony/twilio/stream"
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting to Vensora A I</Say>
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="caller" value="{caller}" />
        </Stream>
    </Connect>
</Response>"""

    return Response(content=twiml, media_type="text/xml")

@router.websocket("/twilio/stream")
async def twilio_stream(websocket: WebSocket):
    """
    WebSocket endpoint that receives the live bidirectional audio stream from Twilio.
    """
    await websocket.accept()
    logger.info("Twilio WebSocket connected.")
    
    # We pass the raw websocket directly to the Event Handler to manage the stream lifecycle
    try:
        await TwilioEventHandler.handle_stream(websocket)
    except WebSocketDisconnect:
        logger.info("Twilio WebSocket disconnected normally.")
    except Exception as e:
        logger.error(f"Twilio WebSocket Error: {e}")
        
@router.get("/health")
async def telephony_health():
    """
    Check connectivity.
    """
    return {"status": "ok", "provider": "twilio"}
