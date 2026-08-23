from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.dependencies.auth import get_current_user, RequirePermission
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse, UserProvisionRequest, ProvisionResponse
from app.modules.users.service import get_user, list_users, provision_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/provision", response_model=ProvisionResponse, status_code=status.HTTP_201_CREATED)
def provision_new_user(
    request: UserProvisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequirePermission("users:create"))
):
    """
    Provision a new Admin or Employee. Requires 'users:create' permission.
    Returns the created user and their temporary, one-time password.
    """
    user, temp_password = provision_user(db, request, current_user)
    return ProvisionResponse(user=user, temporary_password=temp_password)

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Get the currently authenticated user's profile.
    """
    return current_user

@router.get("/", response_model=list[UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(RequirePermission("users:read"))
):
    """
    Retrieve a list of users. Requires 'users:read' permission.
    """
    users = list_users(db, skip=skip, limit=limit)
    return users
