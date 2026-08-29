from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

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

    workflow: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    evaluation_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    guardrail_decision: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    supervisor_decision: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    diagnosis_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


class AgentRunResponse(BaseModel):
    id: int
    incident_id: int
    workflow: str
    started_at: datetime
    completed_at: datetime
    latency_ms: float
    evaluation_score: float | None
    guardrail_decision: str | None
    supervisor_decision: str | None
    diagnosis_summary: str | None
    status: str

    model_config = ConfigDict(from_attributes=True)