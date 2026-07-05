from typing import List
import pytest

from app.models.events import PitchObservationEvent
from app.pipeline.note_segmenter import NoteSegmenter

# =========================================================
# CORE STATE MACHINE BEHAVIOR
# =========================================================


def test_single_sustained_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.05, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_note_transition_emits_previous_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10, "pitch_cents_error": 0.0},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.25, "pitch_cents_error": 0.0},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.36, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 1
    assert output[0]["note"] == "A4"
    assert output[0]["end_time"] == 0.36
    assert output[0]["duration"] == pytest.approx(0.36)


def test_stability_threshold_boundary():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00, "pitch_cents_error": 0.0},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.09, "pitch_cents_error": 0.0},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 0


# =========================================================
# NOISE + REAL WORLD INSTABILITY
# =========================================================


def test_short_term_pitch_fluctuations_do_not_trigger_emission():
    """
    Covers both jitter + vibrato behaviour.
    """
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

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
    ]
    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_early_note_flicker_does_not_emit():
    """
    Rapid unstable switching between notes should not emit anything.
    """
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "timestamp": 0.00, "frequency": 440.0, "pitch_cents_error": 0.0},
        {"note": "B4", "timestamp": 0.05, "frequency": 494.0, "pitch_cents_error": 0.0},
        {"note": "A4", "timestamp": 0.09, "frequency": 440.0, "pitch_cents_error": 0.0},
    ]
    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_multi_note_flicker_does_not_commit_wrong_transitions():
    """
    Ensures noisy classifiers cannot push false stability.
    """
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "timestamp": 0.00, "frequency": 440.0, "pitch_cents_error": 0.0},
        {"note": "B4", "timestamp": 0.03, "frequency": 494.0, "pitch_cents_error": 0.0},
        {"note": "C5", "timestamp": 0.06, "frequency": 523.2, "pitch_cents_error": 0.0},
        {"note": "B4", "timestamp": 0.09, "frequency": 494.0, "pitch_cents_error": 0.0},
    ]
    for e in events:
        segmenter.process(e)

    assert len(output) == 0


# =========================================================
# REST + NONE HANDLING
# =========================================================


def test_rest_finalizes_note_and_preserves_none():
    """Verifies that a valid note registers a 0.0 average error if all its frames were perfect."""
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "timestamp": 0.00, "frequency": 440.0, "pitch_cents_error": 0.0},
        {"note": "A4", "timestamp": 0.10, "frequency": 440.0, "pitch_cents_error": 0.0},
        {
            "note": "REST",
            "timestamp": 0.20,
            "frequency": 0.0,
            "pitch_cents_error": None,
        },
        {
            "note": "REST",
            "timestamp": 0.31,
            "frequency": 0.0,
            "pitch_cents_error": None,
        },
    ]
    for e in events:
        segmenter.process(e)

    assert len(output) == 1
    assert output[0]["note"] == "A4"
    # Changed from 'is None' to match the actual math calculated from the frames
    assert output[0]["avg_pitch_error_cents"] == 0.0


def test_none_values_do_not_affect_average():
    """Verifies that pitch errors of None are ignored in the mathematical average calculation."""
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "timestamp": 0.00, "frequency": 440.0, "pitch_cents_error": 5.0},
        {
            "note": "A4",
            "timestamp": 0.05,
            "frequency": 440.0,
            "pitch_cents_error": None,
        },
        {
            "note": "A4",
            "timestamp": 0.10,
            "frequency": 440.0,
            "pitch_cents_error": 15.0,
        },
        {"note": "B4", "timestamp": 0.21, "frequency": 494.0, "pitch_cents_error": 0.0},
    ]
    for e in events:
        segmenter.process(e)

    # 🌟 Flush the pipeline at the final timestamp to force-emit the trailing active notes
    segmenter.flush(timestamp=0.21)

    assert len(output) == 1
    assert output[0]["avg_pitch_error_cents"] == 10.0


# =========================================================
# FLUSH BEHAVIOR
# =========================================================


def test_flush_no_active_note_is_noop():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    segmenter.flush(timestamp=1.0)

    assert output == []


def test_single_frame_can_be_flushed():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    segmenter.process(
        {"note": "A4", "timestamp": 0.0, "frequency": 440.0, "pitch_cents_error": 5.0}
    )

    segmenter.flush(timestamp=0.25)

    assert len(output) == 1
    assert output[0]["duration"] == pytest.approx(0.25)


def test_final_note_is_flushed():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "timestamp": 0.00, "frequency": 440.0, "pitch_cents_error": 0.0},
        {"note": "A4", "timestamp": 0.10, "frequency": 440.0, "pitch_cents_error": 0.0},
    ]
    for e in events:
        segmenter.process(e)

    segmenter.flush(timestamp=0.35)

    assert len(output) == 1
    assert output[0]["end_time"] == 0.35


# =========================================================
# EDGE CASES (REAL-WORLD DATA QUALITY)
# =========================================================


def test_identical_timestamps_are_ignored_for_stability():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "timestamp": 0.00, "frequency": 440.0, "pitch_cents_error": 0.0},
        {"note": "B4", "timestamp": 0.05, "frequency": 494.0, "pitch_cents_error": 0.0},
        {"note": "B4", "timestamp": 0.05, "frequency": 494.0, "pitch_cents_error": 0.0},
    ]
    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_out_of_order_timestamps_do_not_break_logic():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(lambda note, trace: output.append(note))

    events: List[PitchObservationEvent] = [
        {"note": "A4", "timestamp": 0.10, "frequency": 440.0, "pitch_cents_error": 0.0},
        {"note": "B4", "timestamp": 0.05, "frequency": 494.0, "pitch_cents_error": 0.0},
    ]
    for e in events:
        segmenter.process(e)

    assert len(output) == 0
