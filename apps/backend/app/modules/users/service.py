from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import User
import uuid

def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return list(db.execute(select(User).offset(skip).limit(limit)).scalars().all())

def provision_user(db: Session, request: "UserProvisionRequest", created_by: User) -> tuple[User, str]:
    from fastapi import HTTPException, status
    from app.modules.roles.models import Role
    from app.security.password import generate_temporary_password, get_password_hash
    from app.modules.users.models import UserStatus
    
    # 1. Check if user already exists
    existing_user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    # 2. Get the role
    role = db.execute(select(Role).where(Role.name == request.role_name)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{request.role_name}' not found")
        
    # 3. Generate secure temporary password
    temp_password = generate_temporary_password()
    hashed_password = get_password_hash(temp_password)
    
    # 4. Create user
    new_user = User(
        email=request.email,
        display_name=request.display_name,
        role_id=role.id,
        department_id=request.department_id,
        status=UserStatus.PENDING, # Or ACTIVE, depending on business rules. Prompt says MUST change password.
        password_hash=hashed_password,
        must_change_password=True,
        created_by=created_by.id,
        auth_provider="local"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user, temp_password
