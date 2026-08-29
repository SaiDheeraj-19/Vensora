import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from datetime import datetime, timezone

from app.database.base import Base
from app.modules.campaigns import models

class Call(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twilio_call_sid: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign.id"), nullable=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contact.id"), nullable=False)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent.id"), nullable=True)
    
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    recording_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="calls")
    agent = relationship("Agent", back_populates="calls")
    contact = relationship("Contact", back_populates="calls")
    recording = relationship("CallRecording", back_populates="call", uselist=False)

class CallRecording(Base):
    """Tracks metadata for stored call audio."""
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("call.id"), nullable=False)
    
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(10), default="wav")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    retention_expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    
    call = relationship("Call", back_populates="recording")
