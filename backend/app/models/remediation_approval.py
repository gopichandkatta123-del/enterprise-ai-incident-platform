from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RemediationApproval(Base):
    __tablename__ = "remediation_approvals"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    agent_run_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    approved_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    decided_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


class RemediationDecisionCreate(BaseModel):
    decision: str
    approved_by: str
    notes: str | None = None


class RemediationApprovalResponse(BaseModel):
    id: int
    incident_id: int
    agent_run_id: int
    decision: str
    approved_by: str
    notes: str | None
    decided_at: datetime

    model_config = ConfigDict(from_attributes=True)