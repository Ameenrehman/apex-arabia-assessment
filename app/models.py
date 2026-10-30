"""SQLAlchemy models for Apex Operations API."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class OperationTask(Base):
    """Represents an operational task or deployment job managed by the Apex API."""

    __tablename__ = "operation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False, index=True)
    service_name = Column(String(60), nullable=False, index=True)
    environment = Column(String(30), nullable=False, default="production")
    status = Column(String(30), nullable=False, default="pending")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<OperationTask id={self.id} title='{self.title}' status='{self.status}'>"
