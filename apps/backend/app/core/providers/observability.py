import logging
import os
import time
from typing import Dict, Any
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState

logger = logging.getLogger(__name__)

class ObservabilityProvider(BaseProvider):
    """
    Provider interface for tracking metrics and emitting structured logs.
    """
    
    def __init__(self):
        self.enabled = True
        self._metrics_registry = None
        
        try:
            import prometheus_client
            from prometheus_client import Counter, Histogram
            
            # Setup basic metrics
            self.request_counter = Counter(
                "vensora_api_requests_total",
                "Total number of API requests",
                ["method", "endpoint", "status"]
            )
            
            self.llm_ttft_histogram = Histogram(
                "vensora_llm_ttft_seconds",
                "Time to first token for LLM inference"
            )
            
            self.stt_latency_histogram = Histogram(
                "vensora_stt_latency_seconds",
                "Latency of Faster Whisper transcription"
            )
            
            self.tts_latency_histogram = Histogram(
                "vensora_tts_latency_seconds",
                "Latency of Piper TTS synthesis"
            )
            
            logger.info("Prometheus ObservabilityProvider initialized.")
        except ImportError:
            logger.warning("prometheus_client not installed. Observability running in MOCK mode.")
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled:
            return ProviderHealth(HealthState.MOCK, "prometheus_client missing")
        return ProviderHealth(HealthState.HEALTHY)

    def track_api_request(self, method: str, endpoint: str, status: int):
        if self.enabled:
            self.request_counter.labels(method=method, endpoint=endpoint, status=status).inc()

    def track_llm_ttft(self, latency_seconds: float):
        if self.enabled:
            self.llm_ttft_histogram.observe(latency_seconds)

    def track_stt_latency(self, latency_seconds: float):
        if self.enabled:
            self.stt_latency_histogram.observe(latency_seconds)

    def track_tts_latency(self, latency_seconds: float):
        if self.enabled:
            self.tts_latency_histogram.observe(latency_seconds)
