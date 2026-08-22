from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import User
import uuid

def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return list(db.execute(select(User).offset(skip).limit(limit)).scalars().all())
