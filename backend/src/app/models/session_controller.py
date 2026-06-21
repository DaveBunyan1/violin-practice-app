import time
import threading
from typing import Optional

from app.models.session import PracticeSession
from app.models.practice_target import PracticeTarget
from app.services.note_segmenter import NoteSegmenter


class SessionController:
    def __init__(self, target: PracticeTarget, segmenter: NoteSegmenter) -> None:
        self.target = target
        self._segmenter = segmenter

        # Guard session state changes across WebSocket and processing threads
        self._lock = threading.RLock()

        self._session: Optional[PracticeSession] = None
        self._active: bool = False

    def start_session(self) -> None:
        """Starts a fresh practice session. Threads calling get_session will block momentarily during initialization."""
        with self._lock:
            self._session = PracticeSession(start_time=time.perf_counter())
            self._segmenter.reset()
            self._active = True

    def end_session(self) -> PracticeSession:
        with self._lock:
            if self._session is None:
                raise RuntimeError("No session to end")

            self._active = False
            return self._session

    def reset_session(self) -> None:
        """Hard reset = restart everything cleanly."""
        self.start_session()

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
