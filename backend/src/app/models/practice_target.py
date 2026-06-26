from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ExpectedNote:
    note: str
    time: float
    duration: float


@dataclass
class PracticePiece:
    title: str
    total_duration: float
    notes: list[ExpectedNote] = field(default_factory=list)


@dataclass
class PracticeTarget:
    mode: Literal["tuner", "piece"]

    # Used in tuner mode
    expected_note: str | None = None

    # Used in piece mode
    active_piece: PracticePiece | None = None

    def get_expected_note(self, current_time: float) -> str | None:
        """
        Returns the note that should be playing at the given elapsed time window.
        Returns None if the player is in a rest/silence period.
        """
        if self.mode == "tuner":
            return self.expected_note

        if not self.active_piece or not self.active_piece.notes:
            return None

        # Check if current_time falls directly within any note's start/end window
        for note in self.active_piece.notes:
            if note.time <= current_time <= (note.time + note.duration):
                return note.note
            # Since notes are sorted chronologically, we can break early
            # if we've passed the current time window entirely
            elif note.time > current_time:
                break

        return None

    def get_expected_sequence(self) -> list[ExpectedNote]:
        """
        Returns the full sequence of expected notes for evaluation or tracking.
        """
        if self.mode == "piece" and self.active_piece:
            return self.active_piece.notes
        return []
