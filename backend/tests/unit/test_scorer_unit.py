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
            "pitch_error_cents": 5.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)
    assert result["total_score"] == 100.0
    assert result["pitch_accuracy"] == 100.0
    assert result["timing_accuracy"] == 100.0


def test_missed_note_scores_zero():
    """Verifies that an unperformed note returns a zero score and does not increment notes hit."""
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


def test_timing_linear_decay_score():
    """Verifies that rhythmic offset decays the timing score while pitch remains perfect."""
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.15,  # Late entry
            "performed_end_time": 0.55,
            "pitch_error_cents": 0.0,  # Perfect pitch (100.0%)
            "time_error": 0.15,  # Assuming 0.15s drops timing to 50%
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 100.0
    assert result["timing_accuracy"] == 62.5

    # Blend: (1.0 * 0.7) + (0.625 * 0.3) = 0.70 + 0.1875 = 88.8% (to 1 d.p)
    assert result["total_score"] == 88.8


def test_aggregate_score_for_multiple_notes():
    """Verifies that total scores represent a clean average across an entire phrase array."""
    aligned: List[AlignedNote] = [
        # Note 1: Perfect (100 points)
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 0.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        },
        # Note 2: Completely Missed (0 points)
        {
            "expected_note": "E5",
            "performed_note": None,
            "expected_time": 0.5,
            "performed_start_time": None,
            "performed_end_time": None,
            "pitch_error_cents": None,
            "time_error": None,
            "match_quality": 0.0,
        },
    ]

    result = score_alignment(aligned)

    # Combined average of Note 1 (100) and Note 2 (0) should be exactly 50%
    assert result["total_score"] == 50.0
    assert result["notes_hit"] == 1


def test_empty_alignment_returns_zero_gracefully():
    """Guards against ZeroDivisionError when processing empty phrase streams."""
    aligned: List[AlignedNote] = []

    result = score_alignment(aligned)

    assert result["total_score"] == 0.0
    assert result["pitch_accuracy"] == 0.0
    assert result["timing_accuracy"] == 0.0


def test_pitch_at_perfect_boundary_scores_full():
    """Exactly 10 cents error should still receive full pitch credit."""

    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 10.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 100.0
    assert result["total_score"] == 100.0


def test_pitch_at_zero_boundary_scores_zero():
    """Exactly 50 cents error should receive zero pitch credit."""

    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 50.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 0.0
    assert result["total_score"] == 30.0


def test_negative_pitch_error_scores_same_as_positive():
    """Pitch scoring should use absolute cents error."""

    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": -30.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 50.0
    assert result["total_score"] == 65.0


def test_early_timing_error_scores_same_as_late():
    """Timing scoring should use absolute timing error."""

    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 1.0,
            "performed_start_time": 0.85,
            "performed_end_time": 1.25,
            "pitch_error_cents": 0.0,
            "time_error": -0.15,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 100.0
    assert result["timing_accuracy"] == 62.5
    assert result["total_score"] == 88.8


def test_pitch_and_timing_accuracy_are_averaged_independently():
    """Pitch accuracy, timing accuracy and total score should all average correctly."""

    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 0.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        },
        {
            "expected_note": "B4",
            "performed_note": "B4",
            "expected_time": 1.0,
            "performed_start_time": 1.15,
            "performed_end_time": 1.55,
            "pitch_error_cents": 30.0,
            "time_error": 0.15,
            "match_quality": 1.0,
        },
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 75.0
    assert result["timing_accuracy"] == 81.2
    assert result["total_score"] == 76.9


def test_notes_hit_counts_only_successful_matches():
    """Only aligned notes should contribute to notes_hit."""

    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": 0.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        },
        {
            "expected_note": "B4",
            "performed_note": None,
            "expected_time": 1.0,
            "performed_start_time": None,
            "performed_end_time": None,
            "pitch_error_cents": None,
            "time_error": None,
            "match_quality": 0.0,
        },
        {
            "expected_note": "C5",
            "performed_note": "C5",
            "expected_time": 2.0,
            "performed_start_time": 2.0,
            "performed_end_time": 2.4,
            "pitch_error_cents": 0.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        },
        {
            "expected_note": "D5",
            "performed_note": None,
            "expected_time": 3.0,
            "performed_start_time": None,
            "performed_end_time": None,
            "pitch_error_cents": None,
            "time_error": None,
            "match_quality": 0.0,
        },
        {
            "expected_note": "E5",
            "performed_note": "E5",
            "expected_time": 4.0,
            "performed_start_time": 4.0,
            "performed_end_time": 4.4,
            "pitch_error_cents": 0.0,
            "time_error": 0.0,
            "match_quality": 1.0,
        },
    ]

    result = score_alignment(aligned)

    assert result["notes_hit"] == 3


def test_wrong_note_letter_scores_zero_for_pitch():
    """Verifies that playing the wrong pitch letter gives 0.0 pitch accuracy, even if timing is perfect."""
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "B4",  # Wrong note letter!
            "expected_time": 1.0,
            "performed_start_time": 1.0,
            "performed_end_time": 1.4,
            "pitch_error_cents": 0.0,
            "time_error": 0.0,  # Perfect timing (100.0%)
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    # Note letter mismatch means pitch accuracy drops to 0.0%
    assert result["pitch_accuracy"] == 0.0
    assert result["timing_accuracy"] == 100.0
    # Blend: (0.0 * 0.7) + (1.0 * 0.3) = 30.0%
    assert result["total_score"] == 30.0


def test_matching_note_with_missing_cents_error_defaults_to_perfect():
    """Executes the fallback branch where pitch error is missing but the note names match perfectly."""
    aligned: List[AlignedNote] = [
        {
            "expected_note": "A4",
            "performed_note": "A4",
            "expected_time": 0.0,
            "performed_start_time": 0.0,
            "performed_end_time": 0.4,
            "pitch_error_cents": None,
            "time_error": 0.0,
            "match_quality": 1.0,
        }
    ]

    result = score_alignment(aligned)

    assert result["pitch_accuracy"] == 100.0
    assert result["total_score"] == 100.0
