import logging
import os
import time
from abc import abstractmethod
from typing import Optional, Dict, Any, List
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class LLMProvider(BaseProvider):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Generate a response from the LLM. 
        Returns a dict containing 'content', 'tool_calls', and 'usage' metrics.
        """
        pass

class GroqProvider(LLMProvider):
    """
    Groq implementation for low-latency LLM inference.
    """
    def __init__(self):
        self.settings = get_settings()
        # Fallback to env var if not in settings
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
        self.enabled = bool(self.api_key)
        
        try:
            from openai import AsyncOpenAI
            if self.enabled:
                self.client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key, 
                    timeout=10.0
                )
                logger.info("OpenRouterProvider initialized.")
            else:
                self.client = None
                logger.warning("OPENROUTER_API_KEY not set. LLM running in MOCK mode.")
        except ImportError:
            logger.warning("openai library not installed. LLM running in MOCK mode.")
            self.client = None
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled or not self.client:
            return ProviderHealth(HealthState.MOCK, "groq client missing or api key not set")
        try:
            # Simple models list fetch to verify API key validity
            await self.client.models.list()
            return ProviderHealth(HealthState.HEALTHY)
        except Exception as e:
            return ProviderHealth(HealthState.UNAVAILABLE, str(e))

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        
        if not self.enabled or not self.client:
            latency = time.time() - start_time
            logger.info(f"MOCK TTFT: {latency:.3f}s")
            return {
                "content": "I am a mock AI response since the Groq API key is missing.",
                "tool_calls": None,
                "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
            }
            
        try:
            # We track time to first token if we were streaming, but for this basic 
            # abstraction we will track total request latency.
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            
            latency = time.time() - start_time
            
            # Extract metrics
            usage = response.usage
            logger.info(f"Groq LLM Latency: {latency:.3f}s | Tokens: {usage.total_tokens} (P: {usage.prompt_tokens}, C: {usage.completion_tokens})")
            
            message = response.choices[0].message
            return {
                "content": message.content,
                "tool_calls": message.tool_calls,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
