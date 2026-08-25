import logging
import os
from abc import abstractmethod
from typing import Dict, Any, Optional
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class SIPProvider(BaseProvider):
    @abstractmethod
    def get_sip_configuration(self) -> Dict[str, Any]:
        """Return the SIP trunk configuration details required for Asterisk PJSIP setup."""
        pass

class CompanySIPProvider(SIPProvider):
    """
    Configuration provider for the company's real SIP trunk.
    """
    def __init__(self):
        self.settings = get_settings()
        
        # [REQUIRED FROM COMPANY]
        self.sip_host = os.getenv("SIP_HOST")
        self.sip_port = int(os.getenv("SIP_PORT", "5060"))
        self.sip_username = os.getenv("SIP_USERNAME")
        self.sip_password = os.getenv("SIP_PASSWORD")
        self.sip_transport = os.getenv("SIP_TRANSPORT", "udp")
        self.sip_did = os.getenv("SIP_DID")
        self.sip_codec = os.getenv("SIP_CODEC", "ulaw")
        
        self.enabled = bool(self.sip_host and self.sip_username and self.sip_password)

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled:
            return ProviderHealth(HealthState.MOCK, "SIP_HOST, SIP_USERNAME, SIP_PASSWORD required from company")
        # Since SIP health is typically monitored by Asterisk itself via OPTIONS pings, 
        # we return HEALTHY if the configuration is present.
        return ProviderHealth(HealthState.HEALTHY)

    def get_sip_configuration(self) -> Dict[str, Any]:
        return {
            "host": self.sip_host,
            "port": self.sip_port,
            "username": self.sip_username,
            "password": self.sip_password, # In practice, do not log this
            "transport": self.sip_transport,
            "did": self.sip_did,
            "codec": self.sip_codec
        }

class AsteriskProvider(BaseProvider):
    @abstractmethod
    async def originate_call(self, endpoint: str, extension: str, context: str) -> bool:
        pass

class ARIAsteriskProvider(AsteriskProvider):
    """
    Provider for interacting with Asterisk via the REST Interface (ARI).
    """
    def __init__(self):
        self.settings = get_settings()
        self.host = self.settings.ASTERISK_HOST
        self.port = self.settings.ASTERISK_PORT
        self.user = self.settings.ASTERISK_ARI_USER
        self.password = self.settings.ASTERISK_ARI_PASSWORD
        self.app_name = self.settings.ASTERISK_APP_NAME
        
        self.enabled = True
        
        try:
            import httpx
            self.base_url = f"http://{self.host}:{self.port}/ari"
            self.client = httpx.AsyncClient(
                auth=(self.user, self.password),
                timeout=httpx.Timeout(5.0)
            )
            logger.info("ARIAsteriskProvider initialized.")
        except ImportError:
            logger.warning("httpx not installed. Asterisk running in MOCK mode.")
            self.client = None
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled or not self.client:
            return ProviderHealth(HealthState.MOCK, "httpx missing")
        try:
            # Ping ARI
            response = await self.client.get(f"{self.base_url}/asterisk/info")
            response.raise_for_status()
            return ProviderHealth(HealthState.HEALTHY)
        except Exception as e:
            return ProviderHealth(HealthState.UNAVAILABLE, str(e))

    async def originate_call(self, endpoint: str, extension: str, context: str) -> bool:
        if not self.enabled or not self.client:
            logger.info(f"MOCK Asterisk: Originated call to {endpoint}")
            return True
        try:
            response = await self.client.post(
                f"{self.base_url}/channels",
                params={
                    "endpoint": endpoint,
                    "extension": extension,
                    "context": context,
                    "app": self.app_name
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to originate call: {e}")
            return False
