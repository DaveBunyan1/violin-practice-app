from dataclasses import dataclass, field
import time
import threading
from typing import List, Optional

from app.models.events import SessionStoredNote


@dataclass
class PracticeSession:
    piece_id: int
    start_time: float = field(default_factory=time.perf_counter)
    start_bar: Optional[int] = None
    end_bar: Optional[int] = None

    performed_notes: List[SessionStoredNote] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Internal lock to keep collection mutation thread-safe
        self._lock = threading.RLock()

    def add_performed_note(self, note: SessionStoredNote) -> None:
        with self._lock:
            self.performed_notes.append(note)

    def get_performed_notes(self) -> List[SessionStoredNote]:
        with self._lock:
            return list(self.performed_notes)
