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
            from app.modules.crm.models import PromptStatus
            db: Session = SessionLocal()
            prompt = db.query(PromptTemplate).filter(
                PromptTemplate.name == name, 
                PromptTemplate.status == PromptStatus.ACTIVE
            ).order_by(PromptTemplate.version.desc()).first()
            db.close()
            
            if prompt:
                _PROMPT_CACHE[name] = prompt.content
                return prompt.content
        except Exception as e:
            logger.error(f"Failed to fetch prompt '{name}' from DB: {e}")
            
        fallback = (
            "You are a human customer support agent named Vensora. You must act 100% human at all times. "
            "Never reveal you are an AI or virtual assistant. Speak like a real human on a phone call. "
            "Use natural filler words occasionally like 'umm', 'well', or 'let's see'. "
            "Be highly empathetic and perfectly match your tone to the user's emotional state. "
            "Keep your answers brief, conversational, and completely free of markdown or bullet points. "
            "CRITICAL GUARDRAIL: You must ONLY use the provided knowledge base to answer questions. "
            "If the user asks anything that is not explicitly covered in the knowledge base, you MUST politely refuse to answer. "
            "Say something like 'I'm sorry, I actually don't have that information in front of me right now.' "
            "Do NOT invent facts, assume things, or use outside knowledge. "
            "Use the following KNOWLEDGE BASE to answer questions:\n\n"
        )
        try:
            with open("/Users/saidheeraj/LocalProjects/vensora/sample_docs/AI_Contact_Center_Phase1_ISP_Consolidated_Sample_Pack.txt", "r") as f:
                fallback += f.read(5000)
        except BaseException:
            pass
        _PROMPT_CACHE[name] = fallback
        return fallback

    def invalidate_cache(self, name: str = None):
        """Called by the Admin API when a prompt is updated."""
        if name and name in _PROMPT_CACHE:
            del _PROMPT_CACHE[name]
        elif not name:
            _PROMPT_CACHE.clear()

prompt_service = PromptService()
