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

    def start_session(self) -> None:
        """Starts a fresh practice session. Threads calling get_session will block momentarily during initialization."""
        with self._lock:
            self._session = PracticeSession(start_time=time.perf_counter())
            self._segmenter.reset()

    def get_session(self) -> PracticeSession:
        """
        Thread-safe retrieval of the active session.
        Raises RuntimeError if the session has not been initialized.
        """
        with self._lock:
            if self._session is None:
                raise RuntimeError("Session not started")
            return self._session

    def end_session(self):
        session = self.get_session()
        return session

    def reset_session(self):
        """Explicit wrapper to restart the session state cleanly."""
        self.start_session()

    def get_current_time(self) -> float:
        """
        Returns the elapsed time (seconds) since the current session started.
        Returns 0.0 if no session is active.
        """
        with self._lock:
            session = self.get_session()
            return time.time() - session.start_time
