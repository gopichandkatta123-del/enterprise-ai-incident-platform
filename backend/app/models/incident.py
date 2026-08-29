from datetime import datetime

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    service_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )


class IncidentCreate(BaseModel):
    service_name: str = Field(
        ...,
        examples=["checkout-api"],
    )

    severity: str = Field(
        ...,
        examples=["critical"],
    )

    error_message: str = Field(
        ...,
        examples=["PostgreSQL connection timeout detected"],
    )

    description: str | None = Field(
        default=None,
        examples=["Checkout requests are returning HTTP 500 errors."],
    )

    timestamp: datetime


class IncidentResponse(IncidentCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)