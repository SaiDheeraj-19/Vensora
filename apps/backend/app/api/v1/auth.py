from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.auth.schemas import GoogleLoginRequest, TokenResponse, EmailLoginRequest, PasswordChangeRequest
from app.modules.auth.service import authenticate_google_user, authenticate_local_user, change_password
from app.api.dependencies.auth import get_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/google", response_model=TokenResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a Super Admin using a Google ID token.
    """
    return authenticate_google_user(db, request)

@router.post("/login", response_model=TokenResponse)
def local_login(request: EmailLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate an Admin/Employee using email and password.
    """
    return authenticate_local_user(db, request)

@router.post("/change-password", response_model=TokenResponse)
def change_initial_password(
    request: PasswordChangeRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change password. Required for first-time login by Admin/Employees.
    Uses get_current_user to bypass the get_active_user block.
    """
    return change_password(db, current_user, request)
