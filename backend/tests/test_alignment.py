from app.services.alignment import align_notes
from app.models.practice_target import ExpectedNote
from app.core.events import PerformedNoteEvent
from typing import List


def test_perfect_match():
    expected = [
        ExpectedNote("A4", 0.0),
        ExpectedNote("B4", 1.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 0.0,
        },
        {
            "note": "B4",
            "frequency": 494.0,
            "timestamp": 1.0,
        },
    ]

    result = align_notes(expected, performed)

    assert len(result) == 2

    assert result[0]["expected_note"] == "A4"
    assert result[0]["performed_note"] == "A4"

    assert result[1]["expected_note"] == "B4"
    assert result[1]["performed_note"] == "B4"


def test_note_with_timing_error():
    expected = [
        ExpectedNote("A4", 0.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 0.15,
        }
    ]

    result = align_notes(expected, performed)

    assert result[0]["performed_note"] == "A4"
    assert result[0]["time_error"] == 0.15


def test_missed_note():
    expected = [
        ExpectedNote("A4", 0.0),
    ]

    performed = []

    result = align_notes(expected, performed)

    assert result[0]["performed_note"] is None
    assert result[0]["performed_time"] is None


def test_wrong_pitch():
    expected = [
        ExpectedNote("A4", 0.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "G4",
            "frequency": 392.0,
            "timestamp": 0.0,
        }
    ]

    result = align_notes(expected, performed)

    assert result[0]["performed_note"] == "G4"


def test_closest_note_selected():
    expected = [
        ExpectedNote("A4", 1.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 0.8,
        },
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 1.05,
        },
    ]

    result = align_notes(expected, performed)

    assert result[0]["performed_time"] == 1.05


def test_note_cannot_be_reused():
    expected = [
        ExpectedNote("A4", 0.0),
        ExpectedNote("A4", 1.0),
    ]

    performed: List[PerformedNoteEvent] = [
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 0.1,
        }
    ]

    result = align_notes(expected, performed)

    assert result[0]["performed_note"] == "A4"
    assert result[1]["performed_note"] is None


# TODO
# Future alignment tests:
#
# - Extra performed notes
# - Tempo drift
# - Shifted sequence
# - Dynamic-programming alignment
# - Repeated notes
# - Grace notes
