from typing import List, Optional, Callable
import time

from app.core.telemetry import generate_event_id
from app.models.events import PitchObservationEvent, PerformedNoteEvent
from app.core.logging import logger


class NoteSegmenter:
    """
    Deterministic FSM-based note segmenter.

    States:
    - IDLE: no active note
    - HOLDING: stable committed note
    - CANDIDATE: potential transition note
    """

    def __init__(self, stability_threshold: float = 0.1):
        self.stability_threshold = stability_threshold
        self._callback: Optional[Callable[[PerformedNoteEvent], None]] = None

        # committed state
        self._note: Optional[str] = None
        self._frequency: Optional[float] = None
        self._start_time: Optional[float] = None
        self._cents: List[float] = []

        # candidate state
        self._cand_note: Optional[str] = None
        self._cand_freq: Optional[float] = None
        self._cand_start: Optional[float] = None
        self._cand_cents: List[float] = []

    # -------------------------------------------------
    # API
    # -------------------------------------------------
    def set_callback(self, callback: Callable[[PerformedNoteEvent], None]) -> None:
        self._callback = callback

    # -------------------------------------------------
    # Main entry
    # -------------------------------------------------
    def process(self, event: PitchObservationEvent) -> None:
        note = event["note"]
        freq = event["frequency"]
        timestamp = event["timestamp"]
        cents = event.get("pitch_cents_error")

        # -------------------------
        # 1. REST = HARD BOUNDARY
        # -------------------------
        if note == "REST":
            flushed_note = self._note
            self.flush(timestamp)

            logger.info(
                "rest_flush",
                extra={
                    "extra_context": {
                        "timestamp": timestamp,
                        "flushed_note": flushed_note,
                    }
                },
            )
            return

        # -------------------------
        # 2. First note ever
        # -------------------------
        if self._note is None:
            self._start(note, freq, timestamp, cents)
            return

        # -------------------------
        # 3. Stable continuation
        # -------------------------
        if note == self._note:
            if cents is not None:
                self._cents.append(cents)

            self._cand_reset()
            return

        # -------------------------
        # 4. Candidate logic
        # -------------------------
        self._handle_candidate(note, freq, timestamp, cents)

    # -------------------------------------------------
    # Candidate handling
    # -------------------------------------------------
    def _handle_candidate(
        self, note: str, freq: float, timestamp: float, cents: Optional[float]
    ) -> None:
        # new candidate
        if self._cand_note != note:
            self._cand_note = note
            self._cand_freq = freq
            self._cand_start = timestamp
            self._cand_cents = []
            if cents is not None:
                self._cand_cents.append(cents)
            return

        # continue candidate accumulation
        if cents is not None:
            self._cand_cents.append(cents)

        # stability check
        if self._cand_start is None:
            return

        if timestamp - self._cand_start >= self.stability_threshold:
            self._commit_candidate(timestamp)

    # -------------------------------------------------
    # State transitions
    # -------------------------------------------------
    def _start(
        self, note: str, freq: float, timestamp: float, cents: Optional[float]
    ) -> None:
        self._note = note
        self._frequency = freq
        self._start_time = timestamp
        self._cents = []

        if cents is not None:
            self._cents.append(cents)

        logger.info(
            "note_started", extra={"extra_context": {"note": note, "start": timestamp}}
        )

    def _commit_candidate(self, timestamp: float) -> None:
        self._emit(timestamp)

        self._note = self._cand_note
        self._frequency = self._cand_freq
        self._start_time = self._cand_start
        self._cents = list(self._cand_cents)

        logger.info(
            "note_committed",
            extra={
                "extra_context": {
                    "note": self._cand_note,
                    "start": self._cand_start,
                }
            },
        )

        self._cand_reset()

    def _cand_reset(self) -> None:
        self._cand_note = None
        self._cand_freq = None
        self._cand_start = None
        self._cand_cents = []

    def reset(self) -> None:
        self._note = None
        self._frequency = None
        self._start_time = None
        self._cents = []
        self._cand_reset()

    # -------------------------------------------------
    # Output
    # -------------------------------------------------
    def _emit(self, end_time: float) -> None:
        if self._callback is None:
            return

        if self._note is None or self._start_time is None or self._frequency is None:
            return

        avg = None
        if self._cents:
            avg = sum(self._cents) / len(self._cents)

        event_id = generate_event_id()
        created_at = time.perf_counter()

        event: PerformedNoteEvent = {
            "note": self._note,
            "frequency": self._frequency,
            "avg_pitch_error_cents": avg,
            "start_time": self._start_time,
            "end_time": end_time,
            "duration": end_time - self._start_time,
            "retry_count": 0,
            "telemetry": {
                "event_id": event_id,
                "created_at": created_at,
            },
        }

        self._callback(event)

    # -------------------------------------------------
    # Flush
    # -------------------------------------------------
    def flush(self, timestamp: float) -> None:
        if self._note is None:
            return

        self._emit(timestamp)
        self.reset()
