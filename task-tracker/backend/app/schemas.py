"""Pydantic schemas for request and response validation.
 
Module 1 scope: only the health-check response shape is defined. Task request
and response schemas will be added in a later module.
"""
 
from pydantic import BaseModel, Field
 
 
class HealthResponse(BaseModel):
    """Response body returned by GET /health."""
 
    status: str = Field(
        ...,
        description="Service health indicator.",
        examples=["ok"],
    )
    timestamp: str = Field(
        ...,
        description="Current server time, UTC, ISO 8601 format.",
        examples=["2026-07-23T10:15:30.123456+00:00"],
    )