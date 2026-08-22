from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

def verify_google_token(token: str) -> dict | None:
    """
    Verifies a Google ID token and returns the decoded token payload.
    If the token is invalid, returns None.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        return idinfo
    except ValueError as e:
        logger.warning(f"Invalid Google token: {e}")
        return None
