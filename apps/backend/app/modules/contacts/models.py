import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.base import Base

class Contact(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_metadata: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    calls = relationship("Call", back_populates="contact")
