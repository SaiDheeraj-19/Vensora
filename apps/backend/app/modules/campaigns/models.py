import uuid
import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base
from app.modules.agents.models import Agent

class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class CampaignType(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

class Campaign(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent.id"), nullable=False)
    
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    campaign_type: Mapped[CampaignType] = mapped_column(Enum(CampaignType), nullable=False)
    
    agent = relationship("Agent", back_populates="campaigns")
    calls = relationship("Call", back_populates="campaign")
