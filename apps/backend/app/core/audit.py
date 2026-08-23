import uuid
import asyncio
import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import String, JSON, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)

class AuditLog(Base):
    """
    Global system audit log for compliance.
    Records who did what, when, and where.
    """
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # e.g., "USER_LOGIN", "TICKET_CREATED", "PASSWORD_CHANGED"
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    # ID of the user performing the action (can be null for system actions)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    
    # ID of the entity that was affected
    resource_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    
    # JSON payload of what changed (before/after state)
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # The trace ID from correlation_id_var for debugging
    correlation_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

def log_audit_event_sync(
    action: str, 
    actor_id: Optional[uuid.UUID] = None,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Synchronous implementation to insert an audit record."""
    try:
        db: Session = SessionLocal()
        audit_record = AuditLog(
            action=action,
            actor_id=actor_id,
            resource_id=resource_id,
            changes=changes,
            correlation_id=correlation_id,
            ip_address=ip_address
        )
        db.add(audit_record)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to record audit log {action}: {e}")

def log_audit_event(
    action: str, 
    actor_id: Optional[uuid.UUID] = None,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Fire-and-forget asynchronous audit logger. 
    Prevents audit logging from blocking the main API thread.
    """
    asyncio.get_event_loop().run_in_executor(
        None, 
        log_audit_event_sync, 
        action, actor_id, resource_id, changes, correlation_id, ip_address
    )
