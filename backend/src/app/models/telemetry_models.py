from typing import TypedDict


class TelemetryMeta(TypedDict):
    id: str
    t_start: float
    t_ingest: float
    t_segment: float
    t_process: float
    t_websocket: float
