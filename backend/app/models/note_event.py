from dataclasses import dataclass


@dataclass
class NoteEvent:
    note: str
    frequency: float
    timestamp: float
    expected_note: str | None = None
