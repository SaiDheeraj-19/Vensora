import logging
import os
import json
from abc import abstractmethod
from typing import Optional, Any
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class CacheProvider(BaseProvider):
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass
        
    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

class RedisProvider(CacheProvider):
    """
    Redis implementation for caching, rate limiting, and temporary state.
    """
    def __init__(self):
        self.settings = get_settings()
        self.enabled = True
        self.redis = None
        
        try:
            import redis.asyncio as aioredis
            
            # Connection pooling configuration
            url = f"redis://{self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}"
            self.redis = aioredis.from_url(
                url, 
                encoding="utf-8", 
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
                retry_on_timeout=True
            )
            logger.info("RedisProvider initialized.")
        except ImportError:
            logger.warning("redis library not installed. Cache running in MOCK mode.")
            self.enabled = False
            self.redis = None

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled:
            return ProviderHealth(HealthState.MOCK, "Redis library missing")
        try:
            await self.redis.ping()
            return ProviderHealth(HealthState.HEALTHY)
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return ProviderHealth(HealthState.UNAVAILABLE, str(e))

    async def get(self, key: str) -> Optional[str]:
        if not self.enabled:
            return None
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        if not self.enabled:
            return True
        try:
            await self.redis.set(key, value, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.enabled:
            return True
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE failed for key {key}: {e}")
            return False
