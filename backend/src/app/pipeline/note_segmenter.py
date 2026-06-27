from typing import List, Optional, Callable
from app.models.events import PitchObservationEvent, PerformedNoteEvent


class NoteSegmenter:
    """
    Converts raw pitch observations into stable performed notes
    using a 2-state confirmation model:

    - committed note (current stable note)
    - candidate note (potential transition)
    """

    def __init__(self, stability_threshold: float = 0.1):
        self.stability_threshold = stability_threshold

        # committed state
        self._current_note: Optional[str] = None
        self._current_frequency: Optional[float] = None
        self._note_start_time: Optional[float] = None
        self._current_cents_errors: List[float] = []

        # candidate state
        self._candidate_note: Optional[str] = None
        self._candidate_frequency: Optional[float] = None
        self._candidate_start_time: Optional[float] = None
        self._candidate_cents_errors: List[float] = []

        self._callback: Optional[Callable[[PerformedNoteEvent], None]] = None

    def set_callback(self, callback: Callable[[PerformedNoteEvent], None]) -> None:
        self._callback = callback

    # -------------------------------------------------
    # Main entry
    # -------------------------------------------------
    def process(self, event: PitchObservationEvent) -> None:
        note = event["note"]
        freq = event["frequency"]
        timestamp = event["timestamp"]
        cents_error = event.get("pitch_cents_error")

        # first note ever
        if self._current_note is None:
            self._start_new_note(note, freq, timestamp, cents_error)
            return

        # stable continuation → cancel candidate
        if note == self._current_note:
            if cents_error is not None:
                self._current_cents_errors.append(cents_error)
            self._clear_candidate()
            return

        # start or continue candidate
        if self._candidate_note != note:
            self._start_candidate(note, freq, timestamp, cents_error)
        else:
            # Continue accumulating frames into the candidate window
            if cents_error is not None:
                self._candidate_cents_errors.append(cents_error)

        # guard
        if self._candidate_start_time is None:
            return

        # confirm stability
        if timestamp - self._candidate_start_time >= self.stability_threshold:
            self._commit_candidate(timestamp)

    # -------------------------------------------------
    # State transitions
    # -------------------------------------------------
    def _start_new_note(
        self, note: str, freq: float, timestamp: float, cents_error: Optional[float]
    ) -> None:
        self._current_note = note
        self._current_frequency = freq
        self._note_start_time = timestamp
        self._current_cents_errors = [cents_error] if cents_error is not None else []

    def _start_candidate(
        self, note: str, freq: float, timestamp: float, cents_error: Optional[float]
    ) -> None:
        self._candidate_note = note
        self._candidate_frequency = freq
        self._candidate_start_time = timestamp
        self._candidate_cents_errors = [cents_error] if cents_error is not None else []

    def _clear_candidate(self) -> None:
        self._candidate_note = None
        self._candidate_frequency = None
        self._candidate_start_time = None
        self._candidate_cents_errors = []

    def _commit_candidate(self, timestamp: float) -> None:
        """
        Finalise current note and emit it, then switch to candidate.
        """

        # emit previous note
        self._emit_current_note(timestamp)

        # promote candidate → current
        self._current_note = self._candidate_note
        self._current_frequency = self._candidate_frequency
        self._note_start_time = self._candidate_start_time
        self._current_cents_errors = self._candidate_cents_errors

        self._clear_candidate()

    # -------------------------------------------------
    # Output
    # -------------------------------------------------
    def _emit_current_note(self, end_timestamp: float) -> None:
        if self._callback is None:
            return

        if (
            self._current_note is None
            or self._note_start_time is None
            or self._current_frequency is None
        ):
            return

        if self._current_cents_errors:
            avg_cents_error: Optional[float] = sum(self._current_cents_errors) / len(
                self._current_cents_errors
            )
        else:
            avg_cents_error = None

        event: PerformedNoteEvent = {
            "note": self._current_note,
            "frequency": self._current_frequency,
            "start_time": self._note_start_time,
            "end_time": end_timestamp,
            "duration": end_timestamp - self._note_start_time,
            "avg_pitch_error_cents": avg_cents_error,
        }

        self._callback(event)

    # -------------------------------------------------
    # Public utilities
    # -------------------------------------------------
    def reset(self) -> None:
        self._current_note = None
        self._current_frequency = None
        self._note_start_time = None
        self._current_cents_errors = []
        self._clear_candidate()

    def flush(self, timestamp: float) -> None:
        """
        Force emit last note at end of stream.
        """
        if self._current_note is None:
            return

        self._emit_current_note(timestamp)
        self.reset()
