from typing import List

from app.core.events import PerformedNoteEvent, AlignedNote
from app.models.practice_target import ExpectedNote


def align_notes(
    expected: list[ExpectedNote],
    performed: list[PerformedNoteEvent],
    time_tolerance: float = 0.4,
) -> List[AlignedNote]:
    aligned = []
    used = set()

    for exp in expected:
        best_match = None
        best_dt = float("inf")
        best_idx = None

        for i, perf in enumerate(performed):
            if i in used:
                continue

            dt = abs(perf["timestamp"] - exp.time)

            if dt < best_dt and dt <= time_tolerance:
                best_dt = dt
                best_match = perf
                best_idx = i

        if best_match:
            used.add(best_idx)

            aligned.append(
                {
                    "expected_note": exp.note,
                    "performed_note": best_match["note"],
                    "expected_time": exp.time,
                    "performed_time": best_match["timestamp"],
                    "pitch_error_cents": None,
                    "time_error": best_match["timestamp"] - exp.time,
                    "match_quality": 1.0,
                }
            )
        else:
            aligned.append(
                {
                    "expected_note": exp.note,
                    "performed_note": None,
                    "expected_time": exp.time,
                    "performed_time": None,
                    "pitch_error_cents": None,
                    "time_error": None,
                    "match_quality": 0.0,
                }
            )

    return aligned
