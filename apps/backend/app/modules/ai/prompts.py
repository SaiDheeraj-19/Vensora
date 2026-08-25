import logging
from sqlalchemy.orm import Session
from app.modules.crm.models import PromptTemplate
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)

# Simple in-memory cache to avoid querying the DB on every single turn of the conversation
_PROMPT_CACHE = {}

class PromptService:
    def get_system_prompt(self, name: str = "core_system_prompt") -> str:
        """
        Fetch the active prompt template by name.
        Uses a local cache; falls back to a hardcoded default if the DB fetch fails or is missing.
        """
        if name in _PROMPT_CACHE:
            return _PROMPT_CACHE[name]
            
        try:
            db: Session = SessionLocal()
            prompt = db.query(PromptTemplate).filter(PromptTemplate.name == name, PromptTemplate.is_active == True).first()
            db.close()
            
            if prompt:
                _PROMPT_CACHE[name] = prompt.content
                return prompt.content
        except Exception as e:
            logger.error(f"Failed to fetch prompt '{name}' from DB: {e}")
            
        # Hardcoded default fallback
        fallback = (
            "You are Vensora, an intelligent enterprise AI assistant. "
            "Keep your answers brief, professional, and conversational. "
            "You are speaking over the phone. Do not use markdown."
        )
        _PROMPT_CACHE[name] = fallback
        return fallback

    def invalidate_cache(self, name: str = None):
        """Called by the Admin API when a prompt is updated."""
        if name and name in _PROMPT_CACHE:
            del _PROMPT_CACHE[name]
        elif not name:
            _PROMPT_CACHE.clear()

prompt_service = PromptService()
