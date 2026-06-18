from dataclasses import dataclass, field
import time
import threading
from typing import List

from app.core.events import LiveDashboardMetrics, PerformedNoteEvent


@dataclass
class PracticeSession:
    start_time: float = field(default_factory=time.perf_counter)

    events: List[LiveDashboardMetrics] = field(default_factory=list)
    performed_notes: List[PerformedNoteEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Internal lock to keep collection mutation thread-safe
        self._lock = threading.RLock()

    def add_event(self, event: LiveDashboardMetrics) -> None:
        """Pure append-only event store."""
        with self._lock:
            self.events.append(event)

    def add_performed_note(self, note: PerformedNoteEvent) -> None:
        with self._lock:
            self.performed_notes.append(note)

    def get_events_snapshot(self) -> List[LiveDashboardMetrics]:
        with self._lock:
            return list(self.events)

    def get_performed_notes(self) -> List[PerformedNoteEvent]:
        with self._lock:
            return list(self.performed_notes)


session = PracticeSession()
