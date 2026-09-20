from __future__ import annotations

import threading
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import List, Optional

from .models import IncidentCreate, IncidentResponse


class IncidentStore:
    def __init__(self) -> None:
        self._incidents: OrderedDict[str, IncidentResponse] = OrderedDict()
        self._lock = threading.Lock()

    def upsert(self, incident: IncidentCreate) -> IncidentResponse:
        with self._lock:
            existing = self._incidents.get(incident.client_id)
            if existing is not None:
                return IncidentResponse(
                    client_id=existing.client_id,
                    server_id=existing.server_id,
                    title=existing.title,
                    created_at=existing.created_at,
                    received_at=existing.received_at,
                    was_duplicate=True,
                )

            response = IncidentResponse(
                client_id=incident.client_id,
                server_id=str(uuid.uuid4()),
                title=incident.title,
                created_at=incident.created_at,
                received_at=datetime.now(timezone.utc).isoformat(),
                was_duplicate=False,
            )
            self._incidents[incident.client_id] = response
            return response

    def get_all(self) -> List[IncidentResponse]:
        with self._lock:
            return list(self._incidents.values())

    def get_by_client_id(self, client_id: str) -> Optional[IncidentResponse]:
        with self._lock:
            return self._incidents.get(client_id)

    def count(self) -> int:
        with self._lock:
            return len(self._incidents)

    def clear(self) -> None:
        with self._lock:
            self._incidents.clear()


store = IncidentStore()
