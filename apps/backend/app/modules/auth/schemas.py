from pydantic import BaseModel
import uuid

class GoogleLoginRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    must_change_password: bool
    status: str
