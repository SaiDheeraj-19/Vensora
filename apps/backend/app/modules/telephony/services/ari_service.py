import httpx
from typing import Dict, Any, Optional
import logging
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class ARIService:
    """
    Service for interacting with Asterisk REST Interface (ARI).
    """
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"http://{self.settings.ASTERISK_HOST}:{self.settings.ASTERISK_PORT}/ari"
        self.auth = (self.settings.ASTERISK_ARI_USER, self.settings.ASTERISK_ARI_PASSWORD)
        self.app_name = self.settings.ASTERISK_APP_NAME
        
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generic method to make ARI requests."""
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        params['app'] = self.app_name
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    auth=self.auth,
                    params=params,
                    json=json_data
                )
                response.raise_for_status()
                # ARI might return 204 No Content
                if response.status_code == 204:
                    return {}
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"ARI Request failed: {str(e)}")
                raise

    async def answer_channel(self, channel_id: str) -> bool:
        """Answers an incoming channel."""
        logger.info(f"Answering channel {channel_id}")
        await self._make_request("POST", f"/channels/{channel_id}/answer")
        return True

    async def hangup_channel(self, channel_id: str, reason: str = "normal") -> bool:
        """Hangs up a channel."""
        logger.info(f"Hanging up channel {channel_id}, reason: {reason}")
        await self._make_request("DELETE", f"/channels/{channel_id}", params={"reason": reason})
        return True
        
    async def play_media(self, channel_id: str, media_uri: str) -> str:
        """Plays media to a channel and returns the playback ID."""
        logger.info(f"Playing {media_uri} on channel {channel_id}")
        result = await self._make_request(
            "POST", 
            f"/channels/{channel_id}/play",
            params={"media": media_uri}
        )
        return result.get("id", "")
        
    async def start_recording(self, channel_id: str, name: str, format: str = "wav") -> str:
        """Starts recording a channel."""
        logger.info(f"Starting recording {name} on channel {channel_id}")
        result = await self._make_request(
            "POST",
            f"/channels/{channel_id}/record",
            params={
                "name": name,
                "format": format,
                "maxDurationSeconds": 0,
                "maxSilenceSeconds": 0,
                "ifExists": "overwrite"
            }
        )
        return result.get("name", "")
