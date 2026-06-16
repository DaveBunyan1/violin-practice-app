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


class PerformedNoteEvent(TypedDict):
    note: str
    frequency: float
    timestamp: float  # onset time


class AlignedNote(TypedDict):
    expected_note: str
    performed_note: Optional[str]

    expected_time: float
    performed_time: Optional[float]

    pitch_error_cents: Optional[float]
    time_error: Optional[float]

    match_quality: float
