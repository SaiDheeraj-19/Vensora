import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

class Agent(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    voice_id: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. elevenlabs, playht
    
    campaigns = relationship("Campaign", back_populates="agent")
    calls = relationship("Call", back_populates="agent")
