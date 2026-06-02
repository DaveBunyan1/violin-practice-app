from dataclasses import dataclass, field
from typing import List, Dict, Any
import time


@dataclass
class NoteEvent:
    note: str
    frequency: float
    timestamp: float
    expected_note: str | None = None


@dataclass
class PracticeSession:
    start_time: float = field(default_factory=time.time)
    notes: List[NoteEvent] = field(default_factory=list)

    def add_note(self, note: str, frequency: float, expected_note: str | None = None):
        self.notes.append(
            NoteEvent(
                note=note,
                frequency=frequency,
                timestamp=time.time() - self.start_time,
                expected_note=expected_note,
            )
        )

    def end(self):
        return self.to_report()

    def to_report(self):
        return PracticeReport.from_session(self)


@dataclass
class PracticeReport:
    overall_score: float
    pitch_score: float
    timing_score: float
    notes: List[Dict[str, Any]]

    @staticmethod
    def from_session(session: PracticeSession):
        notes = session.notes

        if not notes:
            return PracticeReport(0, 0, 0, [])

        pitch_scores = []
        timing_scores = []

        formatted = []

        for n in notes:
            # very simple pitch match scoring for now
            pitch_ok = 1.0 if n.note == n.expected_note else 0.0
            pitch_scores.append(pitch_ok)

            formatted.append(
                {
                    "note": n.note,
                    "expected": n.expected_note,
                    "frequency": n.frequency,
                    "time": n.timestamp,
                    "pitchAccuracy": pitch_ok * 100,
                }
            )

        pitch_score = sum(pitch_scores) / len(pitch_scores) * 100

        # placeholder timing (we’ll improve later)
        timing_score = 80.0

        overall = (pitch_score + timing_score) / 2

        return PracticeReport(
            overall_score=overall,
            pitch_score=pitch_score,
            timing_score=timing_score,
            notes=formatted,
        )


session = PracticeSession()
