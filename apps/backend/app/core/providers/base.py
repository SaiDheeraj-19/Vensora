import enum
from abc import ABC, abstractmethod
from typing import Any, Dict

class HealthState(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    MOCK = "MOCK"

class ProviderHealth:
    def __init__(self, state: HealthState, details: str = ""):
        self.state = state
        self.details = details

class BaseProvider(ABC):
    """
    Abstract base class for all external infrastructure and API providers.
    """
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Return True if the provider is enabled via configuration."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Return the current health state of the provider connection."""
        pass
