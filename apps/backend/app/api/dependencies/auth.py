from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.database.session import get_db
from app.security.jwt import verify_token
from app.modules.users.models import User, UserStatus
from app.modules.roles.models import Role, RolePermission, Permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
        
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
        
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception
        
    # Eagerly load role and permissions
    stmt = (
        select(User)
        .options(
            joinedload(User.role).joinedload(Role.permissions).joinedload(RolePermission.permission)
        )
        .where(User.id == user_id)
    )
    user = db.execute(stmt).unique().scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    if user.status not in (UserStatus.ACTIVE, UserStatus.PENDING):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Inactive user account: {user.status.value}"
        )
        
    return user

def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure the user has completed their mandatory first-login password change.
    Use this for all normal business APIs.
    """
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must change your initial password before accessing the system."
        )
    return current_user

class RequirePermission:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
        
    def __call__(self, current_user: User = Depends(get_active_user)):
        # Extract all permission strings for the user's role
        user_permissions = {rp.permission.name for rp in current_user.role.permissions}
        
        # Super admin wildcard bypass
        if "*" in user_permissions:
            return current_user
            
        if self.required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {self.required_permission}"
            )
            
        return current_user
