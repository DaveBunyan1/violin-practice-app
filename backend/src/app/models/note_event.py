from dataclasses import dataclass
from typing import Optional


@dataclass
class NoteEvent:
    """A historical entry specifically designed for reporting and data aggregation."""

    note: str
    frequency: float
    timestamp: float
    expected_note: Optional[str] = None
