from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID

class CallStateEnum(str, Enum):
    INITIATING = "INITIATING"
    RINGING = "RINGING"
    CONNECTED = "CONNECTED"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ESCALATING = "ESCALATING"
    TRANSFERRED = "TRANSFERRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class CallEventCreate(BaseModel):
    call_id: UUID
    state: CallStateEnum
    reason: Optional[str] = None
    metadata: Optional[dict] = None

class CallEventResponse(CallEventCreate):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
