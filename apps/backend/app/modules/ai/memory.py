import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages short-term conversation history for token optimization and 
    extracts long-term facts to store in CustomerProfile.
    """
    def __init__(self, max_history_turns: int = 5):
        self.max_history_turns = max_history_turns

    def optimize_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Keeps only the system prompt and the last N turns to prevent token explosion.
        (A turn is usually a user message + assistant response).
        """
        if not messages:
            return []
            
        system_msgs = [m for m in messages if m.get("role") == "system"]
        conversation = [m for m in messages if m.get("role") != "system"]
        
        # Keep the last (max_history_turns * 2) messages
        keep_count = self.max_history_turns * 2
        optimized_conv = conversation[-keep_count:] if len(conversation) > keep_count else conversation
        
        return system_msgs + optimized_conv
        
    def extract_long_term_facts(self, customer_id: str, messages: List[Dict[str, str]]):
        """
        [PLACEHOLDER] In a full implementation, this would spawn a background LLM task 
        to summarize the conversation and extract permanent facts (e.g., "Customer prefers morning calls")
        and save them to the CustomerProfile.metadata_tags field.
        """
        logger.debug(f"Fact extraction triggered for customer {customer_id}")
        pass

memory_manager = MemoryManager()
