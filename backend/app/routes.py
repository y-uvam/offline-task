from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Response

from .models import IncidentCreate, IncidentResponse
from .store import store

incident_router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@incident_router.post("", response_model=IncidentResponse, status_code=200)
def create_incident(incident: IncidentCreate) -> IncidentResponse:
    return store.upsert(incident)


@incident_router.get("", response_model=List[IncidentResponse])
def list_incidents() -> List[IncidentResponse]:
    return store.get_all()


@incident_router.get("/{client_id}", response_model=IncidentResponse)
def get_incident(client_id: str) -> IncidentResponse:
    result = store.get_by_client_id(client_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return result


@incident_router.delete("", status_code=204)
def clear_incidents() -> Response:
    store.clear()
    return Response(status_code=204)
