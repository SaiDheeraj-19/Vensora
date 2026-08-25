import logging
from typing import Dict, Type, Any
from app.core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """
    Central registry for managing provider singletons and interfaces.
    Allows easy swapping of implementations for testing or Phase 2 migrations.
    """
    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        
    def register(self, interface_name: str, provider: BaseProvider):
        logger.info(f"Registering provider '{provider.__class__.__name__}' for interface '{interface_name}'")
        self._providers[interface_name] = provider
        
    def get(self, interface_name: str) -> BaseProvider:
        provider = self._providers.get(interface_name)
        if not provider:
            raise ValueError(f"No provider registered for interface '{interface_name}'")
        return provider

# Global registry instance
registry = ProviderRegistry()
