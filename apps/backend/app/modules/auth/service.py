from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from fastapi import HTTPException, status
from app.security.google import verify_google_token
from app.security.jwt import create_access_token
from app.modules.users.models import User, UserStatus
from app.modules.roles.models import Role
from .schemas import GoogleLoginRequest, TokenResponse

def authenticate_google_user(db: Session, request: GoogleLoginRequest) -> TokenResponse:
    # 1. Verify Google token
    idinfo = verify_google_token(request.token)
    if not idinfo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google token",
        )
    
    google_subject = idinfo.get("sub")
    email = idinfo.get("email")
    
    if not google_subject or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incomplete Google token payload",
        )
        
    # 2. Look up the user in DB (must already be provisioned)
    stmt = select(User).join(Role).where(
        or_(User.google_subject == google_subject, User.email == email)
    )
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not provisioned in the system",
        )
        
    # 3. Check role (must be SUPER_ADMIN for Google login in Phase 1 setup per prompt)
    if user.role.name != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can log in via Google",
        )
        
    # 4. Check user status
    if user.status not in (UserStatus.ACTIVE, UserStatus.PENDING):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}",
        )
        
    # Link google_subject if it was matched by email only
    if not user.google_subject:
        user.google_subject = google_subject
        user.auth_provider = "google"
        
    if user.status == UserStatus.PENDING:
        user.status = UserStatus.ACTIVE
        
    db.commit()
    
    # 5. Issue JWT
    access_token = create_access_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        must_change_password=user.must_change_password,
        status=user.status.value
    )
