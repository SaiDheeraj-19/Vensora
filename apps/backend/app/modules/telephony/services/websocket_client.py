import asyncio
import websockets
import json
import logging
from typing import Optional

from app.config.settings import get_settings
from app.modules.telephony.event_handler import ARIEventHandler

logger = logging.getLogger(__name__)

class ARIWebSocketClient:
    """
    Connects to Asterisk ARI WebSockets to listen for real-time events.
    """
    def __init__(self):
        self.settings = get_settings()
        self.uri = f"ws://{self.settings.ASTERISK_HOST}:{self.settings.ASTERISK_PORT}/ari/events?app={self.settings.ASTERISK_APP_NAME}&api_key={self.settings.ASTERISK_ARI_USER}:{self.settings.ASTERISK_ARI_PASSWORD}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.reconnect_delay = 5
        self._running = False

    async def connect(self):
        self._running = True
        while self._running:
            try:
                logger.info(f"Connecting to ARI WebSocket at {self.settings.ASTERISK_HOST}:{self.settings.ASTERISK_PORT}")
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    logger.info("Connected to Asterisk ARI WebSocket")
                    await self._listen()
            except Exception as e:
                logger.error(f"ARI WebSocket connection failed: {e}")
                if self._running:
                    logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)

    async def _listen(self):
        if not self.websocket:
            return
            
        try:
            async for message in self.websocket:
                try:
                    event_data = json.loads(message)
                    ARIEventHandler.handle_event(event_data)
                except json.JSONDecodeError:
                    logger.error(f"Received invalid JSON from ARI: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("ARI WebSocket connection closed.")
            
    async def disconnect(self):
        self._running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from Asterisk ARI WebSocket")

ari_ws_client = ARIWebSocketClient()
