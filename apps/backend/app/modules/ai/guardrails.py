import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

class GuardrailService:
    """
    Rapid heuristic checks to prevent prompt injections and off-topic requests.
    These run before the LLM is invoked to save tokens and ensure safety.
    """
    def __init__(self):
        # Basic regex patterns for phase 1 prompt injection detection
        self.injection_patterns = [
            re.compile(r"ignore previous instructions", re.IGNORECASE),
            re.compile(r"system prompt", re.IGNORECASE),
            re.compile(r"forget everything", re.IGNORECASE),
            re.compile(r"you are now", re.IGNORECASE),
            re.compile(r"print your instructions", re.IGNORECASE)
        ]
        
    def check_utterance(self, utterance: str) -> Tuple[bool, str]:
        """
        Checks if the utterance violates any guardrails.
        Returns (is_safe, rejection_reason).
        """
        # 1. Injection Checks
        for pattern in self.injection_patterns:
            if pattern.search(utterance):
                logger.warning(f"Guardrail triggered: Possible prompt injection detected in utterance.")
                return False, "PROMPT_INJECTION"
                
        # 2. Length Checks
        if len(utterance) > 1000:
            logger.warning(f"Guardrail triggered: Utterance too long ({len(utterance)} chars).")
            return False, "EXCESSIVE_LENGTH"
            
        # In a real enterprise system, we might also call a fast classifier model here to detect PII
        # or off-topic rants.
        
        return True, ""

guardrail_service = GuardrailService()
