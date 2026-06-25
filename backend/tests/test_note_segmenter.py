from typing import List
import pytest

from app.core.events import PitchObservationEvent
from app.services.note_segmenter import NoteSegmenter


def test_single_sustained_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.05, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.20, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    # No note change or flush -> no emission yet
    assert len(output) == 0


def test_note_change_emits_previous_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.0, "pitch_cents_error": 0.00},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10, "pitch_cents_error": 0.0},
        {
            "note": "B4",
            "frequency": 494.0,
            "timestamp": 0.25,
            "pitch_cents_error": 0.0,
        },  # Candidate B4 starts at 0.25
        {
            "note": "B4",
            "frequency": 494.0,
            "timestamp": 0.36,
            "pitch_cents_error": 0.0,
        },  # Stable at 0.36 (dt = 0.11) -> Emits A4
    ]

    for e in events:
        segmenter.process(e)

    # Should emit A4 exactly when B4 crosses the stability threshold
    assert len(output) == 1

    a4_note = output[0]
    assert a4_note["note"] == "A4"
    assert a4_note["frequency"] == 440.0
    assert a4_note["start_time"] == 0.00
    assert a4_note["end_time"] == 0.36
    assert a4_note["duration"] == pytest.approx(0.36)


def test_jitter_is_ignored():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {
            "note": "A#4",
            "frequency": 466.0,
            "timestamp": 0.05,
            "pitch_cents_error": 0.0,
        },  # Transient jitter
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 0.08,
            "pitch_cents_error": 0.0,
        },  # Reverts back, clears candidate
        {"note": "A4", "frequency": 440.0, "timestamp": 0.20, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_stability_threshold_boundary():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {
            "note": "B4",
            "frequency": 494.0,
            "timestamp": 0.09,
            "pitch_cents_error": 0.0,
        },  # Candidate B4 starts
        {
            "note": "B4",
            "frequency": 494.0,
            "timestamp": 0.18,
            "pitch_cents_error": 0.0,
        },  # dt = 0.09 (Just below 0.10)
    ]

    for e in events:
        segmenter.process(e)

    # Should NOT emit A4 yet because B4 has only been candidate for 0.09s
    assert len(output) == 0


def test_first_note_is_not_emitted_immediately():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    segmenter.process(
        {"note": "A4", "frequency": 440.0, "timestamp": 0.0, "pitch_cents_error": 0.0}
    )

    assert len(output) == 0


def test_vibrato_does_not_prematurely_trigger_emission():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    # Pitch rapidly cycles every 0.04 seconds (under the 0.1 threshold)
    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {
            "note": "A#4",
            "frequency": 466.0,
            "timestamp": 0.04,
            "pitch_cents_error": 0.0,
        },
        {"note": "A4", "frequency": 440.0, "timestamp": 0.08, "pitch_cents_error": 0.0},
        {
            "note": "A#4",
            "frequency": 466.0,
            "timestamp": 0.12,
            "pitch_cents_error": 0.0,
        },
        {"note": "A4", "frequency": 440.0, "timestamp": 0.16, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    # Because no single candidate held stable for >= 0.1s, it stays clamped
    assert len(output) == 0


def test_candidate_overwritten_by_different_candidate():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    # Update payloads with the new key contract requirement
    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.08, "pitch_cents_error": 0.0},
        {"note": "C5", "frequency": 523.2, "timestamp": 0.12, "pitch_cents_error": 0.0},
        {"note": "C5", "frequency": 523.2, "timestamp": 0.23, "pitch_cents_error": 0.0},
        {"note": "D5", "frequency": 587.3, "timestamp": 0.40, "pitch_cents_error": 0.0},
        {"note": "D5", "frequency": 587.3, "timestamp": 0.55, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 2
    assert output[0]["note"] == "A4"
    assert output[0]["end_time"] == 0.23
    assert output[1]["note"] == "C5"
    assert output[1]["end_time"] == 0.55  # Our fixed boundary assertion from earlier!


def test_silence_finalizes_previous_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10, "pitch_cents_error": 0.0},
        {
            "note": "REST",
            "frequency": 0.0,
            "timestamp": 0.20,
            "pitch_cents_error": 0.0,
        },  # Scrapes/Silence registers as REST
        {
            "note": "REST",
            "frequency": 0.0,
            "timestamp": 0.31,
            "pitch_cents_error": 0.0,
        },  # REST confirms stability
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 1
    assert output[0]["note"] == "A4"
    assert output[0]["end_time"] == 0.31


def test_identical_timestamps_do_not_cause_accidental_stability():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.05, "pitch_cents_error": 0.0},
        {
            "note": "B4",
            "frequency": 494.0,
            "timestamp": 0.05,
            "pitch_cents_error": 0.0,
        },  # Malformed frame event delta = 0.0s
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_final_note_is_flushed_on_end():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.30, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    # Force a manual flush on end of execution stream
    segmenter.flush(timestamp=0.35)

    assert len(output) == 1

    flushed_note = output[0]
    assert flushed_note["note"] == "A4"
    assert flushed_note["start_time"] == 0.00
    assert flushed_note["end_time"] == 0.35
    assert flushed_note["duration"] == pytest.approx(0.35)


def test_segmenter_calculates_pure_mathematical_average():
    """Verifies that multiple frames of the same note average their cents errors correctly."""
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 5.0},
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 0.05,
            "pitch_cents_error": 15.0,
        },
        {
            "note": "A4",
            "frequency": 440.0,
            "timestamp": 0.09,
            "pitch_cents_error": 10.0,
        },
        # Transitioning to B4 to force the pipeline to commit and emit the A4 note window
        {"note": "B4", "frequency": 494.0, "timestamp": 0.20, "pitch_cents_error": 0.0},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.31, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 1
    # Mean average calculation check: (5.0 + 15.0 + 10.0) / 3 = 10.0 cents
    assert output[0]["avg_pitch_error_cents"] == 10.0


def test_segmenter_handles_none_cents_errors_safely():
    """Ensures that RESTs or missing frames do not crash the engine or warp mathematical averages."""
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        # Gated ambient noise frame or clear REST element setup
        {
            "note": "REST",
            "frequency": 0.0,
            "timestamp": 0.00,
            "pitch_cents_error": None,
        },
        {
            "note": "REST",
            "frequency": 0.0,
            "timestamp": 0.05,
            "pitch_cents_error": None,
        },
        # Transitioning to a clean note to force a flush/commit event trigger
        {"note": "E4", "frequency": 329.6, "timestamp": 0.16, "pitch_cents_error": 4.0},
        {"note": "E4", "frequency": 329.6, "timestamp": 0.27, "pitch_cents_error": 4.0},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 1
    # The first note emitted was the REST segment, which should cleanly contain None
    assert output[0]["note"] == "REST"
    assert output[0]["avg_pitch_error_cents"] is None
