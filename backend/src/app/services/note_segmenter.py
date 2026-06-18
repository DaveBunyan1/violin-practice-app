from typing import Optional, Callable
from app.core.events import PitchObservationEvent, PerformedNoteEvent


class NoteSegmenter:
    """
    Converts raw pitch observations into stable performed notes
    using a 2-state confirmation model:
    - committed note
    - candidate note (pending confirmation)
    """

    def __init__(
        self,
        stability_threshold: float = 0.1,
    ):
        self.stability_threshold = stability_threshold

        self._current_note: Optional[str] = None
        self._current_frequency: Optional[float] = None
        self._note_start_time: Optional[float] = None

        self._candidate_note: Optional[str] = None
        self._candidate_frequency: Optional[float] = None
        self._candidate_start_time: Optional[float] = None

        self._callback: Optional[Callable[[PerformedNoteEvent], None]] = None

    def set_callback(self, callback: Callable[[PerformedNoteEvent], None]) -> None:
        """
        Called when a stable note is confirmed.
        """
        self._callback = callback

    def process(self, event: PitchObservationEvent) -> None:
        note = event["note"]
        freq = event["frequency"]
        timestamp = event["timestamp"]

        # first note
        if self._current_note is None:
            self._commit_note(note, freq, timestamp)
            return

        # same note → reset candidate
        if note == self._current_note:
            self._clear_candidate()
            return

        # new candidate or continuing candidate
        if self._candidate_note != note:
            self._start_candidate(note, freq, timestamp)

        # Guard Clause: Type check the candidate state
        if (
            self._candidate_note is None
            or self._candidate_frequency is None
            or self._candidate_start_time is None
        ):
            return

        # Stability Evaluation
        if timestamp - self._candidate_start_time >= self.stability_threshold:
            self._commit_note(
                note=self._candidate_note,
                freq=self._candidate_frequency,
                timestamp=self._candidate_start_time,
            )

    def reset(self):
        self._current_note = None
        self._current_frequency = None
        self._note_start_time = None

        self._candidate_note = None
        self._candidate_frequency = None
        self._candidate_start_time = None

    def flush(self, timestamp: float) -> None:
        """
        Finalize the current note at end of stream.
        Should be called when audio input stops.
        """
        if self._current_note is None:
            return

        # Emit final active note
        self._emit_current_note(timestamp)

        # Reset all state
        self._current_note = None
        self._current_frequency = None
        self._note_start_time = None

        self._clear_candidate()

    # -------------------------
    # State transitions
    # -------------------------
    def _start_candidate(self, note: str, freq: float, timestamp: float) -> None:
        self._candidate_note = note
        self._candidate_frequency = freq
        self._candidate_start_time = timestamp

    def _clear_candidate(self) -> None:
        self._candidate_note = None
        self._candidate_frequency = None
        self._candidate_start_time = None

    def _commit_note(self, note: str, freq: float, timestamp: float) -> None:
        """
        Finalize current note and emit it.
        """
        if self._current_note is not None:
            self._emit_current_note(timestamp)

        self._current_note = note
        self._current_frequency = freq
        self._note_start_time = timestamp

        self._clear_candidate()

    def _emit_current_note(self, end_timestamp: float) -> None:
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
