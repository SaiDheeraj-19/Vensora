import logging
import os
import time
from abc import abstractmethod
from typing import Dict, Any
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class EmotionProvider(BaseProvider):
    @abstractmethod
    def detect_emotion(self, text: str) -> Dict[str, Any]:
        """
        Analyze the text and return the primary emotion and confidence score.
        Expected return format: {"emotion": "anger", "score": 0.95}
        """
        pass

class LocalTextEmotionProvider(EmotionProvider):
    """
    Local Text-based Emotion detection using a lightweight HuggingFace pipeline.
    """
    def __init__(self, model_name: str = "bhadresh-savani/distilbert-base-uncased-emotion"):
        self.settings = get_settings()
        self.model_name = model_name
        self.enabled = os.getenv("EMOTION_ENABLED", "true").lower() == "true"
        self._pipeline = None
        self._initialized = False
        
        try:
            import transformers
        except ImportError:
            logger.warning("transformers not installed. Emotion detection running in MOCK mode.")
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled:
            return ProviderHealth(HealthState.MOCK, "EMOTION_ENABLED is false or transformers missing")
        return ProviderHealth(HealthState.HEALTHY)

    def _initialize(self):
        if not self._initialized and self.enabled:
            try:
                from transformers import pipeline
                logger.info(f"Loading emotion classification model: {self.model_name}")
                # We use pipeline for quick and easy sentiment/emotion classification
                self._pipeline = pipeline("text-classification", model=self.model_name, top_k=1)
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to load emotion model: {e}")
                self.enabled = False

    def detect_emotion(self, text: str) -> Dict[str, Any]:
        start_time = time.time()
        
        if not self.enabled:
            latency = time.time() - start_time
            logger.debug(f"MOCK Emotion Latency: {latency:.3f}s")
            return {"emotion": "neutral", "score": 1.0}
            
        self._initialize()
        
        try:
            # Result format from pipeline(top_k=1): [[{'label': 'anger', 'score': 0.98}]]
            results = self._pipeline(text)
            top_result = results[0][0]
            emotion = top_result['label'].lower()
            score = top_result['score']
            
            latency = time.time() - start_time
            logger.info(f"Emotion detected: '{emotion}' (score: {score:.2f}) in {latency:.3f}s")
            
            return {"emotion": emotion, "score": score}
        except Exception as e:
            logger.error(f"Emotion detection failed: {e}")
            return {"emotion": "neutral", "score": 1.0}
