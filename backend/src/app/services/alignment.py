from typing import List


from app.core.events import AlignedNote, SessionStoredNote
from app.models.practice_target import ExpectedNote


def align_notes(
    expected: list[ExpectedNote],
    performed: list[SessionStoredNote],
    time_tolerance: float = 0.4,
) -> List[AlignedNote]:
    aligned: List[AlignedNote] = []
    used = set()

    for exp in expected:
        best_match = None
        best_dt = float("inf")
        best_idx = None

        exp_time = exp.time

        for i, perf in enumerate(performed):
            if i in used:
                continue

            perf_time = perf["start_time"]

            dt = abs(perf_time - exp_time)

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
                    "expected_time": exp_time,
                    "performed_start_time": best_match["start_time"],
                    "performed_end_time": best_match["end_time"],
                    "pitch_error_cents": None,  # v1.2
                    "time_error": best_match["start_time"] - exp_time,
                    "match_quality": 1.0,
                }
            )

        else:
            aligned.append(
                {
                    "expected_note": exp.note,
                    "performed_note": None,
                    "expected_time": exp_time,
                    "performed_start_time": None,
                    "performed_end_time": None,
                    "pitch_error_cents": None,
                    "time_error": None,
                    "match_quality": 0.0,
                }
            )

    return aligned
