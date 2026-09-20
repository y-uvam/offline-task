from __future__ import annotations

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    client_id: str
    title: str = Field(..., min_length=1, max_length=500)
    created_at: str


class IncidentResponse(BaseModel):
    client_id: str
    server_id: str
    title: str
    created_at: str
    received_at: str
    was_duplicate: bool = False
