"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthLiveResponse(BaseModel):
    """Response schema for liveness probe."""

    status: str = Field(..., examples=["alive"])
    app: str = Field(..., examples=["Apex Operations API"])
    version: str = Field(..., examples=["1.0.0"])
    timestamp: datetime


class HealthReadyResponse(BaseModel):
    """Response schema for readiness probe."""

    status: str = Field(..., examples=["ready"])
    database: str = Field(..., examples=["connected"])
    timestamp: datetime


class OperationTaskBase(BaseModel):
    """Base schema with common attributes."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Descriptive title of the operation task",
        examples=["Deploy Payment Gateway Service"],
    )
    service_name: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Target microservice or system component",
        examples=["payment-service"],
    )
    environment: str = Field(
        default="production",
        max_length=30,
        description="Target environment (production, staging, dev)",
        examples=["production"],
    )
    status: str = Field(
        default="pending",
        max_length=30,
        description="Task lifecycle status (pending, in_progress, completed, failed)",
        examples=["pending"],
    )


class OperationTaskCreate(OperationTaskBase):
    """Schema for creating a new operation task."""

    pass


class OperationTaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(None, min_length=3, max_length=120)
    service_name: Optional[str] = Field(None, min_length=2, max_length=60)
    environment: Optional[str] = Field(None, max_length=30)
    status: Optional[str] = Field(None, max_length=30)


class OperationTaskResponse(OperationTaskBase):
    """Schema for returning operation task data."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
