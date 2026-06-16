import time
from typing import Optional, Callable
from app.core.events import NoteEvent, PerformedNoteEvent


class NoteSegmenter:
    """
    Converts raw pitch observations into stable performed notes.
    """

    def __init__(
        self,
        stability_threshold: float = 0.1,  # seconds
    ):
        self.stability_threshold = stability_threshold

        self._current_note: Optional[str] = None
        self._note_start_time: Optional[float] = None
        self._last_change_time: float = time.time()
        self._current_frequency: Optional[float] = None

        self._callback: Optional[Callable[[PerformedNoteEvent], None]] = None

    def set_callback(self, callback: Callable[[PerformedNoteEvent], None]) -> None:
        """
        Called when a stable note is confirmed.
        """
        self._callback = callback

    def process(self, event: NoteEvent) -> None:
        note = event["note"]
        freq = event["frequency"]
        timestamp = event["timestamp"]

        # First ever note
        if self._current_note is None:
            self._start_new_note(note, freq, timestamp)
            return

        # Same note → just continue
        if note == self._current_note:
            return

        # NOTE CHANGE DETECTED
        time_since_last_change = timestamp - self._last_change_time

        # Only accept as real change if stable long enough
        if time_since_last_change >= self.stability_threshold:
            self._emit_current_note(timestamp)
            self._start_new_note(note, freq, timestamp)

        else:
            # ignore jitter / noise
            pass

    def _start_new_note(self, note: str, freq: float, timestamp: float) -> None:
        self._current_note = note
        self._note_start_time = timestamp
        self._last_change_time = timestamp
        self._current_frequency = freq

    def _emit_current_note(self, timestamp: float) -> None:
        if self._callback is None:
            return

        if (
            self._current_note is None
            or self._note_start_time is None
            or self._current_frequency is None
        ):
            return

        self._callback(
            {
                "note": self._current_note,
                "frequency": self._current_frequency,
                "timestamp": self._note_start_time,
            }
        )
