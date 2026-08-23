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

class UserProvisionRequest(BaseModel):
    email: EmailStr
    display_name: str
    role_name: str  # SUPER_ADMIN, ADMIN, or EMPLOYEE
    department_id: Optional[uuid.UUID] = None

class ProvisionResponse(BaseModel):
    user: UserResponse
    temporary_password: str
