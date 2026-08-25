import logging
import os
from abc import abstractmethod
from typing import Dict, Any
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class CRMProvider(BaseProvider):
    @abstractmethod
    async def get_customer(self, phone_number: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_shipment_status(self, tracking_number: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def create_ticket(self, customer_id: str, issue_summary: str) -> Dict[str, Any]:
        pass

class CompanyCRMProvider(CRMProvider):
    """
    Adapter for the logistics company's actual CRM and TMS (Transportation Management System).
    Currently implemented as a circuit-breaker ready wrapper pending actual company credentials.
    """
    def __init__(self):
        self.settings = get_settings()
        
        # [REQUIRED FROM COMPANY]
        self.api_key = os.getenv("COMPANY_CRM_API_KEY")
        self.base_url = os.getenv("COMPANY_CRM_URL", "https://api.company-crm.example.com")
        self.enabled = bool(self.api_key)
        
        # Circuit Breaker state
        self.failures = 0
        self.max_failures = 3
        
        try:
            import httpx
            if self.enabled:
                # Configure timeouts and retries for robust external integration
                self.client = httpx.AsyncClient(
                    base_url=self.base_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=httpx.Timeout(5.0, read=15.0)
                )
                logger.info("CompanyCRMProvider initialized.")
            else:
                self.client = None
                logger.warning("COMPANY_CRM_API_KEY not set. CRM running in MOCK mode.")
        except ImportError:
            logger.warning("httpx not installed. CRM running in MOCK mode.")
            self.client = None
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled or not self.client:
            return ProviderHealth(HealthState.MOCK, "COMPANY_CRM_API_KEY required from company")
            
        if self.failures >= self.max_failures:
            return ProviderHealth(HealthState.UNAVAILABLE, "Circuit breaker open due to successive failures")
            
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            self.failures = 0 # Reset circuit breaker
            return ProviderHealth(HealthState.HEALTHY)
        except Exception as e:
            self.failures += 1
            return ProviderHealth(HealthState.UNAVAILABLE, str(e))

    async def get_customer(self, phone_number: str) -> Dict[str, Any]:
        if not self.enabled or not self.client:
            logger.info(f"MOCK CRM: Looking up customer with phone {phone_number}")
            return {"customer_id": "CUST-999", "name": "Mock Customer", "status": "active"}
            
        try:
            response = await self.client.get(f"/customers/search", params={"phone": phone_number})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CRM Customer Lookup failed: {e}")
            raise

    async def get_shipment_status(self, tracking_number: str) -> Dict[str, Any]:
        if not self.enabled or not self.client:
            logger.info(f"MOCK CRM: Looking up shipment {tracking_number}")
            return {"tracking_number": tracking_number, "status": "In Transit", "location": "Mock Hub"}
            
        try:
            response = await self.client.get(f"/shipments/{tracking_number}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CRM Shipment Lookup failed: {e}")
            raise

    async def create_ticket(self, customer_id: str, issue_summary: str) -> Dict[str, Any]:
        if not self.enabled or not self.client:
            logger.info(f"MOCK CRM: Creating ticket for {customer_id}: {issue_summary}")
            return {"ticket_id": "TICKET-999", "status": "open"}
            
        try:
            # Non-idempotent operation - do not blindly retry
            response = await self.client.post("/tickets", json={
                "customer_id": customer_id,
                "summary": issue_summary
            })
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CRM Ticket Creation failed: {e}")
            raise
