from dataclasses import dataclass, field
import time
import threading
from typing import List

from app.core.events import SessionStoredNote


@dataclass
class PracticeSession:
    start_time: float = field(default_factory=time.perf_counter)

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


session = PracticeSession()
