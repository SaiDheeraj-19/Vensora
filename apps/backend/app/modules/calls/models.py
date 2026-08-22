import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

class Call(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twilio_call_sid: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign.id"), nullable=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contact.id"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="initiated")
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    recording_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    campaign = relationship("Campaign", back_populates="calls")
    contact = relationship("Contact", back_populates="calls")
