from typing import Optional, TypedDict
import queue


class NoteEvent(TypedDict):
    frequency: float
    note: str
    timestamp: float


note_queue: queue.Queue[NoteEvent] = queue.Queue()


class BroadcastEventData(TypedDict):
    frequency: float
    note: str
    time: float
    expected_note: Optional[str]


class WebSocketBroadcastEvent(TypedDict):
    type: str  # e.g., "pitch"
    data: BroadcastEventData
