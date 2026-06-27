from typing import List

from app.models.events import AlignedNote
from app.scoring.scorer import score_alignment


def test_perfect_score():
    """A note with perfect timing and <= 10 cents pitch error must yield 100%."""
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 5.0,  # v1.2.0: Inside the <= 10.0 cents perfect threshold window
            "time_error": 0.0,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)
    assert result["total_score"] == 100.0
    assert result["pitch_accuracy"] == 100.0
    assert result["timing_accuracy"] == 100.0


def test_missed_note_scores_zero():
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": None,
            "expected_time": 0.0,
            "performed_start_time": None,
            "performed_end_time": None,
            "pitch_error_cents": None,
            "time_error": None,
            "match_quality": 0.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["total_score"] == 0.0
    assert result["notes_hit"] == 0


# -----------------------------------------------------------------
# New v1.2.0 Specific Curve Tests
# -----------------------------------------------------------------


def test_pitch_linear_decay_score():
    """A note with 30 cents error sits exactly halfway between 10 and 50 cents, receiving a 0.5 pitch multiplier."""
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 30.0,  # 30 cents out of tune
            "time_error": 0.0,  # Perfect timing (1.0 points)
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    # Pitch score should be 0.5 (50.0%)
    assert result["pitch_accuracy"] == 50.0
    assert result["timing_accuracy"] == 100.0

    # Combined weighted blend: (0.5 * 0.7 + 1.0 * 0.3) * 100 = (0.35 + 0.30) * 100 = 65.0
    assert result["total_score"] == 65.0


def test_pitch_beyond_tolerance_scores_zero():
    """A note played more than 50 cents sharp/flat receives 0 points for pitch."""
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 55.0,  # Completely out of tune (> 50 cents)
            "time_error": 0.0,  # Perfect timing
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 0.0
    assert result["timing_accuracy"] == 100.0
    # Combined weighted blend: (0.0 * 0.7 + 1.0 * 0.3) * 100 = 30.0
    assert result["total_score"] == 30.0
