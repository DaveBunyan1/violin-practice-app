from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ExpectedNote:
    note: str
    time: float


@dataclass
class PracticeTarget:
    mode: Literal["tuner", "piece"]

    # Used in tuner mode
    expected_note: str | None = None

    # Used in piece mode
    notes: list[ExpectedNote] = field(default_factory=list)

    def get_expected_note(self, current_time: float) -> str | None:
        """
        Returns the note that should be played at the given time.
        """

        if self.mode == "tuner":
            return self.expected_note

        if not self.notes:
            return None

        current = None

        for note in self.notes:
            if note.time <= current_time:
                current = note.note
            else:
                break

        return current
