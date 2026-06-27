from typing import TypedDict


class HealthCheckReturn(TypedDict):
    status: str
    version: str
    session_active: bool
