from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
import uuid
from typing import Optional

class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: Optional[str] = None
    display_name: str
    status: str
    role: RoleResponse
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
