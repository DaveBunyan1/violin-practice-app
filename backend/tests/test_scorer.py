from typing import List

from app.core.events import AlignedNote
from app.scoring.scorer import score_alignment


def test_perfect_score():
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_time": 0.0,
            "pitch_error_cents": None,
            "time_error": 0.0,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["total_score"] == 100.0


def test_missed_note_scores_zero():
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": None,
            "expected_time": 0.0,
            "performed_time": None,
            "pitch_error_cents": None,
            "time_error": None,
            "match_quality": 0.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["total_score"] == 0.0
