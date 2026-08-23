import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

class GroqService:
    """
    Service to handle LLM inferences via Groq.
    Built for ultra-low latency voice responses.
    """
    def __init__(self):
        # Import dynamically to avoid crashing if library is missing locally
        try:
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "mock_key"))
            self.model = "llama3-8b-8192" # Fast model suitable for conversational voice
            self.enabled = True
        except ImportError:
            logger.warning("groq library not installed. LLM service will use mock mode.")
            self.client = None
            self.enabled = False

    async def generate_response(self, system_prompt: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Generate a conversational response given a system context and message history.
        """
        if not self.enabled or not self.client:
            return "I am a mock AI response since the Groq API key or library is missing."

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.5,
                max_tokens=150, # Keep voice responses concise
            )
            return chat_completion.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "I'm sorry, I'm having trouble processing that right now."

llm_service = GroqService()
