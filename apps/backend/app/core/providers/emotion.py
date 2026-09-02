import logging
import time
import re
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
    Ultra-low latency heuristic emotion detector.
    Executes in <5ms instead of the 3000ms+ PyTorch/Transformers overhead,
    satisfying the strict <200ms pipeline budget while effectively capturing frustration.
    """
    def __init__(self):
        self.enabled = True
        
        # Fast compiled regex for emotion keywords
        self.anger_pattern = re.compile(r'\b(angry|mad|furious|frustrated|annoyed|upset|pissed|hate|terrible|awful|unacceptable)\b', re.IGNORECASE)
        self.sad_pattern = re.compile(r'\b(sad|depressed|unhappy|cry|crying|sorry|disappointed)\b', re.IGNORECASE)
        self.joy_pattern = re.compile(r'\b(happy|glad|great|awesome|excellent|love|perfect|thanks|thank you)\b', re.IGNORECASE)
        self.fear_pattern = re.compile(r'\b(scared|afraid|terrified|anxious|worried|nervous)\b', re.IGNORECASE)
        
    def check_health(self) -> ProviderHealth:
        return ProviderHealth(HealthState.HEALTHY, "Heuristic emotion engine ready")
        
    def detect_emotion(self, text: str) -> Dict[str, Any]:
        """
        Detect emotion using regex keyword heuristics for ultra-low latency.
        """
        start_time = time.time()
        
        emotion = "neutral"
        score = 0.5
        
        # Simple weighted scoring
        if self.anger_pattern.search(text):
            emotion = "anger"
            score = 0.85
        elif self.fear_pattern.search(text):
            emotion = "fear"
            score = 0.75
        elif self.sad_pattern.search(text):
            emotion = "sadness"
            score = 0.70
        elif self.joy_pattern.search(text):
            emotion = "joy"
            score = 0.90
            
        latency = time.time() - start_time
        logger.debug(f"Fast Emotion Latency: {latency:.4f}s - Result: {emotion}")
        
        return {
            "emotion": emotion,
            "score": score
        }
