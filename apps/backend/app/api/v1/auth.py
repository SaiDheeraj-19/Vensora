from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.auth.schemas import GoogleLoginRequest, TokenResponse
from app.modules.auth.service import authenticate_google_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/google", response_model=TokenResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a Super Admin using a Google ID token.
    """
    return authenticate_google_user(db, request)
