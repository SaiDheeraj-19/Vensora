from app.database.base import Base

# Import all models here so SQLAlchemy registers them with the metadata
from app.modules.departments.models import Department
from app.modules.roles.models import Role, Permission, RolePermission
from app.modules.users.models import User, UserInvitation
from app.modules.agents.models import Agent
from app.modules.campaigns.models import Campaign
from app.modules.contacts.models import Contact
from app.modules.calls.models import Call, CallRecording
from app.modules.crm.models import Ticket, CustomerProfile, KnowledgeDocument, PromptTemplate
from app.core.audit import AuditLog

__all__ = ["Base"]
