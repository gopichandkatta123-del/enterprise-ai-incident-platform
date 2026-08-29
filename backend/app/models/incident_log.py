from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IncidentLog(Base):
    __tablename__ = "incident_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=False,
        index=True,
    )

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


class IncidentLogCreate(BaseModel):
    level: str = Field(
        ...,
        examples=["ERROR"],
    )

    source: str = Field(
        ...,
        examples=["payment-api"],
    )

    message: str = Field(
        ...,
        examples=[
            "Container terminated with OOMKilled after memory usage reached 98%"
        ],
    )

    timestamp: datetime


class IncidentLogResponse(IncidentLogCreate):
    id: int
    incident_id: int

    model_config = ConfigDict(from_attributes=True)