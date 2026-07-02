import time
import threading
from typing import Optional
from sqlalchemy.orm import Session

from app.pipeline.practice_session import PracticeSession
from app.pipeline.practice_target import ExpectedNote, PracticePiece, PracticeTarget
from app.pipeline.note_segmenter import NoteSegmenter
from app.services.repertoire_service import get_piece_by_id


class SessionController:
    def __init__(
        self,
        target: PracticeTarget,
        segmenter: NoteSegmenter,
    ) -> None:
        self.target = target
        self._segmenter = segmenter

        # Guard session state changes across WebSocket and processing threads
        self._lock = threading.RLock()

        self._session: Optional[PracticeSession] = None
        self._active: bool = False

    def start_session(
        self,
        db: Session,
        piece_id: int,
        start_bar: Optional[int] = None,
        end_bar: Optional[int] = None,
        target_bpm: Optional[int] = None,
        countdownSeconds: Optional[float] = 0.0,
    ) -> None:
        """Starts a fresh practice session. Threads calling get_session will block momentarily during initialization."""
        with self._lock:
            db_piece = get_piece_by_id(db, piece_id)

            if not db_piece:
                raise ValueError(f"Repertoire piece with ID {piece_id} not found.")

            original_bpm = (
                db_piece.bpm if db_piece.bpm else 116
            )  # 116 hardcoded is an issue
            effective_bpm = target_bpm if target_bpm else original_bpm

            speed_multiplier = original_bpm / effective_bpm

            seconds_per_beat = 60.0 / effective_bpm
            seconds_per_bar = seconds_per_beat * db_piece.time_signature_numerator

            start_time_offset = 0.0
            if start_bar and start_bar > 1:
                start_time_offset = (start_bar - 1) * seconds_per_bar

            end_time_offset = db_piece.total_duration
            if end_bar:
                end_time_offset = end_bar * seconds_per_bar

            # 2. Filter and shift the notes for the pipeline
            expected_notes = []
            for note_model in db_piece.notes:
                # Only include notes that fall within the selected bar time window
                scaled_note_time = note_model.time * speed_multiplier

                if start_time_offset <= scaled_note_time <= end_time_offset:

                    # CRITICAL: Shift the target time back to 0.0 so the
                    # countdown/timer aligns perfectly with when they start playing!
                    adjusted_time = scaled_note_time - start_time_offset

                    scaled_duration = note_model.duration * speed_multiplier

                    expected_notes.append(
                        ExpectedNote(
                            note=note_model.note,
                            time=adjusted_time,
                            duration=scaled_duration,
                        )
                    )

            # 3. Feed the isolated loop segment to the pipeline target
            practice_piece = PracticePiece(
                title=f"{db_piece.title} (Bars {start_bar or 1}-{end_bar or 'End'})",
                total_duration=end_time_offset - start_time_offset,
                notes=expected_notes,
            )

            self.target.mode = "piece"
            self.target.active_piece = practice_piece

            delay_buffer = countdownSeconds if countdownSeconds is not None else 0.0
            synchronized_start = time.perf_counter() + delay_buffer

            # 4. Spin up the active session tracking state
            self._session = PracticeSession(
                piece_id=piece_id,
                start_time=synchronized_start,
                start_bar=start_bar,
                end_bar=end_bar,
            )
            self._segmenter.reset()
            self._active = True

    def end_session(self) -> PracticeSession:
        with self._lock:
            if self._session is None:
                raise RuntimeError("No session to end")

            self._active = False
            return self._session

    def reset_session(
        self,
        db: Session,
        piece_id: int,
        start_bar: Optional[int] = None,
        end_bar: Optional[int] = None,
    ) -> None:
        """Hard reset = restart everything cleanly."""
        self.start_session(db, piece_id, start_bar, end_bar)

    def get_session(self) -> PracticeSession:
        """
        Thread-safe retrieval of the active session.
        Raises RuntimeError if the session has not been initialized.
        """
        with self._lock:
            if self._session is None or not self._active:
                raise RuntimeError("Session not started")
            return self._session

    def is_active(self) -> bool:
        return self._active

    def get_elapsed_time(self) -> float:
        """
        Session-relative time using the SAME clock as ingestion.
        """
        with self._lock:
            if self._session is None:
                return 0.0
            return time.perf_counter() - self._session.start_time
