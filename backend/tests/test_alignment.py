from typing import List
import pytest

from app.models.events import SessionStoredNote
from app.pipeline.practice_target import ExpectedNote
from app.pipeline.alignment import align_notes


def test_align_notes_perfect_match():
    """Verifies that a session note matching an expected note aligns perfectly and preserves pitch error."""
    expected = [ExpectedNote(note="A4", time=1.0, duration=0.5)]

    # 🌟 Explicitly typed to SessionStoredNote
    performed: List[SessionStoredNote] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 1.0,  # Exactly 1.0s into the session
            "end_time": 1.5,
            "duration": 0.5,
            "avg_pitch_error_cents": -4.5,
        }
    ]

    result = align_notes(expected, performed, time_tolerance=0.4)

    assert len(result) == 1
    assert result[0]["expected_note"] == "A4"
    assert result[0]["performed_note"] == "A4"
    assert result[0]["pitch_error_cents"] == -4.5
    assert result[0]["time_error"] == 0.0
    assert result[0]["match_quality"] == 1.0


def test_align_notes_selects_closest_chronological_match():
    """Verifies that the alignment greedily locks onto the closest note in the session timeline."""
    expected = [ExpectedNote(note="D4", time=1.0, duration=0.5)]
    performed: List[SessionStoredNote] = [
        {
            "note": "D4",
            "frequency": 293.66,
            "start_time": 0.7,  # 0.3s early
            "end_time": 1.1,
            "duration": 0.4,
            "avg_pitch_error_cents": 12.0,
        },
        {
            "note": "D4",
            "frequency": 293.66,
            "start_time": 1.05,  # 0.05s late (Closest match)
            "end_time": 1.45,
            "duration": 0.4,
            "avg_pitch_error_cents": -2.0,
        },
    ]

    result = align_notes(expected, performed, time_tolerance=0.4)

    assert len(result) == 1
    assert result[0]["performed_start_time"] == 1.05
    assert result[0]["pitch_error_cents"] == -2.0
    assert result[0]["time_error"] == pytest.approx(0.05)


def test_align_notes_prevents_double_matching():
    """Verifies that a stored session note cannot double-bind to multiple expected target slots."""
    expected = [
        ExpectedNote(note="A4", time=1.0, duration=0.2),
        ExpectedNote(note="A4", time=1.2, duration=0.2),
    ]
    performed: List[SessionStoredNote] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 1.05,
            "end_time": 1.4,
            "duration": 0.35,
            "avg_pitch_error_cents": 0.0,
        }
    ]

    result = align_notes(expected, performed, time_tolerance=0.4)

    assert len(result) == 2
    assert result[0]["performed_note"] == "A4"
    assert result[1]["performed_note"] is None
    assert result[1]["match_quality"] == 0.0
