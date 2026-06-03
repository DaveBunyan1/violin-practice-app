import time
from models.session import PracticeSession
from models.practice_target import PracticeTarget


class SessionController:
    def __init__(self, target: PracticeTarget) -> None:
        self.target = target
        self.practice_start: float | None = None
        self.session: PracticeSession | None = None

    def start_session(self, target: PracticeTarget):
        self.practice_start = time.time()
        self.session = PracticeSession(start_time=self.practice_start)
        self.target = target

    def get_session(self) -> PracticeSession:
        if self.session is None:
            raise RuntimeError("Session not started")
        return self.session

    def reset_session(self):
        self.start_session(self.target)

    def get_current_time(self) -> float:
        if self.practice_start is None:
            return 0.0
        return time.time() - self.practice_start
