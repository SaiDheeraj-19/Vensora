import re
from datetime import datetime, timezone

from sqlalchemy.orm import declarative_base, declared_attr, Mapped, mapped_column
from sqlalchemy import DateTime

def camel_to_snake(name: str) -> str:
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

class CustomBase:
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return camel_to_snake(cls.__name__)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

Base = declarative_base(cls=CustomBase)
