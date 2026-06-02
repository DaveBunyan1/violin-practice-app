from typing import TypedDict
import queue


class NoteEvent(TypedDict):
    frequency: float
    note: str
    timestamp: float


note_queue: queue.Queue[NoteEvent] = queue.Queue()
