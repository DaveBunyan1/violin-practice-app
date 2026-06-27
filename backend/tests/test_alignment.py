from typing import List
import pytest

from app.pipeline.alignment import align_notes
from app.pipeline.practice_target import ExpectedNote
from app.models.events import PerformedNoteEvent


def test_perfect_match():
    expected = [
        ExpectedNote("A4", 0.0),
        ExpectedNote("B4", 1.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 0.0,
            "end_time": 0.5,
            "duration": 0.5,
        },
        {
            "note": "B4",
            "frequency": 494.0,
            "start_time": 1.0,
            "end_time": 1.5,
            "duration": 0.5,
        },
    ]

    result = align_notes(expected, performed)

    assert len(result) == 2

    assert result[0]["expected_note"] == "A4"
    assert result[0]["performed_note"] == "A4"
    assert result[0]["performed_start_time"] == 0.0
    assert result[0]["match_quality"] == 1.0

    assert result[1]["expected_note"] == "B4"
    assert result[1]["performed_note"] == "B4"
    assert result[1]["performed_start_time"] == 1.0
    assert result[1]["match_quality"] == 1.0


def test_note_with_timing_error():
    expected = [
        ExpectedNote("A4", 0.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 0.15,
            "end_time": 0.65,
            "duration": 0.5,
        }
    ]

    result = align_notes(expected, performed)

    assert result[0]["performed_note"] == "A4"
    # pytest.approx handles floating point precision issues in math operations
    assert result[0]["time_error"] == pytest.approx(0.15)


def test_missed_note():
    expected = [
        ExpectedNote("A4", 0.0),
    ]

    performed = []

    result = align_notes(expected, performed)

    assert result[0]["performed_note"] is None
    assert result[0]["performed_start_time"] is None
    assert result[0]["performed_end_time"] is None
    assert result[0]["time_error"] is None
    assert result[0]["match_quality"] == 0.0


def test_wrong_pitch_greedy_match():
    """
    Verifies that the greedy time matcher still pairs notes based purely on
    temporal proximity, even if the pitch is incorrect.
    """
    expected = [
        ExpectedNote("A4", 0.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "G4",
            "frequency": 392.0,
            "start_time": 0.0,
            "end_time": 0.5,
            "duration": 0.5,
        }
    ]

    result = align_notes(expected, performed)

    assert result[0]["expected_note"] == "A4"
    assert result[0]["performed_note"] == "G4"
    assert result[0]["match_quality"] == 1.0


def test_closest_note_selected():
    expected = [
        ExpectedNote("A4", 1.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 0.8,
            "end_time": 1.2,
            "duration": 0.4,
        },
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 1.05,
            "end_time": 1.45,
            "duration": 0.4,
        },
    ]

    result = align_notes(expected, performed)

    assert result[0]["performed_start_time"] == 1.05


def test_note_cannot_be_reused():
    expected = [
        ExpectedNote("A4", 0.0),
        ExpectedNote("A4", 1.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 0.1,
            "end_time": 0.5,
            "duration": 0.4,
        }
    ]

    result = align_notes(expected, performed)

    assert result[0]["performed_note"] == "A4"
    assert result[1]["performed_note"] is None


def test_time_tolerance_boundary():
    """
    Ensures notes outside the explicit time tolerance window are rejected
    and counted as missed notes.
    """
    expected = [
        ExpectedNote("A4", 1.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "start_time": 1.41,  # dt = 0.41, higher than default 0.4 tolerance
            "end_time": 1.91,
            "duration": 0.5,
        }
    ]

    result = align_notes(expected, performed, time_tolerance=0.4)

    assert result[0]["performed_note"] is None
    assert result[0]["match_quality"] == 0.0
