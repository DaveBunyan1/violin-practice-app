from typing import Optional, TypedDict


class NoteEvent(TypedDict):
    frequency: float
    note: str
    timestamp: float


class BroadcastEventData(TypedDict):
    frequency: float
    note: str
    time: float
    expected_note: Optional[str]


class WebSocketBroadcastEvent(TypedDict):
    type: str  # e.g., "pitch"
    data: BroadcastEventData
