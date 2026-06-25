from typing import List

from app.core.events import AlignedNote, ScoreResult


def score_alignment(aligned: List[AlignedNote]) -> ScoreResult:
    total_notes = len(aligned)

    if total_notes == 0:
        return {
            "total_score": 0.0,
            "pitch_accuracy": 0.0,
            "timing_accuracy": 0.0,
            "notes_hit": 0,
            "notes_total": 0,
        }

    pitch_score = 0.0
    timing_score = 0.0
    notes_hit = 0

    for note in aligned:
        if note["performed_note"] is None:
            continue

        time_error = note["time_error"]
        cents_error = note.get("pitch_error_cents")

        if time_error is None:
            continue

        notes_hit += 1

        # ------------------------------------------------
        # 1. Pitch Scoring Curve (v1.2.0 Cents Upgrade)
        # ------------------------------------------------
        # Base Check: Did they even play the right nominal note letter?
        if note["performed_note"] == note["expected_note"]:
            if cents_error is not None:
                abs_cents = abs(cents_error)

                if abs_cents <= 10.0:
                    pitch_score += 1.0
                elif abs_cents >= 50.0:
                    pitch_score += 0.0
                else:
                    # Linear decay curve between 10 and 50 cents
                    # Formula tracks decay across a 40-cent window width
                    pitch_score += 1.0 - ((abs_cents - 10.0) / 40.0)

            else:
                pitch_score += 1.0

        # Timing
        abs_time_error = abs(time_error)

        timing_score += max(
            0.0,
            1.0 - (abs_time_error / 0.4),
        )

    pitch_accuracy = pitch_score / total_notes
    timing_accuracy = timing_score / total_notes

    total_score = (pitch_accuracy * 0.7 + timing_accuracy * 0.3) * 100

    return {
        "total_score": round(total_score, 1),
        "pitch_accuracy": round(pitch_accuracy * 100, 1),
        "timing_accuracy": round(timing_accuracy * 100, 1),
        "notes_hit": notes_hit,
        "notes_total": total_notes,
    }
